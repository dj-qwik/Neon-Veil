#pragma once

#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "NVSaveSubsystem.generated.h"

class UNVSaveGame;
class ANVCheckpoint;

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FNVOnCheckpointSaved, FName, CheckpointID);

/**
 * Writes checkpoint saves when the objective subsystem asks for one, and reloads them.
 * A load reopens the saved map; ANVGameMode consumes the pending save while the map starts.
 */
UCLASS()
class NEONVEIL_API UNVSaveSubsystem : public UGameInstanceSubsystem
{
	GENERATED_BODY()

public:
	static UNVSaveSubsystem* Get(const UObject* WorldContext);

	virtual void Initialize(FSubsystemCollectionBase& Collection) override;

	/** Save at a checkpoint actor's ID. Returns false if nothing could be saved. */
	UFUNCTION(BlueprintCallable, Category = "NeonVeil|Save")
	bool SaveCheckpoint(FName CheckpointID);

	/** Reopen the map from the last checkpoint. */
	UFUNCTION(BlueprintCallable, Category = "NeonVeil|Save")
	bool LoadCheckpoint();

	/** Delete the checkpoint and restart the given map fresh. */
	UFUNCTION(BlueprintCallable, Category = "NeonVeil|Save")
	void NewGame(const FString& MapPackage);

	UFUNCTION(BlueprintPure, Category = "NeonVeil|Save")
	bool HasCheckpoint() const;

	/** Valid only while a map is starting from a load. */
	UNVSaveGame* GetPendingRestore() const { return PendingRestore; }
	void FinishRestore();

	UPROPERTY(BlueprintAssignable, Category = "NeonVeil|Save")
	FNVOnCheckpointSaved OnCheckpointSaved;

	static const FString SlotName;

private:
	UFUNCTION()
	void HandleCheckpointRequested(FName ReasonObjectiveID);

	UPROPERTY(Transient)
	TObjectPtr<UNVSaveGame> PendingRestore;

	double LoadRequestTime = 0.0;
};
