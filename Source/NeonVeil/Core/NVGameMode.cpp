#include "Core/NVGameMode.h"
#include "Abilities/NVAbilityComponent.h"
#include "Core/NVPlayerController.h"
#include "Core/NVMapPreloadSubsystem.h"
#include "UI/NVHUD.h"
#include "Objectives/NVObjectiveSubsystem.h"
#include "Objectives/NVObjectiveData.h"
#include "Save/NVSaveSubsystem.h"
#include "Save/NVSaveGame.h"
#include "World/NVCheckpoint.h"
#include "Character/NVPlayerCharacter.h"
#include "Combat/NVHealthComponent.h"
#include "Combat/NVWeaponComponent.h"
#include "NeonVeil.h"

#include "Camera/PlayerCameraManager.h"
#include "EngineUtils.h"
#include "GameFramework/PlayerStart.h"
#include "Kismet/GameplayStatics.h"
#include "TimerManager.h"
#include "Engine/World.h"

ANVGameMode::ANVGameMode()
{
	HUDClass = ANVHUD::StaticClass();
	PlayerControllerClass = ANVPlayerController::StaticClass();
	EndCardTitle = NSLOCTEXT("NeonVeil", "EndCardTitle", "Black Protocol");
	EndCardSubtitle = NSLOCTEXT("NeonVeil", "EndCardSub", "Mission M01 is not built yet. End of the current build.");
}

AActor* ANVGameMode::ChoosePlayerStart_Implementation(AController* Player)
{
	const UNVSaveSubsystem* Save = UNVSaveSubsystem::Get(this);
	const UNVSaveGame* Pending = Save ? Save->GetPendingRestore() : nullptr;
	APlayerStart* FirstPlain = nullptr;
	for (TActorIterator<APlayerStart> It(GetWorld()); It; ++It)
	{
		if (const ANVCheckpoint* CP = Cast<ANVCheckpoint>(*It))
		{
			if (Pending && CP->CheckpointID == Pending->CheckpointID)
			{
				return *It;
			}
		}
		else if (!FirstPlain)
		{
			FirstPlain = *It;
		}
	}
	if (Pending)
	{
		UE_LOG(LogNeonVeil, Warning, TEXT("Checkpoint %s not found in this map; using the level start"), *Pending->CheckpointID.ToString());
	}
	return FirstPlain ? FirstPlain : Super::ChoosePlayerStart_Implementation(Player);
}

void ANVGameMode::StartPlay()
{
	UNVObjectiveSubsystem* Obj = UNVObjectiveSubsystem::Get(this);
	UNVSaveSubsystem* SaveSys = UNVSaveSubsystem::Get(this);
	const UNVSaveGame* Pending = SaveSys ? SaveSys->GetPendingRestore() : nullptr;
	UNVMissionData* RestoreMission = Pending ? FindChainedMission(Pending->MissionID) : nullptr;
	const bool bRestoring = RestoreMission != nullptr;
	ActiveMission = bRestoring ? RestoreMission : Mission.Get();

	// Objective state must exist before actors' BeginPlay so doors and directors see it.
	if (Obj)
	{
		Obj->OnMissionCompleted.AddUniqueDynamic(this, &ANVGameMode::HandleMissionCompleted);
		if (bRestoring)
		{
			Obj->RestoreState(RestoreMission, Pending->CompletedObjectives);
		}
		else if (Mission)
		{
			Obj->StartMission(Mission);
		}
	}

	Super::StartPlay();

	// a package preloaded by the previous map has been consumed by now; queue the next one if asked
	if (UNVMapPreloadSubsystem* Pre = UNVMapPreloadSubsystem::Get(this))
	{
		Pre->Release();
		if (bPreloadNextMap && Mission && !Mission->NextMissionMap.IsNull())   // first mission's hand-off only
		{
			Pre->Preload(Mission->NextMissionMap.ToSoftObjectPath().GetLongPackageName());
		}
	}

	// Pawn has begun play now: restore health and weapons over the defaults.
	if (bRestoring)
	{
		if (APlayerController* PC = GetWorld()->GetFirstPlayerController())
		{
			if (ANVPlayerCharacter* P = Cast<ANVPlayerCharacter>(PC->GetPawn()))
			{
				P->GetHealth()->SetHealthDirect(Pending->Health);
				P->GetAbilities()->RestoreDisabledTags(Pending->DisabledAbilities);
				if (Pending->WeaponSlots.Num() > 0)
				{
					P->GetWeapons()->RestoreSlots(Pending->WeaponSlots, Pending->CurrentWeaponSlot);
				}
			}
		}
	}
	if (SaveSys && Pending)
	{
		SaveSys->FinishRestore();
	}
}

UNVMissionData* ANVGameMode::FindChainedMission(FName MissionID) const
{
	int32 Guard = 0;
	for (UNVMissionData* M = Mission; M && Guard < 16; M = M->ContinuesInto, ++Guard)
	{
		if (M->MissionID == MissionID)
		{
			return M;
		}
	}
	return nullptr;
}

void ANVGameMode::StartContinuation()
{
	if (ActiveMission)
	{
		UE_LOG(LogNeonVeil, Log, TEXT("Mission continues in this map: %s"), *ActiveMission->MissionID.ToString());
		if (UNVObjectiveSubsystem* Obj = UNVObjectiveSubsystem::Get(this))
		{
			Obj->StartMission(ActiveMission);
		}
	}
}

void ANVGameMode::HandleMissionCompleted(FName MissionID)
{
	// seamless hand-off inside this map: start the next mission on the next tick (we are inside the
	// objective subsystem's broadcast here)
	if (ActiveMission && ActiveMission->MissionID == MissionID && ActiveMission->ContinuesInto)
	{
		ActiveMission = ActiveMission->ContinuesInto;
		GetWorldTimerManager().SetTimerForNextTick(this, &ANVGameMode::StartContinuation);
		return;
	}
	if (bTransitionStarted)
	{
		return;
	}
	bTransitionStarted = true;
	UE_LOG(LogNeonVeil, Log, TEXT("End of mission %s: fade and end card"), *MissionID.ToString());

	if (APlayerController* PC = GetWorld()->GetFirstPlayerController())
	{
		if (ANVPlayerCharacter* P = Cast<ANVPlayerCharacter>(PC->GetPawn()))
		{
			P->SetGameplayInputLocked(true, true);
		}
		// EndFadeTime 0: no fade at all (the prologue tram carries straight on into the next map)
		if (PC->PlayerCameraManager && EndFadeTime > 0.f)
		{
			PC->PlayerCameraManager->StartCameraFade(0.f, 1.f, EndFadeTime, FLinearColor::Black, false, true);
		}
		if (ANVHUD* HUD = Cast<ANVHUD>(PC->GetHUD()))
		{
			HUD->SetInstruction(FText::GetEmpty());
		}
	}
	if (bShowEndCard)
	{
		GetWorldTimerManager().SetTimer(EndCardTimer, this, &ANVGameMode::ShowEndCard, EndFadeTime, false);
	}
	BP_OnMissionCompleted(MissionID);

	if (ActiveMission && !ActiveMission->NextMissionMap.IsNull())
	{
		GetWorldTimerManager().SetTimer(TransitionTimer, this, &ANVGameMode::TravelToNextMission, TransitionDelay, false);
	}
}

void ANVGameMode::ShowEndCard()
{
	if (APlayerController* PC = GetWorld()->GetFirstPlayerController())
	{
		if (ANVHUD* HUD = Cast<ANVHUD>(PC->GetHUD()))
		{
			HUD->SetHUDVisible(false);
			HUD->ShowTitleCard(EndCardTitle, EndCardSubtitle, 1000.f);
		}
	}
}

void ANVGameMode::TravelToNextMission()
{
	const FString MapName = ActiveMission->NextMissionMap.ToSoftObjectPath().GetLongPackageName();
	UE_LOG(LogNeonVeil, Log, TEXT("Travelling to %s"), *MapName);
	UGameplayStatics::OpenLevel(this, FName(*MapName));
}
