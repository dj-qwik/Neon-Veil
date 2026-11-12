#include "World/NVSurveillanceCamera.h"
#include "Abilities/NVAbilityComponent.h"
#include "NeonVeil.h"

#include "Camera/CameraComponent.h"
#include "Components/SpotLightComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/Pawn.h"
#include "Materials/MaterialInterface.h"
#include "UObject/ConstructorHelpers.h"

ANVSurveillanceCamera::ANVSurveillanceCamera()
{
	PrimaryActorTick.bCanEverTick = true;
	PrimaryActorTick.TickInterval = 0.03f;

	Root = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
	SetRootComponent(Root);

	static ConstructorHelpers::FObjectFinder<UStaticMesh> CubeMesh(TEXT("/Engine/BasicShapes/Cube.Cube"));
	static ConstructorHelpers::FObjectFinder<UStaticMesh> ConeMesh(TEXT("/Engine/BasicShapes/Cone.Cone"));

	Mount = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Mount"));
	Mount->SetupAttachment(Root);
	Mount->SetRelativeScale3D(FVector(0.15f, 0.15f, 0.4f));
	Mount->SetRelativeLocation(FVector(0.f, 0.f, 20.f));
	Mount->SetCollisionProfileName(TEXT("NoCollision"));

	Head = CreateDefaultSubobject<USceneComponent>(TEXT("Head"));
	Head->SetupAttachment(Root);

	HeadMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("HeadMesh"));
	HeadMesh->SetupAttachment(Head);
	HeadMesh->SetRelativeScale3D(FVector(0.4f, 0.2f, 0.2f));
	HeadMesh->SetCollisionProfileName(TEXT("NoCollision"));

	Cone = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Cone"));
	Cone->SetupAttachment(Head);
	Cone->SetCollisionProfileName(TEXT("NoCollision"));
	Cone->CastShadow = false;
	Cone->SetHiddenInGame(true);

	if (CubeMesh.Succeeded())
	{
		Mount->SetStaticMesh(CubeMesh.Object);
		HeadMesh->SetStaticMesh(CubeMesh.Object);
	}
	if (ConeMesh.Succeeded())
	{
		Cone->SetStaticMesh(ConeMesh.Object);
	}

	Spot = CreateDefaultSubobject<USpotLightComponent>(TEXT("Spot"));
	Spot->SetupAttachment(Head);
	Spot->SetIntensity(0.f);
	Spot->SetLightColor(FLinearColor(1.f, 0.3f, 0.25f));
	Spot->SetCastShadows(false);
}

void ANVSurveillanceCamera::OnConstruction(const FTransform& Transform)
{
	Super::OnConstruction(Transform);
	LayoutCone();
}

void ANVSurveillanceCamera::LayoutCone()
{
	// Engine cone: 100 units tall, base radius 50, apex at +Z. Pitch +90 points the apex back at
	// the camera and the base along +X; then scale to the view distance and angle.
	const float Radius = ViewDistance * FMath::Tan(FMath::DegreesToRadians(HalfAngle));
	Cone->SetRelativeRotation(FRotator(90.f, 0.f, 0.f));
	Cone->SetRelativeLocation(FVector(ViewDistance * 0.5f, 0.f, 0.f));
	Cone->SetRelativeScale3D(FVector(Radius / 50.f, Radius / 50.f, ViewDistance / 100.f));
	if (ConeMaterial)
	{
		Cone->SetMaterial(0, ConeMaterial);
	}
	Spot->SetOuterConeAngle(HalfAngle);
	Spot->SetInnerConeAngle(HalfAngle * 0.7f);
	Spot->SetAttenuationRadius(ViewDistance);
}

void ANVSurveillanceCamera::BeginPlay()
{
	Super::BeginPlay();
	LayoutCone();
	SetCameraActive(bStartActive);
}

void ANVSurveillanceCamera::SetCameraActive(bool bActive)
{
	bCameraActive = bActive;
	Detection = 0.f;
	Cooldown = 0.f;
	Cone->SetHiddenInGame(!bActive);
	Spot->SetIntensity(bActive ? 2500.f : 0.f);
	SetActorTickEnabled(bActive);
	UE_LOG(LogNeonVeil, Log, TEXT("%s %s"), *GetName(), bActive ? TEXT("active") : TEXT("inactive"));
}

bool ANVSurveillanceCamera::CanSee(const AActor* Target) const
{
	if (!Target || UNVAbilityComponent::IsActorCloaked(Target))
	{
		return false;
	}
	const FVector Eye = Head->GetComponentLocation();
	// Test the head and the chest so peeking counts.
	FVector Points[2] = { Target->GetActorLocation(), Target->GetActorLocation() + FVector(0.f, 0.f, 60.f) };
	if (const UCameraComponent* Cam = Target->FindComponentByClass<UCameraComponent>())
	{
		Points[1] = Cam->GetComponentLocation();
	}
	const FVector Fwd = Head->GetForwardVector();
	const float CosHalf = FMath::Cos(FMath::DegreesToRadians(HalfAngle));
	for (const FVector& P : Points)
	{
		const FVector To = P - Eye;
		const float Dist = To.Size();
		if (Dist > ViewDistance || Dist < 1.f || FVector::DotProduct(To / Dist, Fwd) < CosHalf)
		{
			continue;
		}
		FCollisionQueryParams Params(SCENE_QUERY_STAT(NVCameraSight), true, this);
		Params.AddIgnoredActor(Target);
		if (!GetWorld()->LineTraceTestByChannel(Eye, P, ECC_Visibility, Params))
		{
			return true;
		}
	}
	return false;
}

void ANVSurveillanceCamera::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	if (!bCameraActive)
	{
		return;
	}
	SweepTime += DeltaSeconds;
	const float Yaw = SweepPeriod > 0.f ? SweepAngle * FMath::Sin(SweepTime * 2.f * PI / SweepPeriod) : 0.f;
	Head->SetRelativeRotation(FRotator(0.f, Yaw, 0.f));

	if (Cooldown > 0.f)
	{
		Cooldown -= DeltaSeconds;
		return;
	}
	const APlayerController* PC = GetWorld()->GetFirstPlayerController();
	APawn* Player = PC ? PC->GetPawn() : nullptr;
	if (CanSee(Player))
	{
		Detection = FMath::Min(1.f, Detection + DeltaSeconds / FMath::Max(0.05f, TimeToDetect));
		if (Detection >= 1.f)
		{
			UE_LOG(LogNeonVeil, Log, TEXT("%s detected %s"), *GetName(), *GetNameSafe(Player));
			Detection = 0.f;
			Cooldown = 1.5f;
			OnDetected.Broadcast(Player);
		}
	}
	else
	{
		Detection = FMath::Max(0.f, Detection - DeltaSeconds / (TimeToDetect * 2.f));
	}
}
