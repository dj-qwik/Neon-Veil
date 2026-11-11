#pragma once

#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "GameplayTagContainer.h"
#include "Objectives/NVObjectiveData.h"
#include "NVObjectiveSubsystem.generated.h"

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FNVOnObjectiveEvent, FName, ObjectiveID);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FNVOnMissionEvent, FName, MissionID);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FNVOnCheckpointRequested, FName, ReasonObjectiveID);

/**
 * Objective state and mission progression. Interactables and triggers send gameplay tags;
 * this validates prerequisites, records completion, activates the next objectives and requests saves.
 */
UCLASS()
class NEONVEIL_API UNVObjectiveSubsystem : public UGameInstanceSubsystem
{
	GENERATED_BODY()

public:
	static UNVObjectiveSubsystem* Get(const UObject* WorldContext);

	UFUNCTION(BlueprintCallable, Category = "NeonVeil|Objectives")
	void StartMission(UNVMissionData* Mission);

	/** Completes every active objective whose CompletionEventTag matches. Returns true if any completed. */
	UFUNCTION(BlueprintCallable, Category = "NeonVeil|Objectives")
	bool SendEvent(FGameplayTag EventTag);

	/** Direct completion by ID (debug and scripted sequences). Ignores the call if prerequisites are unmet. */
	UFUNCTION(BlueprintCallable, Category = "NeonVeil|Objectives")
	bool CompleteObjective(FName ObjectiveID);

	UFUNCTION(BlueprintPure, Category = "NeonVeil|Objectives")
	bool IsObjectiveComplete(FName ObjectiveID) const { return Completed.Contains(ObjectiveID); }

	UFUNCTION(BlueprintPure, Category = "NeonVeil|Objectives")
	bool IsObjectiveActive(FName ObjectiveID) const;

	/** Active required objectives first, then optional. */
	UFUNCTION(BlueprintPure, Category = "NeonVeil|Objectives")
	TArray<FNVObjectiveDef> GetActiveObjectives() const;

	UFUNCTION(BlueprintPure, Category = "NeonVeil|Objectives")
	bool IsMissionComplete() const { return bMissionComplete; }

	UFUNCTION(BlueprintPure, Category = "NeonVeil|Objectives")
	UNVMissionData* GetCurrentMission() const { return CurrentMission; }

	/** Save/restore support. */
	const TSet<FName>& GetCompletedSet() const { return Completed; }
	void RestoreState(UNVMissionData* Mission, const TArray<FName>& CompletedIDs);

	UPROPERTY(BlueprintAssignable, Category = "NeonVeil|Objectives")
	FNVOnObjectiveEvent OnObjectiveActivated;

	UPROPERTY(BlueprintAssignable, Category = "NeonVeil|Objectives")
	FNVOnObjectiveEvent OnObjectiveCompleted;

	UPROPERTY(BlueprintAssignable, Category = "NeonVeil|Objectives")
	FNVOnMissionEvent OnMissionCompleted;

	UPROPERTY(BlueprintAssignable, Category = "NeonVeil|Objectives")
	FNVOnCheckpointRequested OnCheckpointRequested;

private:
	bool ArePrerequisitesMet(const FNVObjectiveDef& Def) const;
	void RefreshActive(bool bBroadcast);
	void CheckMissionComplete();

	UPROPERTY(Transient)
	TObjectPtr<UNVMissionData> CurrentMission;

	TSet<FName> Completed;
	TSet<FName> Active;
	bool bMissionComplete = false;
};
