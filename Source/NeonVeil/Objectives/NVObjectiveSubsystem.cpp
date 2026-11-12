#include "Objectives/NVObjectiveSubsystem.h"
#include "NeonVeil.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "Kismet/GameplayStatics.h"

UNVObjectiveSubsystem* UNVObjectiveSubsystem::Get(const UObject* WorldContext)
{
	const UWorld* World = WorldContext ? WorldContext->GetWorld() : nullptr;
	const UGameInstance* GI = World ? World->GetGameInstance() : nullptr;
	return GI ? GI->GetSubsystem<UNVObjectiveSubsystem>() : nullptr;
}

void UNVObjectiveSubsystem::StartMission(UNVMissionData* Mission)
{
	CurrentMission = Mission;
	Completed.Reset();
	Active.Reset();
	bMissionComplete = false;
	UE_LOG(LogNeonVeil, Log, TEXT("Mission started: %s"), Mission ? *Mission->MissionID.ToString() : TEXT("None"));
	RefreshActive(true);
}

void UNVObjectiveSubsystem::RestoreState(UNVMissionData* Mission, const TArray<FName>& CompletedIDs)
{
	CurrentMission = Mission;
	Completed = TSet<FName>(CompletedIDs);
	Active.Reset();
	bMissionComplete = false;
	RefreshActive(false);
	UE_LOG(LogNeonVeil, Log, TEXT("Objectives restored: %d complete, %d active"), Completed.Num(), Active.Num());
	OnObjectivesRestored.Broadcast();
	// Restoring never triggers the mission-complete transition; the save happens before it.
}

bool UNVObjectiveSubsystem::ArePrerequisitesMet(const FNVObjectiveDef& Def) const
{
	for (const FName& Pre : Def.Prerequisites)
	{
		if (!Completed.Contains(Pre))
		{
			return false;
		}
	}
	return true;
}

bool UNVObjectiveSubsystem::IsObjectiveActive(FName ObjectiveID) const
{
	return Active.Contains(ObjectiveID);
}

void UNVObjectiveSubsystem::RefreshActive(bool bBroadcast)
{
	if (!CurrentMission)
	{
		return;
	}
	for (const FNVObjectiveDef& Def : CurrentMission->Objectives)
	{
		if (Completed.Contains(Def.ObjectiveID) || Active.Contains(Def.ObjectiveID))
		{
			continue;
		}
		if (ArePrerequisitesMet(Def))
		{
			Active.Add(Def.ObjectiveID);
			UE_LOG(LogNeonVeil, Log, TEXT("Objective active: %s"), *Def.ObjectiveID.ToString());
			if (bBroadcast)
			{
				OnObjectiveActivated.Broadcast(Def.ObjectiveID);
				if (Def.CheckpointPolicy == ENVCheckpointPolicy::OnActivate)
				{
					OnCheckpointRequested.Broadcast(Def.ObjectiveID);
				}
			}
		}
	}
}

bool UNVObjectiveSubsystem::CompleteObjective(FName ObjectiveID)
{
	if (!CurrentMission || !Active.Contains(ObjectiveID))
	{
		return false;
	}
	const FNVObjectiveDef* Def = CurrentMission->FindObjective(ObjectiveID);
	if (!Def)
	{
		return false;
	}
	Active.Remove(ObjectiveID);
	Completed.Add(ObjectiveID);
	UE_LOG(LogNeonVeil, Log, TEXT("Objective complete: %s"), *ObjectiveID.ToString());
	OnObjectiveCompleted.Broadcast(ObjectiveID);

	RefreshActive(true);
	if (Def->CheckpointPolicy == ENVCheckpointPolicy::OnComplete)
	{
		OnCheckpointRequested.Broadcast(ObjectiveID);
	}
	CheckMissionComplete();
	return true;
}

bool UNVObjectiveSubsystem::SendEvent(FGameplayTag EventTag)
{
	if (!CurrentMission || !EventTag.IsValid())
	{
		return false;
	}
	TArray<FName> ToComplete;
	for (const FName& ID : Active)
	{
		const FNVObjectiveDef* Def = CurrentMission->FindObjective(ID);
		if (Def && Def->CompletionEventTag.MatchesTagExact(EventTag))
		{
			ToComplete.Add(ID);
		}
	}
	bool bAny = false;
	for (const FName& ID : ToComplete)
	{
		bAny |= CompleteObjective(ID);
	}
	if (!bAny)
	{
		UE_LOG(LogNeonVeil, Verbose, TEXT("Event %s matched no active objective"), *EventTag.ToString());
	}
	return bAny;
}

TArray<FNVObjectiveDef> UNVObjectiveSubsystem::GetActiveObjectives() const
{
	TArray<FNVObjectiveDef> Result;
	if (!CurrentMission)
	{
		return Result;
	}
	for (int32 Pass = 0; Pass < 2; ++Pass)
	{
		for (const FNVObjectiveDef& Def : CurrentMission->Objectives)
		{
			if (Active.Contains(Def.ObjectiveID) && Def.bOptional == (Pass == 1))
			{
				Result.Add(Def);
			}
		}
	}
	return Result;
}

void UNVObjectiveSubsystem::CheckMissionComplete()
{
	if (bMissionComplete || !CurrentMission)
	{
		return;
	}
	for (const FNVObjectiveDef& Def : CurrentMission->Objectives)
	{
		if (!Def.bOptional && !Completed.Contains(Def.ObjectiveID))
		{
			return;
		}
	}
	bMissionComplete = true;
	UE_LOG(LogNeonVeil, Log, TEXT("Mission complete: %s"), *CurrentMission->MissionID.ToString());
	OnMissionCompleted.Broadcast(CurrentMission->MissionID);
}
