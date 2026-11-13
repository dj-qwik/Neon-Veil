#include "Missions/NVSimulationDirector.h"
#include "Abilities/NVAbilityComponent.h"
#include "Character/NVPlayerCharacter.h"
#include "Combat/NVHealthComponent.h"
#include "Combat/NVTrainingTarget.h"
#include "Combat/NVWeaponComponent.h"
#include "Missions/NVSimVolleyEmitter.h"
#include "Objectives/NVObjectiveSubsystem.h"
#include "UI/NVHUD.h"
#include "World/NVSurveillanceCamera.h"
#include "NeonVeil.h"

#include "Components/AudioComponent.h"
#include "Components/BoxComponent.h"
#include "Kismet/GameplayStatics.h"
#include "Sound/AmbientSound.h"
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
				T->OnTargetCleared.AddUniqueDynamic(this, &ANVSimulationDirector::HandleTargetCleared);
			}
		}
		if (Step.Emitter)
		{
			Step.Emitter->OnVolleyFinished.AddUniqueDynamic(this, &ANVSimulationDirector::HandleVolleyFinished);
		}
		for (ANVSurveillanceCamera* C : Step.Cameras)
		{
			if (C)
			{
				C->OnDetected.AddUniqueDynamic(this, &ANVSimulationDirector::HandleCameraDetected);
			}
		}
	}
	if (UNVObjectiveSubsystem* Obj = UNVObjectiveSubsystem::Get(this))
	{
		Obj->OnGameplayEvent.AddDynamic(this, &ANVSimulationDirector::HandleGameplayEvent);
		// A checkpoint load past this objective leaves the suite idle.
		bFinished = Obj->IsObjectiveComplete(ObjectiveID);
	}
}

ANVPlayerCharacter* ANVSimulationDirector::GetPlayer() const
{
	const APlayerController* PC = GetWorld()->GetFirstPlayerController();
	return PC ? Cast<ANVPlayerCharacter>(PC->GetPawn()) : nullptr;
}

ANVHUD* ANVSimulationDirector::GetHUD() const
{
	const APlayerController* PC = GetWorld()->GetFirstPlayerController();
	return PC ? Cast<ANVHUD>(PC->GetHUD()) : nullptr;
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
	if (ANVPlayerCharacter* P = GetPlayer())
	{
		// Training rounds can sting but never kill.
		P->GetHealth()->bCannotDie = true;
		P->GetHealth()->OnHealthChanged.AddUniqueDynamic(this, &ANVSimulationDirector::HandlePlayerHealthChanged);
	}
	SetActorTickEnabled(true);
	StartSimMusic();
	StartStep(0);
}

void ANVSimulationDirector::StartSimMusic()
{
	if (SimMusic && !SimMusicComp)
	{
		SimMusicComp = UGameplayStatics::SpawnSound2D(this, SimMusic, 1.f, 1.f, 0.f, nullptr, false, false);
		if (SimMusicComp)
		{
			SimMusicComp->FadeIn(SimMusicFadeIn, SimMusicVolume);
		}
	}
	if (MusicToDuck && MusicToDuck->GetAudioComponent())
	{
		MusicToDuck->GetAudioComponent()->AdjustVolume(SimMusicFadeIn, DuckLevel);
	}
}

void ANVSimulationDirector::StopSimMusic()
{
	if (SimMusicComp)
	{
		SimMusicComp->FadeOut(SimMusicFadeOut, 0.f);
		SimMusicComp = nullptr;
	}
	if (MusicToDuck && MusicToDuck->GetAudioComponent())
	{
		MusicToDuck->GetAudioComponent()->AdjustVolume(SimMusicFadeOut, 1.f);
	}
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
	VolleyState = EVolleyState::WaitArea;
	bVolleyHit = false;
	RetryTimer = 0.f;
	bEventReceived = false;
	FNVSimStep& Step = Steps[Index];
	UE_LOG(LogNeonVeil, Log, TEXT("Simulation step %d: %s"), Index, *Step.Instruction.ToString());
	for (ANVTrainingTarget* T : Step.Targets)
	{
		if (T)
		{
			T->ResetTarget();
		}
	}
	for (ANVSurveillanceCamera* C : Step.Cameras)
	{
		if (C)
		{
			C->SetCameraActive(true);
		}
	}
	if (Step.Type == ENVSimStepType::Volley)
	{
		if (ANVPlayerCharacter* P = GetPlayer())
		{
			P->GetHealth()->Heal(P->GetHealth()->GetMaxHealth());
		}
	}
	if (ANVHUD* HUD = GetHUD())
	{
		HUD->SetInstruction(Step.Instruction);
		HUD->QueueSubtitles(Step.Lines);
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
		const ANVPlayerCharacter* P = GetPlayer();
		return P && P->GetWeapons()->GetCurrentSlotIndex() == Step.WeaponSlot;
	}
	case ENVSimStepType::Volley:
		return VolleyState == EVolleyState::Passed;
	case ENVSimStepType::MarkTargets:
	{
		const ANVPlayerCharacter* P = GetPlayer();
		if (!P)
		{
			return false;
		}
		const TArray<AActor*> Marked = P->GetAbilities()->GetMarkedActors();
		int32 Count = 0;
		for (const ANVTrainingTarget* T : Step.Targets)
		{
			Count += (T && Marked.Contains(T)) ? 1 : 0;
		}
		return Count >= Step.MinMarks;
	}
	case ENVSimStepType::WaitForEvent:
		return bEventReceived;
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
	switch (Step.Type)
	{
	case ENVSimStepType::Wait:
		StepTimer += DeltaSeconds;
		break;
	case ENVSimStepType::HoldAim:
	{
		const ANVPlayerCharacter* P = GetPlayer();
		if (P && P->GetWeapons()->GetAdsAlpha() >= 0.99f)
		{
			StepTimer += DeltaSeconds;
		}
		break;
	}
	case ENVSimStepType::Volley:
		TickVolley(Step, DeltaSeconds);
		break;
	case ENVSimStepType::WaitForEvent:
		if (ANVHUD* HUD = GetHUD())
		{
			float D = 0.f;
			for (const ANVSurveillanceCamera* C : Step.Cameras)
			{
				D = C ? FMath::Max(D, C->GetDetection()) : D;
			}
			HUD->SetDetection(D);
		}
		break;
	default:
		break;
	}
	if (IsStepDone(Step))
	{
		CompleteStep();
	}
}

void ANVSimulationDirector::TickVolley(const FNVSimStep& Step, float DeltaSeconds)
{
	ANVPlayerCharacter* P = GetPlayer();
	if (!P || !Step.Emitter)
	{
		return;
	}
	const bool bInArea = !Step.Area || Step.Area->IsOverlappingActor(P);
	switch (VolleyState)
	{
	case EVolleyState::WaitArea:
		if (bInArea)
		{
			bVolleyHit = false;
			VolleyState = EVolleyState::Running;
			Step.Emitter->StartVolley(P, Step.WarmupSeconds, Step.Duration);
			if (ANVHUD* HUD = GetHUD())
			{
				HUD->ShowThreat(Step.WarningText, Step.WarmupSeconds + 0.3f);
			}
		}
		break;
	case EVolleyState::Running:
		if (!bInArea)
		{
			FailStep(TEXT("left the area"));
		}
		break;
	case EVolleyState::Retry:
		RetryTimer -= DeltaSeconds;
		if (RetryTimer <= 0.f)
		{
			P->GetHealth()->Heal(P->GetHealth()->GetMaxHealth());
			VolleyState = EVolleyState::WaitArea;
		}
		break;
	default:
		break;
	}
}

void ANVSimulationDirector::HandlePlayerHealthChanged(UNVHealthComponent* HealthComp, float NewHealth, float Delta, AActor* InstigatorActor, FGameplayTag DamageType)
{
	if (Delta < 0.f && Steps.IsValidIndex(CurrentStep) && Steps[CurrentStep].Type == ENVSimStepType::Volley && VolleyState == EVolleyState::Running)
	{
		bVolleyHit = true;
	}
}

void ANVSimulationDirector::HandleVolleyFinished()
{
	if (!Steps.IsValidIndex(CurrentStep) || Steps[CurrentStep].Type != ENVSimStepType::Volley || VolleyState != EVolleyState::Running)
	{
		return;
	}
	if (bVolleyHit)
	{
		FailStep(TEXT("took damage"));
	}
	else
	{
		UE_LOG(LogNeonVeil, Log, TEXT("Volley survived without damage"));
		VolleyState = EVolleyState::Passed;
	}
}

void ANVSimulationDirector::HandleGameplayEvent(FGameplayTag EventTag)
{
	if (bRunning && Steps.IsValidIndex(CurrentStep) && Steps[CurrentStep].Type == ENVSimStepType::WaitForEvent
		&& Steps[CurrentStep].EventTag.IsValid() && EventTag.MatchesTagExact(Steps[CurrentStep].EventTag))
	{
		bEventReceived = true;
	}
}

void ANVSimulationDirector::HandleCameraDetected(AActor* Detected)
{
	if (!bRunning || !Steps.IsValidIndex(CurrentStep) || Steps[CurrentStep].Type != ENVSimStepType::WaitForEvent)
	{
		return;
	}
	FailStep(TEXT("detected by camera"));
	const FNVSimStep& Step = Steps[CurrentStep];
	ANVPlayerCharacter* P = GetPlayer();
	if (P && Step.ResetPoint)
	{
		P->TeleportTo(Step.ResetPoint->GetActorLocation(), Step.ResetPoint->GetActorRotation());
		if (AController* C = P->GetController())
		{
			C->SetControlRotation(Step.ResetPoint->GetActorRotation());
		}
	}
}

void ANVSimulationDirector::FailStep(const TCHAR* Why)
{
	FNVSimStep& Step = Steps[CurrentStep];
	UE_LOG(LogNeonVeil, Log, TEXT("Simulation step %d failed (%s), retrying"), CurrentStep, Why);
	if (Step.Type == ENVSimStepType::Volley)
	{
		if (Step.Emitter)
		{
			Step.Emitter->StopVolley();
		}
		VolleyState = EVolleyState::Retry;
		RetryTimer = 2.5f;
	}
	if (ANVHUD* HUD = GetHUD())
	{
		HUD->ShowThreat(Step.Type == ENVSimStepType::WaitForEvent
			? NSLOCTEXT("NeonVeil", "SimDetected", "Detected - simulation reset")
			: NSLOCTEXT("NeonVeil", "SimFailed", "Calibration failed - resetting"), 2.f);
		HUD->QueueSubtitles(Step.FailLines);
	}
}

void ANVSimulationDirector::HandleTargetCleared(ANVTrainingTarget* Target)
{
	// Tick evaluates completion; nothing else to do here.
}

void ANVSimulationDirector::EndStepSideEffects(FNVSimStep& Step)
{
	for (ANVSurveillanceCamera* C : Step.Cameras)
	{
		if (C)
		{
			C->SetCameraActive(false);
		}
	}
	if (Step.Emitter)
	{
		Step.Emitter->StopVolley();
	}
	// Targets that were only there to be marked go away once the step is done.
	if (Step.Type != ENVSimStepType::ClearTargets)
	{
		for (ANVTrainingTarget* T : Step.Targets)
		{
			if (T && !T->IsCleared())
			{
				T->Deactivate();
			}
		}
	}
}

void ANVSimulationDirector::CompleteStep()
{
	UE_LOG(LogNeonVeil, Log, TEXT("Simulation step %d complete"), CurrentStep);
	EndStepSideEffects(Steps[CurrentStep]);
	StartStep(CurrentStep + 1);
}

void ANVSimulationDirector::DebugSkipStep()
{
	if (bRunning && Steps.IsValidIndex(CurrentStep))
	{
		// A skipped step leaves nothing live behind.
		for (ANVTrainingTarget* T : Steps[CurrentStep].Targets)
		{
			if (T && !T->IsCleared())
			{
				T->Deactivate();
			}
		}
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
	StopSimMusic();
	// Retire anything still live (e.g. from a skipped step) so the suite goes quiet.
	for (FNVSimStep& Step : Steps)
	{
		for (ANVTrainingTarget* T : Step.Targets)
		{
			if (T && !T->IsCleared())
			{
				T->Deactivate();
			}
		}
		for (ANVSurveillanceCamera* C : Step.Cameras)
		{
			if (C && C->IsCameraActive())
			{
				C->SetCameraActive(false);
			}
		}
	}
	if (ANVPlayerCharacter* P = GetPlayer())
	{
		P->GetHealth()->bCannotDie = false;
		P->GetHealth()->OnHealthChanged.RemoveDynamic(this, &ANVSimulationDirector::HandlePlayerHealthChanged);
	}
	if (ANVHUD* HUD = GetHUD())
	{
		HUD->SetInstruction(FText::GetEmpty());
		HUD->QueueSubtitles(LinesOnComplete);
	}
	if (UNVObjectiveSubsystem* Obj = UNVObjectiveSubsystem::Get(this))
	{
		Obj->SendEvent(CompletionTag);
	}
}
