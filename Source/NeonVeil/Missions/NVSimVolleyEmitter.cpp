#include "Missions/NVSimVolleyEmitter.h"
#include "Combat/NVHealthComponent.h"
#include "Core/NVGameplayTags.h"
#include "NeonVeil.h"

#include "Components/CapsuleComponent.h"
#include "Components/PointLightComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "GameFramework/Character.h"
#include "Kismet/GameplayStatics.h"
#include "UObject/ConstructorHelpers.h"

static constexpr int32 NVTracerPoolSize = 6;

ANVSimVolleyEmitter::ANVSimVolleyEmitter()
{
	PrimaryActorTick.bCanEverTick = true;
	PrimaryActorTick.bStartWithTickEnabled = false;

	Body = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Body"));
	SetRootComponent(Body);
	Body->SetCollisionProfileName(TEXT("NoCollision"));
	Body->SetRelativeScale3D(FVector(0.5f));
	static ConstructorHelpers::FObjectFinder<UStaticMesh> Sphere(TEXT("/Engine/BasicShapes/Sphere.Sphere"));
	static ConstructorHelpers::FObjectFinder<UStaticMesh> Cyl(TEXT("/Engine/BasicShapes/Cylinder.Cylinder"));
	if (Sphere.Succeeded())
	{
		Body->SetStaticMesh(Sphere.Object);
	}

	Light = CreateDefaultSubobject<UPointLightComponent>(TEXT("Light"));
	Light->SetupAttachment(Body);
	Light->SetIntensity(0.f);
	Light->SetAttenuationRadius(600.f);
	Light->SetLightColor(FLinearColor(1.f, 0.25f, 0.15f));
	Light->SetCastShadows(false);

	for (int32 i = 0; i < NVTracerPoolSize; ++i)
	{
		UStaticMeshComponent* T = CreateDefaultSubobject<UStaticMeshComponent>(*FString::Printf(TEXT("Tracer%d"), i));
		T->SetupAttachment(Body);
		T->SetUsingAbsoluteLocation(true);
		T->SetUsingAbsoluteRotation(true);
		T->SetUsingAbsoluteScale(true);
		T->SetCollisionProfileName(TEXT("NoCollision"));
		T->CastShadow = false;
		T->SetHiddenInGame(true);
		if (Cyl.Succeeded())
		{
			T->SetStaticMesh(Cyl.Object);
		}
		Tracers.Add(T);
	}
}

void ANVSimVolleyEmitter::BeginPlay()
{
	Super::BeginPlay();
	TracerTimeLeft.Init(0.f, Tracers.Num());
	if (!DamageType.IsValid())
	{
		DamageType = NVTags::Damage_Training;
	}
}

void ANVSimVolleyEmitter::StartVolley(AActor* Target, float WarmupSeconds, float FireSeconds)
{
	VolleyTarget = Target;
	Phase = EPhase::Warmup;
	PhaseTimeLeft = WarmupSeconds;
	// Firing time is kept for when the warm-up ends.
	ShotTimer = -FireSeconds;
	ShotsFired = ShotsLanded = 0;
	SetActorTickEnabled(true);
	if (WarningSound)
	{
		UGameplayStatics::PlaySoundAtLocation(this, WarningSound, GetActorLocation());
	}
	UE_LOG(LogNeonVeil, Log, TEXT("%s volley: warm-up %.1f s, fire %.1f s"), *GetName(), WarmupSeconds, FireSeconds);
}

void ANVSimVolleyEmitter::StopVolley()
{
	Phase = EPhase::Idle;
	Light->SetIntensity(0.f);
	SetActorTickEnabled(false);
	for (int32 i = 0; i < Tracers.Num(); ++i)
	{
		Tracers[i]->SetHiddenInGame(true);
		TracerTimeLeft[i] = 0.f;
	}
}

void ANVSimVolleyEmitter::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	for (int32 i = 0; i < Tracers.Num(); ++i)
	{
		if (TracerTimeLeft[i] > 0.f)
		{
			TracerTimeLeft[i] -= DeltaSeconds;
			if (TracerTimeLeft[i] <= 0.f)
			{
				Tracers[i]->SetHiddenInGame(true);
			}
		}
	}
	const float Now = GetWorld()->GetTimeSeconds();
	if (Phase == EPhase::Warmup)
	{
		// Fast red pulse: readable telegraph for the incoming volley.
		Light->SetIntensity(FMath::Fmod(Now * 6.f, 1.f) < 0.5f ? 8000.f : 1500.f);
		PhaseTimeLeft -= DeltaSeconds;
		if (PhaseTimeLeft <= 0.f)
		{
			Phase = EPhase::Firing;
			PhaseTimeLeft = -ShotTimer; // stored fire duration
			ShotTimer = 0.f;
		}
		return;
	}
	if (Phase == EPhase::Firing)
	{
		Light->SetIntensity(5000.f);
		PhaseTimeLeft -= DeltaSeconds;
		ShotTimer -= DeltaSeconds;
		while (ShotTimer <= 0.f && PhaseTimeLeft > 0.f)
		{
			FireShot();
			ShotTimer += 1.f / FMath::Max(1.f, ShotsPerSecond);
		}
		if (PhaseTimeLeft <= 0.f)
		{
			UE_LOG(LogNeonVeil, Log, TEXT("%s volley finished: %d shots, %d reached the target"), *GetName(), ShotsFired, ShotsLanded);
			Phase = EPhase::Idle;
			Light->SetIntensity(0.f);
			OnVolleyFinished.Broadcast();
		}
		return;
	}
	// Idle: keep ticking only until tracers fade.
	bool bAnyTracer = false;
	for (float T : TracerTimeLeft)
	{
		bAnyTracer |= T > 0.f;
	}
	if (!bAnyTracer)
	{
		SetActorTickEnabled(false);
	}
}

void ANVSimVolleyEmitter::FireShot()
{
	AActor* Target = VolleyTarget.Get();
	if (!Target)
	{
		return;
	}
	++ShotsFired;
	// Aim at a random height on the target's capsule so partial cover matters.
	FVector AimPoint = Target->GetActorLocation();
	if (const ACharacter* C = Cast<ACharacter>(Target))
	{
		const float HalfH = C->GetCapsuleComponent()->GetScaledCapsuleHalfHeight();
		AimPoint.Z += FMath::FRandRange(-0.5f, 0.85f) * HalfH;
	}
	const FVector Start = GetActorLocation();
	const FVector Dir = FMath::VRandCone((AimPoint - Start).GetSafeNormal(), FMath::DegreesToRadians(SpreadDeg));
	const FVector End = Start + Dir * (FVector::Dist(Start, AimPoint) + 500.f);

	FCollisionQueryParams Params(SCENE_QUERY_STAT(NVVolleyTrace), false, this);
	FHitResult Hit;
	// Pawn channel: walls and cover block it, and so does the player's capsule.
	const bool bHit = GetWorld()->LineTraceSingleByChannel(Hit, Start, End, ECC_Pawn, Params);
	const FVector Impact = bHit ? Hit.ImpactPoint : End;
	if (bHit && Hit.GetActor() == Target)
	{
		if (UNVHealthComponent* H = Target->FindComponentByClass<UNVHealthComponent>())
		{
			H->ApplyDamage(DamagePerShot, this, DamageType, false);
			++ShotsLanded;
		}
	}
	if (ShotSound)
	{
		UGameplayStatics::PlaySoundAtLocation(this, ShotSound, Start, 0.6f);
	}
	// Tracer: stretched cylinder from muzzle to impact, visible for a few frames.
	if (Tracers.Num() > 0)
	{
		UStaticMeshComponent* T = Tracers[NextTracer];
		const float Len = FVector::Dist(Start, Impact);
		T->SetWorldLocation((Start + Impact) * 0.5f);
		T->SetWorldRotation(FRotationMatrix::MakeFromZ(Impact - Start).Rotator());
		T->SetWorldScale3D(FVector(0.02f, 0.02f, Len / 100.f));
		T->SetHiddenInGame(false);
		TracerTimeLeft[NextTracer] = 0.06f;
		NextTracer = (NextTracer + 1) % Tracers.Num();
	}
}
