#include "World/NVObjectiveDoor.h"
#include "Objectives/NVObjectiveSubsystem.h"
#include "NeonVeil.h"
#include "Components/StaticMeshComponent.h"
#include "Kismet/GameplayStatics.h"
#include "Sound/SoundBase.h"

ANVObjectiveDoor::ANVObjectiveDoor()
{
	PrimaryActorTick.bCanEverTick = true;
	PrimaryActorTick.bStartWithTickEnabled = false;

	Root = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
	SetRootComponent(Root);
	Frame = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Frame"));
	Frame->SetupAttachment(Root);
	PanelLeft = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("PanelLeft"));
	PanelLeft->SetupAttachment(Root);
	PanelRight = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("PanelRight"));
	PanelRight->SetupAttachment(Root);
	PanelLeft->SetMobility(EComponentMobility::Movable);
	PanelRight->SetMobility(EComponentMobility::Movable);
}

void ANVObjectiveDoor::BeginPlay()
{
	Super::BeginPlay();
	LeftClosed = PanelLeft->GetRelativeLocation();
	RightClosed = PanelRight->GetRelativeLocation();
	if (UNVObjectiveSubsystem* Obj = UNVObjectiveSubsystem::Get(this))
	{
		Obj->OnObjectiveActivated.AddDynamic(this, &ANVObjectiveDoor::HandleObjectiveEvent);
		Obj->OnObjectiveCompleted.AddDynamic(this, &ANVObjectiveDoor::HandleObjectiveEvent);
		Obj->OnObjectivesRestored.AddDynamic(this, &ANVObjectiveDoor::Evaluate);
	}
	Evaluate();
	if (bTargetOpen)
	{
		SetOpen(true, true);
	}
}

void ANVObjectiveDoor::HandleObjectiveEvent(FName)
{
	Evaluate();
}

void ANVObjectiveDoor::Evaluate()
{
	const UNVObjectiveSubsystem* Obj = UNVObjectiveSubsystem::Get(this);
	if (!Obj)
	{
		return;
	}
	bool bShouldOpen = false;
	if (!OpenWhenComplete.IsNone() && Obj->IsObjectiveComplete(OpenWhenComplete))
	{
		bShouldOpen = true;
	}
	if (!OpenWhenActive.IsNone() && (Obj->IsObjectiveActive(OpenWhenActive) || Obj->IsObjectiveComplete(OpenWhenActive)))
	{
		bShouldOpen = true;
	}
	if (bShouldOpen && !bTargetOpen)
	{
		SetOpen(true);
	}
}

void ANVObjectiveDoor::SetOpen(bool bOpen, bool bInstant)
{
	if (bOpen && !bTargetOpen && OpenSound && !bInstant)
	{
		UGameplayStatics::PlaySoundAtLocation(this, OpenSound, GetActorLocation());
	}
	if (bOpen != bTargetOpen)
	{
		UE_LOG(LogNeonVeil, Log, TEXT("%s %s"), *GetName(), bOpen ? TEXT("opening") : TEXT("closing"));
	}
	bTargetOpen = bOpen;
	if (bInstant)
	{
		Alpha = bOpen ? 1.f : 0.f;
		Tick(0.f);
	}
	SetActorTickEnabled(true);
}

void ANVObjectiveDoor::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	Alpha = FMath::FInterpConstantTo(Alpha, bTargetOpen ? 1.f : 0.f, DeltaSeconds, 1.f / FMath::Max(0.05f, OpenTime));
	const float E = FMath::InterpEaseInOut(0.f, 1.f, Alpha, 2.f);
	PanelLeft->SetRelativeLocation(LeftClosed + FVector(0.f, -SlideDistance * E, 0.f));
	PanelRight->SetRelativeLocation(RightClosed + FVector(0.f, SlideDistance * E, 0.f));
	if (FMath::IsNearlyEqual(Alpha, bTargetOpen ? 1.f : 0.f))
	{
		SetActorTickEnabled(false);
	}
}
