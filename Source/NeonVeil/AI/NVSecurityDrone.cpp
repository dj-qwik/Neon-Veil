#include "AI/NVSecurityDrone.h"
#include "AI/NVHostileFire.h"
#include "Combat/NVHealthComponent.h"
#include "Core/NVGameplayTags.h"
#include "Objectives/NVObjectiveSubsystem.h"
#include "NeonVeil.h"

#include "Components/AudioComponent.h"
#include "Components/PointLightComponent.h"
#include "Components/SphereComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "GameFramework/Pawn.h"
#include "Kismet/GameplayStatics.h"
#include "NiagaraFunctionLibrary.h"
#include "TimerManager.h"
#include "UObject/ConstructorHelpers.h"

ANVSecurityDrone::ANVSecurityDrone()
{
	PrimaryActorTick.bCanEverTick = true;
	PrimaryActorTick.bStartWithTickEnabled = false;

	Collision = CreateDefaultSubobject<USphereComponent>(TEXT("Collision"));
	Collision->InitSphereRadius(48.f);
	Collision->SetCollisionProfileName(TEXT("BlockAllDynamic"));
	SetRootComponent(Collision);

	static ConstructorHelpers::FObjectFinder<UStaticMesh> Sphere(TEXT("/Engine/BasicShapes/Sphere.Sphere"));
	static ConstructorHelpers::FObjectFinder<UStaticMesh> Cyl(TEXT("/Engine/BasicShapes/Cylinder.Cylinder"));
	Body = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Body"));
	Body->SetupAttachment(Collision);
	Body->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	Body->SetRelativeScale3D(FVector(0.85f, 0.85f, 0.55f));
	Ring = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Ring"));
	Ring->SetupAttachment(Collision);
	Ring->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	Ring->SetRelativeScale3D(FVector(1.35f, 1.35f, 0.06f));
	Eye = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Eye"));
	Eye->SetupAttachment(Collision);
	Eye->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	Eye->SetRelativeLocation(FVector(38.f, 0.f, 0.f));
	Eye->SetRelativeScale3D(FVector(0.22f));
	if (Sphere.Succeeded())
	{
		Body->SetStaticMesh(Sphere.Object);
		Eye->SetStaticMesh(Sphere.Object);
	}
	if (Cyl.Succeeded())
	{
		Ring->SetStaticMesh(Cyl.Object);
	}
	EyeLight = CreateDefaultSubobject<UPointLightComponent>(TEXT("EyeLight"));
	EyeLight->SetupAttachment(Eye);
	EyeLight->SetIntensity(0.f);
	EyeLight->SetAttenuationRadius(700.f);
	EyeLight->SetLightColor(FLinearColor(1.f, 0.12f, 0.08f));
	EyeLight->SetCastShadows(false);

	Gun = CreateDefaultSubobject<UNVHostileFire>(TEXT("Gun"));
	Gun->SetupAttachment(Collision);
	Gun->SetRelativeLocation(FVector(55.f, 0.f, -18.f));
	Gun->Damage = 4.f;
	Gun->SpreadDeg = 2.2f;

	Health = CreateDefaultSubobject<UNVHealthComponent>(TEXT("Health"));
	Health->MaxHealth = 70.f;
}

void ANVSecurityDrone::BeginPlay()
{
	Super::BeginPlay();
	DockLocation = GetActorLocation();
	Health->OnDeath.AddDynamic(this, &ANVSecurityDrone::HandleDeath);
	if (!DestroyedEventTag.IsValid())
	{
		DestroyedEventTag = NVTags::Event_M01_DroneDown;
	}
	OrbitAngle = FMath::FRandRange(0.f, 360.f);
	// docked: dark, not shootable until deployed (it is up in its ceiling dock)
	Collision->SetCollisionEnabled(ECollisionEnabled::NoCollision);
}

void ANVSecurityDrone::Activate(float Delay)
{
	if (State != EState::Docked)
	{
		return;
	}
	if (Delay > 0.f)
	{
		GetWorldTimerManager().SetTimer(ActivateTimer, this, &ANVSecurityDrone::BeginActive, Delay, false);
	}
	else
	{
		BeginActive();
	}
}

void ANVSecurityDrone::BeginActive()
{
	if (State != EState::Docked)
	{
		return;
	}
	State = EState::Deploying;
	StateTime = 0.f;
	Collision->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
	EyeLight->SetIntensity(3000.f);
	if (HumSound)
	{
		Hum = UGameplayStatics::SpawnSoundAttached(HumSound, Collision, NAME_None, FVector::ZeroVector, EAttachLocation::KeepRelativeOffset, true, 0.5f);
	}
	SetActorTickEnabled(true);
	UE_LOG(LogNeonVeil, Log, TEXT("%s deployed"), *GetName());
}

void ANVSecurityDrone::SetWrecked()
{
	bDestroyed = true;
	State = EState::Gone;
	SetActorTickEnabled(false);
	SetActorHiddenInGame(true);
	SetActorEnableCollision(false);
}

FVector ANVSecurityDrone::ClampToBounds(const FVector& P) const
{
	if ((BoundsMax - BoundsMin).IsNearlyZero())
	{
		return P;
	}
	return FVector(FMath::Clamp(P.X, FMath::Min(BoundsMin.X, BoundsMax.X), FMath::Max(BoundsMin.X, BoundsMax.X)),
		FMath::Clamp(P.Y, FMath::Min(BoundsMin.Y, BoundsMax.Y), FMath::Max(BoundsMin.Y, BoundsMax.Y)),
		FMath::Clamp(P.Z, FMath::Min(BoundsMin.Z, BoundsMax.Z), FMath::Max(BoundsMin.Z, BoundsMax.Z)));
}

void ANVSecurityDrone::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	StateTime += DeltaSeconds;
	const float Now = GetWorld()->GetTimeSeconds();
	if (State == EState::Deploying)
	{
		const float A = FMath::Clamp(StateTime / 1.1f, 0.f, 1.f);
		SetActorLocation(DockLocation - FVector(0.f, 0.f, DeployDrop * FMath::InterpEaseOut(0.f, 1.f, A, 2.f)));
		Ring->AddLocalRotation(FRotator(0.f, 720.f * DeltaSeconds, 0.f));
		if (A >= 1.f)
		{
			State = EState::Active;
			FireTimer = FMath::FRandRange(0.8f, 1.6f);
		}
		return;
	}
	if (State == EState::Falling)
	{
		if (StateTime > 6.f)
		{
			State = EState::Gone;
			SetActorTickEnabled(false);
			SetActorHiddenInGame(true);
		}
		return;
	}
	if (State != EState::Active)
	{
		return;
	}
	if (!Target.IsValid())
	{
		Target = UGameplayStatics::GetPlayerPawn(this, 0);
	}
	AActor* T = Target.Get();
	if (!T)
	{
		return;
	}
	Ring->AddLocalRotation(FRotator(0.f, 540.f * DeltaSeconds, 0.f));

	// movement: orbit the player at range, bob a little, stay in the flight box
	if (Now > NextDirFlip)
	{
		OrbitDir = FMath::RandBool() ? 1.f : -1.f;
		NextDirFlip = Now + FMath::FRandRange(2.5f, 5.f);
	}
	OrbitAngle += OrbitDir * OrbitSpeed * DeltaSeconds;
	const FVector Feet = T->GetActorLocation() - FVector(0.f, 0.f, 90.f);
	const FVector Want = ClampToBounds(Feet + FRotator(0.f, OrbitAngle, 0.f).Vector() * OrbitRadius
		+ FVector(0.f, 0.f, HoverHeight + 35.f * FMath::Sin(Now * 1.7f)));
	const FVector Cur = GetActorLocation();
	const FVector Step = (Want - Cur).GetClampedToMaxSize(MoveSpeed * DeltaSeconds);
	SetActorLocation(Cur + Step, true);
	const FRotator Face = (T->GetActorLocation() - GetActorLocation()).Rotation();
	SetActorRotation(FMath::RInterpTo(GetActorRotation(), FRotator(0.f, Face.Yaw, 0.f), DeltaSeconds, 6.f));
	Eye->SetRelativeRotation(FRotator(Face.Pitch, 0.f, 0.f));

	// firing: idle -> telegraph (eye pulses) -> burst, only with line of sight in range
	const bool bSees = FVector::Dist(GetActorLocation(), T->GetActorLocation()) < EngageRange
		&& UNVHostileFire::CanSee(GetWorld(), this, Gun->GetComponentLocation(), T);
	FireTimer -= DeltaSeconds;
	if (FirePhase == 0)
	{
		EyeLight->SetIntensity(3000.f);
		if (FireTimer <= 0.f && bSees)
		{
			FirePhase = 1;
			FireTimer = TelegraphTime;
			if (TelegraphSound)
			{
				UGameplayStatics::PlaySoundAtLocation(this, TelegraphSound, GetActorLocation(), 0.8f);
			}
		}
	}
	else if (FirePhase == 1)
	{
		EyeLight->SetIntensity(FMath::Fmod(Now * 10.f, 1.f) < 0.5f ? 22000.f : 4000.f);
		if (FireTimer <= 0.f)
		{
			FirePhase = 2;
			ShotsLeft = BurstShots;
			FireTimer = 0.f;
		}
	}
	else
	{
		EyeLight->SetIntensity(16000.f);
		if (FireTimer <= 0.f)
		{
			if (ShotsLeft > 0 && bSees)
			{
				Gun->Fire(T, UNVHostileFire::AimPointOn(T));
				--ShotsLeft;
				FireTimer = ShotInterval;
			}
			else
			{
				FirePhase = 0;
				FireTimer = FMath::FRandRange(BurstPause.X, BurstPause.Y);
			}
		}
	}
}

void ANVSecurityDrone::HandleDeath(UNVHealthComponent* HealthComp, AActor* Killer)
{
	if (bDestroyed)
	{
		return;
	}
	bDestroyed = true;
	State = EState::Falling;
	StateTime = 0.f;
	EyeLight->SetIntensity(0.f);
	if (Hum)
	{
		Hum->FadeOut(0.3f, 0.f);
	}
	if (DestroyedFX)
	{
		UNiagaraFunctionLibrary::SpawnSystemAtLocation(this, DestroyedFX, GetActorLocation(), FRotator::ZeroRotator, FVector(0.8f));
	}
	if (SmokeFX)
	{
		UNiagaraFunctionLibrary::SpawnSystemAttached(SmokeFX, Collision, NAME_None, FVector::ZeroVector, FRotator::ZeroRotator, EAttachLocation::KeepRelativeOffset, true);
	}
	if (DestroyedSound)
	{
		UGameplayStatics::PlaySoundAtLocation(this, DestroyedSound, GetActorLocation());
	}
	// drop out of the air and tumble
	Collision->SetCollisionProfileName(TEXT("PhysicsActor"));
	Collision->SetSimulatePhysics(true);
	Collision->AddImpulse(FVector(FMath::FRandRange(-150.f, 150.f), FMath::FRandRange(-150.f, 150.f), 100.f), NAME_None, true);
	Collision->AddAngularImpulseInDegrees(FVector(FMath::FRandRange(-400.f, 400.f), FMath::FRandRange(-400.f, 400.f), 600.f), NAME_None, true);
	UE_LOG(LogNeonVeil, Log, TEXT("%s destroyed by %s"), *GetName(), *GetNameSafe(Killer));
	OnDestroyedDrone.Broadcast(this);
	if (UNVObjectiveSubsystem* Obj = UNVObjectiveSubsystem::Get(this))
	{
		Obj->SendEvent(DestroyedEventTag);
	}
}
