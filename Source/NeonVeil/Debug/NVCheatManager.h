#pragma once

#include "CoreMinimal.h"
#include "GameFramework/CheatManager.h"
#include "NVCheatManager.generated.h"

class ANVPlayerCharacter;

/**
 * Developer / QA console commands (non-shipping). Every command logs to LogNeonVeil so
 * results can be read back from Saved/Logs/NeonVeil.log.
 */
UCLASS()
class NEONVEIL_API UNVCheatManager : public UCheatManager
{
	GENERATED_BODY()

public:
	/** Point the view at the first actor whose label/name contains Name. WeakPoint=1 aims at its weak point. */
	UFUNCTION(Exec)
	void NVAimAt(const FString& Name, int32 WeakPoint = 0);

	/** Fire N shots at the weapon's own fire rate (semi-auto taps). */
	UFUNCTION(Exec)
	void NVFire(int32 Shots = 1);

	UFUNCTION(Exec)
	void NVReload();

	/** Hold or release aim-down-sights. */
	UFUNCTION(Exec)
	void NVAim(int32 bOn = 1);

	UFUNCTION(Exec)
	void NVEquip(int32 Slot);

	/** Teleport Distance cm from an actor and face it. ApproachYaw >= 0 places you so you face along that world yaw; -1 = from your current side. */
	UFUNCTION(Exec)
	void NVGoTo(const FString& Name, float Distance = 200.f, float ApproachYaw = -1.f);

	/** Start using the focused interactable; Hold seconds before release. */
	UFUNCTION(Exec)
	void NVUse(float Hold = 0.f);

	/** Apply damage to the player (tests health HUD and death rules). */
	UFUNCTION(Exec)
	void NVHurtSelf(float Amount = 10.f);

	/** Log player, weapon, target, objective and timing state. */
	UFUNCTION(Exec)
	void NVReport();

	/** Starts ADS from rest and logs alpha/FOV N times over Seconds (measures the ADS transition). */
	UFUNCTION(Exec)
	void NVSampleAds(float Seconds = 0.4f, int32 Samples = 8);

	/** Hold movement input for Seconds (Forward/Right in -1..1, Sprint 0/1), logging speed every 0.25 s. */
	UFUNCTION(Exec)
	void NVMove(float Forward = 1.f, float Right = 0.f, float Seconds = 1.f, int32 Sprint = 0);

	/** Press jump (vaults if facing a vaultable obstacle). */
	UFUNCTION(Exec)
	void NVJump();

	/** Press (1) or release (0) crouch; while sprinting this starts a slide. */
	UFUNCTION(Exec)
	void NVCrouch(int32 bPressed = 1);

	/** Face a world yaw in degrees. */
	UFUNCTION(Exec)
	void NVFace(float Yaw);

private:
	ANVPlayerCharacter* GetNVPlayer() const;
	AActor* FindActor(const FString& Name) const;
	void FireTick();
	void UseRelease();
	void SampleTick();
	void MoveTick();

	int32 ShotsRemaining = 0;
	FTimerHandle FireTimer;
	FTimerHandle UseTimer;
	FTimerHandle SampleTimer;
	int32 SamplesRemaining = 0;
	float SampleStart = 0.f;
	FTimerHandle MoveTimer;
	float MoveEndTime = 0.f;
};
