#include "Abilities/NVReconDrone.h"
#include "Abilities/NVAbilityComponent.h"
#include "Combat/NVHealthComponent.h"
#include "NeonVeil.h"

#include "Components/PointLightComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "UObject/ConstructorHelpers.h"

ANVReconDrone::ANVReconDrone()
{
	PrimaryActorTick.bCanEverTick = true;

	Body = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Body"));
	SetRootComponent(Body);
	Body->SetCollisionProfileName(TEXT("NoCollision"));
	Body->SetRelativeScale3D(FVector(0.22f));
	Body->CastShadow = true;
	static ConstructorHelpers::FObjectFinder<UStaticMesh> Sphere(TEXT("/Engine/BasicShapes/Sphere.Sphere"));
	if (Sphere.Succeeded())
	{
		Body->SetStaticMesh(Sphere.Object);
	}

	Light = CreateDefaultSubobject<UPointLightComponent>(TEXT("Light"));
	Light->SetupAttachment(Body);
	Light->SetIntensity(1200.f);
	Light->SetAttenuationRadius(450.f);
	Light->SetLightColor(FLinearColor(0.35f, 0.9f, 1.f));
	Light->SetCastShadows(false);
}

void ANVReconDrone::Launch(UNVAbilityComponent* InOwner, const FVector& Direction, float Range, float InScanRadius, float InMarkDuration, float InLifetime)
{
	OwnerAbilities = InOwner;
	ScanRadius = InScanRadius;
	MarkDuration = InMarkDuration;

	// Fly along the aim until something is in the way, staying a little above head height.
	const FVector Start = GetActorLocation();
	const FVector End = Start + Direction.GetSafeNormal() * Range;
	// Fly against level geometry only; targets and characters don't stop the drone.
	FCollisionQueryParams Params(SCENE_QUERY_STAT(NVDroneLaunch), false, this);
	Params.AddIgnoredActor(GetOwner());
	const FCollisionObjectQueryParams Static(ECC_WorldStatic);
	FHitResult Hit;
	Target = GetWorld()->LineTraceSingleByObjectType(Hit, Start, End, Static, Params)
		? Hit.ImpactPoint - Direction.GetSafeNormal() * 120.f
		: End;
	// Climb above head height for a view over low walls, but stay under the ceiling.
	const float DesiredZ = FMath::Max(Target.Z, Start.Z + HoverHeight);
	FHitResult Ceil;
	const FVector Up(Target.X, Target.Y, DesiredZ + 60.f);
	Target.Z = GetWorld()->LineTraceSingleByObjectType(Ceil, FVector(Target.X, Target.Y, Target.Z), Up, Static, Params)
		? FMath::Max(Target.Z, Ceil.ImpactPoint.Z - 60.f)
		: DesiredZ;
	UE_LOG(LogNeonVeil, Log, TEXT("Recon drone launched toward %s"), *Target.ToCompactString());
	SetLifeSpan(InLifetime + 3.f); // safety net if Recall never arrives
}

void ANVReconDrone::Recall()
{
	bReturning = true;
}

void ANVReconDrone::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	Age += DeltaSeconds;

	if (bReturning)
	{
		const AActor* OwnerActor = GetOwner();
		const FVector Home = OwnerActor ? OwnerActor->GetActorLocation() + FVector(0.f, 0.f, 80.f) : GetActorLocation();
		const FVector NewLoc = FMath::VInterpConstantTo(GetActorLocation(), Home, DeltaSeconds, FlySpeed * 1.5f);
		SetActorLocation(NewLoc);
		if (FVector::DistSquared(NewLoc, Home) < FMath::Square(80.f))
		{
			Destroy();
		}
		return;
	}

	if (!bArrived)
	{
		const FVector NewLoc = FMath::VInterpConstantTo(GetActorLocation(), Target, DeltaSeconds, FlySpeed);
		SetActorLocation(NewLoc);
		if (FVector::DistSquared(NewLoc, Target) < FMath::Square(10.f))
		{
			bArrived = true;
			ScanTimer = 0.f;
			Scan();
		}
		return;
	}

	// Hover: small bob so it reads as alive.
	SetActorLocation(Target + FVector(0.f, 0.f, FMath::Sin(Age * 3.f) * 6.f));
	ScanTimer += DeltaSeconds;
	if (ScanTimer >= ScanInterval)
	{
		ScanTimer = 0.f;
		Scan();
	}
}

void ANVReconDrone::Scan()
{
	UNVAbilityComponent* Abilities = OwnerAbilities.Get();
	if (!Abilities)
	{
		return;
	}
	const FVector Eye = GetActorLocation();
	TArray<AActor*> Found;
	for (TActorIterator<AActor> It(GetWorld()); It; ++It)
	{
		AActor* A = *It;
		if (A == this || A == GetOwner() || A->IsHidden())
		{
			continue;
		}
		const UNVHealthComponent* H = A->FindComponentByClass<UNVHealthComponent>();
		if (!H || H->IsDead())
		{
			continue;
		}
		FVector Center, Extent;
		A->GetActorBounds(true, Center, Extent);
		if (FVector::DistSquared(Eye, Center) > FMath::Square(ScanRadius))
		{
			continue;
		}
		FCollisionQueryParams Params(SCENE_QUERY_STAT(NVDroneScan), true, this);
		Params.AddIgnoredActor(GetOwner());
		FHitResult Hit;
		const bool bBlocked = GetWorld()->LineTraceSingleByChannel(Hit, Eye, Center, ECC_Visibility, Params);
		if (!bBlocked || Hit.GetActor() == A)
		{
			Found.Add(A);
		}
	}
	if (Found.Num() > 0)
	{
		Abilities->AddMarks(Found, MarkDuration);
	}
	BP_OnScan(Found.Num());
}
