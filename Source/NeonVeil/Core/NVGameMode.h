#pragma once

#include "CoreMinimal.h"
#include "GameFramework/GameModeBase.h"
#include "NVGameMode.generated.h"

class UNVMissionData;

/**
 * Single-player mission game mode. Starts (or restores) the level's mission, picks the
 * checkpoint spawn on loads, plays the end-of-mission beat and travels to the next map once (QA-02).
 */
UCLASS()
class NEONVEIL_API ANVGameMode : public AGameModeBase
{
	GENERATED_BODY()

public:
	ANVGameMode();

	virtual void StartPlay() override;
	virtual AActor* ChoosePlayerStart_Implementation(AController* Player) override;

	/** Mission this map runs. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "NeonVeil")
	TObjectPtr<UNVMissionData> Mission;

	/** Seconds between mission completion and the map change (lets the end beat play). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "NeonVeil")
	float TransitionDelay = 6.f;

	/** Seconds of fade to black after the final objective (0 = no fade). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "NeonVeil")
	float EndFadeTime = 2.5f;

	/** Off for seamless hand-offs (the prologue tram ride into M00): fade and travel, no end card. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "NeonVeil")
	bool bShowEndCard = true;

	/** Load the next mission's map in the background during this one (seamless hand-off; not in PIE). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "NeonVeil")
	bool bPreloadNextMap = false;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "NeonVeil")
	FText EndCardTitle;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "NeonVeil")
	FText EndCardSubtitle;

protected:
	UFUNCTION()
	void HandleMissionCompleted(FName MissionID);

	UFUNCTION(BlueprintImplementableEvent, Category = "NeonVeil")
	void BP_OnMissionCompleted(FName MissionID);

	void ShowEndCard();
	void TravelToNextMission();

private:
	bool bTransitionStarted = false;
	FTimerHandle EndCardTimer;
	FTimerHandle TransitionTimer;
};
