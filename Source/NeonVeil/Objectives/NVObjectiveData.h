#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "GameplayTagContainer.h"
#include "NVObjectiveData.generated.h"

UENUM(BlueprintType)
enum class ENVCheckpointPolicy : uint8
{
	None,
	/** Save when this objective completes. */
	OnComplete,
	/** Save when this objective becomes active. */
	OnActivate
};

/** One objective, following the Bible §11 event contract. */
USTRUCT(BlueprintType)
struct FNVObjectiveDef
{
	GENERATED_BODY()

	/** e.g. M00-O01 */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Objective")
	FName ObjectiveID;

	/** Player-facing text, e.g. "Report to Directorate security". */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Objective")
	FText DisplayText;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Objective")
	TArray<FName> Prerequisites;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Objective")
	FGameplayTag CompletionEventTag;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Objective")
	bool bOptional = false;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Objective")
	ENVCheckpointPolicy CheckpointPolicy = ENVCheckpointPolicy::OnComplete;
};

/** A mission: ordered objectives plus identity. One per M00, M01, M02. */
UCLASS(BlueprintType)
class NEONVEIL_API UNVMissionData : public UPrimaryDataAsset
{
	GENERATED_BODY()

public:
	virtual FPrimaryAssetId GetPrimaryAssetId() const override { return FPrimaryAssetId(TEXT("NVMission"), GetFName()); }

	/** e.g. M00 */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Mission")
	FName MissionID;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Mission")
	FText MissionTitle;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Mission")
	TArray<FNVObjectiveDef> Objectives;

	/** Map to open when the final required objective completes. Empty = stay. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Mission")
	TSoftObjectPtr<UWorld> NextMissionMap;

	const FNVObjectiveDef* FindObjective(FName ID) const
	{
		return Objectives.FindByPredicate([ID](const FNVObjectiveDef& O) { return O.ObjectiveID == ID; });
	}
};
