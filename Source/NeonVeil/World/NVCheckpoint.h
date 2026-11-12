#pragma once

#include "CoreMinimal.h"
#include "GameFramework/PlayerStart.h"
#include "NVCheckpoint.generated.h"

/**
 * Respawn point for checkpoint loads. Placed where the player should stand after loading,
 * in a camera-safe spot. Saved when the objective named ObjectiveID requests a checkpoint.
 */
UCLASS()
class NEONVEIL_API ANVCheckpoint : public APlayerStart
{
	GENERATED_BODY()

public:
	ANVCheckpoint(const FObjectInitializer& ObjectInitializer);

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "NeonVeil")
	FName CheckpointID;

	/** Objective whose checkpoint request saves here (e.g. M00-O01). */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "NeonVeil")
	FName ObjectiveID;
};
