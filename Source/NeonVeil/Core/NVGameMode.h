#pragma once

#include "CoreMinimal.h"
#include "GameFramework/GameModeBase.h"
#include "NVGameMode.generated.h"

class UNVMissionData;

/**
 * Single-player mission game mode. Starts the level's mission on BeginPlay and
 * handles the one-time transition to the next mission map (QA-02).
 */
UCLASS()
class NEONVEIL_API ANVGameMode : public AGameModeBase
{
	GENERATED_BODY()

public:
	ANVGameMode();

	virtual void StartPlay() override;

	/** Mission this map runs. Set per level through World Settings > GameMode override or a BP child. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "NeonVeil")
	TObjectPtr<UNVMissionData> Mission;

	/** Seconds between mission completion and the map change (lets the end beat play). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "NeonVeil")
	float TransitionDelay = 4.f;

protected:
	UFUNCTION()
	void HandleMissionCompleted(FName MissionID);

	UFUNCTION(BlueprintImplementableEvent, Category = "NeonVeil")
	void BP_OnMissionCompleted(FName MissionID);

	void TravelToNextMission();

private:
	bool bTransitionStarted = false;
	FTimerHandle TransitionTimer;
};
