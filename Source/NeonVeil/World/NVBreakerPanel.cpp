#include "World/NVBreakerPanel.h"

#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Materials/MaterialInterface.h"
#include "Objectives/NVObjectiveSubsystem.h"
#include "UObject/ConstructorHelpers.h"

namespace
{
	const TCHAR* CubePath = TEXT("/Engine/BasicShapes/Cube.Cube");
}

UStaticMeshComponent* ANVBreakerPanel::MakePart(FName Name, USceneComponent* Parent, const FVector& Loc, const FVector& Size)
{
	static ConstructorHelpers::FObjectFinder<UStaticMesh> Cube(CubePath);
	UStaticMeshComponent* C = CreateDefaultSubobject<UStaticMeshComponent>(Name);
	C->SetupAttachment(Parent);
	C->SetStaticMesh(Cube.Object);
	C->SetRelativeLocation(Loc);
	C->SetRelativeScale3D(Size / 100.f);
	C->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	C->SetCastShadow(false);
	C->SetCanEverAffectNavigation(false);
	return C;
}

ANVBreakerPanel::ANVBreakerPanel()
{
	PrimaryActorTick.bCanEverTick = true;
	PrimaryActorTick.bStartWithTickEnabled = false;

	static ConstructorHelpers::FObjectFinder<UStaticMesh> Cube(CubePath);
	// the inherited Mesh is the root on plain interactables; here a scene root sits on the wall surface
	USceneComponent* PanelRoot = CreateDefaultSubobject<USceneComponent>(TEXT("PanelRoot"));
	SetRootComponent(PanelRoot);
	Mesh->SetupAttachment(PanelRoot);
	// the inherited Mesh is the housing (it keeps the interaction collision and the focus outline)
	Mesh->SetStaticMesh(Cube.Object);
	Mesh->SetRelativeLocation(FVector(9.f, 0.f, 140.f));
	Mesh->SetRelativeScale3D(FVector(18.f, 72.f, 96.f) / 100.f);

	USceneComponent* Root = PanelRoot;
	FacePlate = MakePart(TEXT("FacePlate"), Root, FVector(18.6f, 0.f, 140.f), FVector(1.2f, 64.f, 88.f));
	Hazard = MakePart(TEXT("Hazard"), Root, FVector(19.4f, 0.f, 103.f), FVector(1.f, 64.f, 7.f));
	for (int32 i = 0; i < 6; ++i)
	{
		const float Y = -25.f + i * 10.f;
		Fuses.Add(MakePart(*FString::Printf(TEXT("Fuse%d"), i), Root, FVector(21.f, Y, 166.f), FVector(4.f, 6.f, 14.f)));
	}
	LampRed = MakePart(TEXT("LampRed"), Root, FVector(20.5f, -22.f, 128.f), FVector(3.f, 7.f, 7.f));
	LampGreen = MakePart(TEXT("LampGreen"), Root, FVector(20.5f, -10.f, 128.f), FVector(3.f, 7.f, 7.f));

	LeverPivot = CreateDefaultSubobject<USceneComponent>(TEXT("LeverPivot"));
	LeverPivot->SetupAttachment(Root);
	LeverPivot->SetRelativeLocation(FVector(22.f, 16.f, 130.f));
	LeverPivot->SetRelativeRotation(FRotator(OffPitch, 0.f, 0.f));
	LeverArm = MakePart(TEXT("LeverArm"), LeverPivot, FVector(0.f, 0.f, 15.f), FVector(4.f, 4.f, 30.f));
	LeverGrip = MakePart(TEXT("LeverGrip"), LeverPivot, FVector(0.f, 0.f, 31.f), FVector(6.f, 14.f, 6.f));
}

void ANVBreakerPanel::ApplyLook()
{
	auto Set = [](UStaticMeshComponent* C, UMaterialInterface* M)
	{
		if (C && M)
		{
			C->SetMaterial(0, M);
		}
	};
	Set(Mesh, HousingMaterial);
	Set(FacePlate, PlateMaterial);
	Set(Hazard, HazardMaterial);
	Set(LeverArm, LeverMaterial);
	Set(LeverGrip, HazardMaterial);
	for (UStaticMeshComponent* F : Fuses)
	{
		Set(F, FuseMaterial);
	}
}

void ANVBreakerPanel::SetLamps(bool bOn)
{
	if (LampRed && LampOffMaterial && RedLitMaterial)
	{
		LampRed->SetMaterial(0, bOn ? LampOffMaterial.Get() : RedLitMaterial.Get());
	}
	if (LampGreen && LampOffMaterial && GreenLitMaterial)
	{
		LampGreen->SetMaterial(0, bOn ? GreenLitMaterial.Get() : LampOffMaterial.Get());
	}
}

void ANVBreakerPanel::OnConstruction(const FTransform& Transform)
{
	Super::OnConstruction(Transform);
	ApplyLook();
	SetLamps(false);
	LeverPivot->SetRelativeRotation(FRotator(OffPitch, 0.f, 0.f));
}

void ANVBreakerPanel::BeginPlay()
{
	Super::BeginPlay();
	// loaded past this step (checkpoint): show the breaker already thrown
	const UNVObjectiveSubsystem* Obj = UNVObjectiveSubsystem::Get(this);
	const bool bDone = Obj && !GetRequiredActiveObjective().IsNone() && Obj->IsObjectiveComplete(GetRequiredActiveObjective());
	LeverPivot->SetRelativeRotation(FRotator(bDone ? OnPitch : OffPitch, 0.f, 0.f));
	SetLamps(bDone);
}

void ANVBreakerPanel::Interact_Implementation(AActor* Interactor)
{
	if (!CanInteract_Implementation(Interactor))
	{
		return;
	}
	Super::Interact_Implementation(Interactor);
	bThrowing = true;
	ThrowAlpha = 0.f;
	SetActorTickEnabled(true);
}

void ANVBreakerPanel::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	if (!bThrowing)
	{
		SetActorTickEnabled(false);
		return;
	}
	ThrowAlpha = FMath::Min(1.f, ThrowAlpha + DeltaSeconds / ThrowTime);
	// quick start, hard stop: a heavy switch slamming home
	const float A = FMath::InterpEaseIn(0.f, 1.f, ThrowAlpha, 2.2f);
	LeverPivot->SetRelativeRotation(FRotator(FMath::Lerp(OffPitch, OnPitch, A), 0.f, 0.f));
	if (ThrowAlpha >= 1.f)
	{
		bThrowing = false;
		SetLamps(true);
		SetActorTickEnabled(false);
	}
}

void ANVBreakerPanel::SetFocused_Implementation(bool bFocused)
{
	Super::SetFocused_Implementation(bFocused);
	for (UStaticMeshComponent* C : {FacePlate.Get(), LeverArm.Get(), LeverGrip.Get()})
	{
		if (C)
		{
			C->SetRenderCustomDepth(bFocused);
			C->SetCustomDepthStencilValue(FocusStencilValue);
		}
	}
}
