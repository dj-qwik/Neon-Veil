#include "Core/NVGameMode.h"
#include "UI/NVHUD.h"
#include "Core/NVPlayerController.h"
#include "Objectives/NVObjectiveSubsystem.h"
#include "Objectives/NVObjectiveData.h"
#include "NeonVeil.h"
#include "Kismet/GameplayStatics.h"
#include "TimerManager.h"
#include "Engine/World.h"

ANVGameMode::ANVGameMode()
{
	HUDClass = ANVHUD::StaticClass();
	PlayerControllerClass = ANVPlayerController::StaticClass();
}

void ANVGameMode::StartPlay()
{
	Super::StartPlay();
	if (UNVObjectiveSubsystem* Obj = UNVObjectiveSubsystem::Get(this))
	{
		Obj->OnMissionCompleted.AddDynamic(this, &ANVGameMode::HandleMissionCompleted);
		// A checkpoint load may already have restored this mission; only start fresh otherwise.
		if (Mission && Obj->GetCurrentMission() != Mission)
		{
			Obj->StartMission(Mission);
		}
	}
}

void ANVGameMode::HandleMissionCompleted(FName MissionID)
{
	if (bTransitionStarted)
	{
		return;
	}
	bTransitionStarted = true;
	BP_OnMissionCompleted(MissionID);
	if (Mission && !Mission->NextMissionMap.IsNull())
	{
		GetWorldTimerManager().SetTimer(TransitionTimer, this, &ANVGameMode::TravelToNextMission, TransitionDelay, false);
	}
	else
	{
		UE_LOG(LogNeonVeil, Log, TEXT("Mission %s complete; no next map set (end of current build)."), *MissionID.ToString());
	}
}

void ANVGameMode::TravelToNextMission()
{
	const FString MapName = Mission->NextMissionMap.ToSoftObjectPath().GetLongPackageName();
	UE_LOG(LogNeonVeil, Log, TEXT("Travelling to %s"), *MapName);
	UGameplayStatics::OpenLevel(this, FName(*MapName));
}
