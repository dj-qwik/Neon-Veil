#include "Missions/NVSimulationDirector.h"
#include "Character/NVPlayerCharacter.h"
#include "Combat/NVTrainingTarget.h"
#include "Combat/NVWeaponComponent.h"
#include "Objectives/NVObjectiveSubsystem.h"
#include "UI/NVHUD.h"
#include "NeonVeil.h"

#include "Components/BoxComponent.h"
#include "GameFramework/PlayerController.h"

ANVSimulationDirector::ANVSimulationDirector()
{
	PrimaryActorTick.bCanEverTick = true;
	PrimaryActorTick.bStartWithTickEnabled = false;
	PrimaryActorTick.TickInterval = 0.05f;
	StartVolume = CreateDefaultSubobject<UBoxComponent>(TEXT("StartVolume"));
	SetRootComponent(StartVolume);
	StartVolume->SetBoxExtent(FVector(200.f, 400.f, 150.f));
	StartVolume->SetCollisionProfileName(TEXT("Trigger"));
}

void ANVSimulationDirector::BeginPlay()
{
	Super::BeginPlay();
	StartVolume->OnComponentBeginOverlap.AddDynamic(this, &ANVSimulationDirector::HandleStartOverlap);
	for (FNVSimStep& Step : Steps)
	{
		for (ANVTrainingTarget* T : Step.Targets)
		{
			if (T)
			{
				T->OnTargetCleared.AddDynamic(this, &ANVSimulationDirector::HandleTargetCleared);
			}
		}
	}
	// A checkpoint load past this objective leaves the suite idle.
	if (const UNVObjectiveSubsystem* Obj = UNVObjectiveSubsystem::Get(this))
	{
		bFinished = Obj->IsObjectiveComplete(ObjectiveID);
	}
}

FText ANVSimulationDirector::GetCurrentInstruction() const
{
	return Steps.IsValidIndex(CurrentStep) ? Steps[CurrentStep].Instruction : FText::GetEmpty();
}

void ANVSimulationDirector::HandleStartOverlap(UPrimitiveComponent*, AActor* Other, UPrimitiveComponent*, int32, bool, const FHitResult&)
{
	if (bRunning || bFinished || !Cast<ANVPlayerCharacter>(Other))
	{
		return;
	}
	const UNVObjectiveSubsystem* Obj = UNVObjectiveSubsystem::Get(this);
	if (Obj && Obj->IsObjectiveActive(ObjectiveID))
	{
		BeginRun();
	}
}

void ANVSimulationDirector::BeginRun()
{
	bRunning = true;
	UE_LOG(LogNeonVeil, Log, TEXT("Simulation started (%d steps)"), Steps.Num());
	SetActorTickEnabled(true);
	StartStep(0);
}

void ANVSimulationDirector::StartStep(int32 Index)
{
	if (!Steps.IsValidIndex(Index))
	{
		Finish();
		return;
	}
	CurrentStep = Index;
	StepTimer = 0.f;
	FNVSimStep& Step = Steps[Index];
	UE_LOG(LogNeonVeil, Log, TEXT("Simulation step %d: %s"), Index, *Step.Instruction.ToString());
	for (ANVTrainingTarget* T : Step.Targets)
	{
		if (T)
		{
			T->ResetTarget();
		}
	}
	if (APlayerController* PC = GetWorld()->GetFirstPlayerController())
	{
		if (ANVHUD* HUD = Cast<ANVHUD>(PC->GetHUD()))
		{
			HUD->SetInstruction(Step.Instruction);
			HUD->QueueSubtitles(Step.Lines);
		}
	}
	OnStepStarted.Broadcast(Index);
}

bool ANVSimulationDirector::IsStepDone(const FNVSimStep& Step) const
{
	switch (Step.Type)
	{
	case ENVSimStepType::ClearTargets:
		for (const ANVTrainingTarget* T : Step.Targets)
		{
			if (T && !T->IsCleared())
			{
				return false;
			}
		}
		return true;
	case ENVSimStepType::HoldAim:
	case ENVSimStepType::Wait:
		return StepTimer >= Step.Duration;
	case ENVSimStepType::EquipWeapon:
	{
		const APlayerController* PC = GetWorld()->GetFirstPlayerController();
		const ANVPlayerCharacter* P = PC ? Cast<ANVPlayerCharacter>(PC->GetPawn()) : nullptr;
		return P && P->GetWeapons()->GetCurrentSlotIndex() == Step.WeaponSlot;
	}
	}
	return true;
}

void ANVSimulationDirector::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	if (!bRunning || !Steps.IsValidIndex(CurrentStep))
	{
		return;
	}
	const FNVSimStep& Step = Steps[CurrentStep];
	if (Step.Type == ENVSimStepType::Wait)
	{
		StepTimer += DeltaSeconds;
	}
	else if (Step.Type == ENVSimStepType::HoldAim)
	{
		const APlayerController* PC = GetWorld()->GetFirstPlayerController();
		const ANVPlayerCharacter* P = PC ? Cast<ANVPlayerCharacter>(PC->GetPawn()) : nullptr;
		if (P && P->GetWeapons()->GetAdsAlpha() >= 0.99f)
		{
			StepTimer += DeltaSeconds;
		}
	}
	if (IsStepDone(Step))
	{
		CompleteStep();
	}
}

void ANVSimulationDirector::HandleTargetCleared(ANVTrainingTarget* Target)
{
	// Tick evaluates completion; nothing else to do here.
}

void ANVSimulationDirector::CompleteStep()
{
	UE_LOG(LogNeonVeil, Log, TEXT("Simulation step %d complete"), CurrentStep);
	StartStep(CurrentStep + 1);
}

void ANVSimulationDirector::DebugSkipStep()
{
	if (bRunning)
	{
		CompleteStep();
	}
}

void ANVSimulationDirector::Finish()
{
	bRunning = false;
	bFinished = true;
	CurrentStep = INDEX_NONE;
	SetActorTickEnabled(false);
	UE_LOG(LogNeonVeil, Log, TEXT("Simulation complete"));
	// Retire any target still live (e.g. from a skipped step) so the suite goes quiet.
	for (FNVSimStep& Step : Steps)
	{
		for (ANVTrainingTarget* T : Step.Targets)
		{
			if (T && !T->IsCleared())
			{
				T->Deactivate();
			}
		}
	}
	if (APlayerController* PC = GetWorld()->GetFirstPlayerController())
	{
		if (ANVHUD* HUD = Cast<ANVHUD>(PC->GetHUD()))
		{
			HUD->SetInstruction(FText::GetEmpty());
			HUD->QueueSubtitles(LinesOnComplete);
		}
	}
	if (UNVObjectiveSubsystem* Obj = UNVObjectiveSubsystem::Get(this))
	{
		Obj->SendEvent(CompletionTag);
	}
}
