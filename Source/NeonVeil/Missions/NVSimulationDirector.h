#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "GameplayTagContainer.h"
#include "UI/NVSubtitleLine.h"
#include "NVSimulationDirector.generated.h"

class UBoxComponent;
class ANVTrainingTarget;
class ANVSimVolleyEmitter;
class ANVSurveillanceCamera;
class ANVPlayerCharacter;
class UNVHealthComponent;
class USoundBase;
class UAudioComponent;
class AAmbientSound;

UENUM(BlueprintType)
enum class ENVSimStepType : uint8
{
	/** Wait until every listed target is cleared. */
	ClearTargets,
	/** Wait until the player has aimed down sights for Duration seconds in total. */
	HoldAim,
	/** Wait until the player has switched to the weapon in slot WeaponSlot. */
	EquipWeapon,
	/** Pause for Duration seconds (lets lines play). */
	Wait,
	/**
	 * Survive a scripted volley without losing health (cover drill, shield-burst drill). Starts when
	 * the player stands in Area; leaving Area or taking health damage fails and restarts the step.
	 */
	Volley,
	/** Mark at least MinMarks of Targets with the drone uplink. */
	MarkTargets,
	/** Wait for EventTag (e.g. a terminal). Cameras are live; detection resets the player to ResetPoint. */
	WaitForEvent
};

USTRUCT(BlueprintType)
struct FNVSimStep
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Step")
	ENVSimStepType Type = ENVSimStepType::ClearTargets;

	/** On-screen instruction while the step is active, e.g. "Neutralise the moving targets". */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Step")
	FText Instruction;

	/** Played when the step starts. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Step")
	TArray<FNVSubtitleLine> Lines;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Step")
	TArray<TObjectPtr<ANVTrainingTarget>> Targets;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Step")
	float Duration = 1.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Step")
	int32 WeaponSlot = 0;

	// --- Volley
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Step|Volley")
	TObjectPtr<ANVSimVolleyEmitter> Emitter;

	/** Player must stand inside this actor's bounds (a trigger box) for the volley to start. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Step|Volley")
	TObjectPtr<AActor> Area;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Step|Volley")
	float WarmupSeconds = 1.5f;

	/** Telegraph text near the reticle during warm-up, e.g. "Incoming volley". */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Step|Volley")
	FText WarningText;

	// --- Mark
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Step|Mark")
	int32 MinMarks = 1;

	// --- Event / stealth
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Step|Event")
	FGameplayTag EventTag;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Step|Event")
	TArray<TObjectPtr<ANVSurveillanceCamera>> Cameras;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Step|Event")
	TObjectPtr<AActor> ResetPoint;

	/** Played when the step fails (hit during a volley, seen by a camera). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Step")
	TArray<FNVSubtitleLine> FailLines;
};

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FNVOnSimStep, int32, StepIndex);

/**
 * Runs the combat simulation (M00-O02) as an ordered list of steps. Starts when its objective is
 * active and the player enters the start volume; sends CompletionTag when the last step ends.
 * Later steps (cover, melee, gadget, shield burst) are added in Milestone 3 as new step types.
 */
UCLASS()
class NEONVEIL_API ANVSimulationDirector : public AActor
{
	GENERATED_BODY()

public:
	ANVSimulationDirector();

	virtual void Tick(float DeltaSeconds) override;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Simulation")
	FName ObjectiveID = TEXT("M00-O02");

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Simulation")
	FGameplayTag CompletionTag;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Simulation")
	TArray<FNVSimStep> Steps;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Simulation")
	TArray<FNVSubtitleLine> LinesOnComplete;

	/** Combat-state score layer: 2D, fades in when the run starts and out when it finishes. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Simulation|Music")
	TObjectPtr<USoundBase> SimMusic;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Simulation|Music", meta = (ClampMin = "0"))
	float SimMusicVolume = 0.22f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Simulation|Music", meta = (ClampMin = "0"))
	float SimMusicFadeIn = 3.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Simulation|Music", meta = (ClampMin = "0"))
	float SimMusicFadeOut = 6.f;

	/** Explore bed to duck while the combat layer plays (restored on finish). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Simulation|Music")
	TObjectPtr<AAmbientSound> MusicToDuck;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Simulation|Music", meta = (ClampMin = "0", ClampMax = "1"))
	float DuckLevel = 0.15f;

	UFUNCTION(BlueprintPure, Category = "NeonVeil")
	int32 GetCurrentStep() const { return CurrentStep; }

	UFUNCTION(BlueprintPure, Category = "NeonVeil")
	FText GetCurrentInstruction() const;

	UPROPERTY(BlueprintAssignable, Category = "NeonVeil")
	FNVOnSimStep OnStepStarted;

	/** QA: complete the current step immediately. */
	void DebugSkipStep();

protected:
	virtual void BeginPlay() override;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	TObjectPtr<UBoxComponent> StartVolume;

private:
	UFUNCTION()
	void HandleStartOverlap(UPrimitiveComponent* OverlappedComp, AActor* Other, UPrimitiveComponent* OtherComp, int32 BodyIndex, bool bFromSweep, const FHitResult& Sweep);

	UFUNCTION()
	void HandleTargetCleared(ANVTrainingTarget* Target);

	UFUNCTION()
	void HandlePlayerHealthChanged(UNVHealthComponent* HealthComp, float NewHealth, float Delta, AActor* InstigatorActor, FGameplayTag DamageType);

	UFUNCTION()
	void HandleVolleyFinished();

	UFUNCTION()
	void HandleGameplayEvent(FGameplayTag EventTag);

	UFUNCTION()
	void HandleCameraDetected(AActor* Detected);

	ANVPlayerCharacter* GetPlayer() const;
	void TickVolley(const FNVSimStep& Step, float DeltaSeconds);
	void FailStep(const TCHAR* Why);
	void EndStepSideEffects(FNVSimStep& Step);
	class ANVHUD* GetHUD() const;

	void BeginRun();
	void StartStep(int32 Index);
	void CompleteStep();
	void Finish();
	bool IsStepDone(const FNVSimStep& Step) const;

	void StartSimMusic();
	void StopSimMusic();

	UPROPERTY(Transient)
	TObjectPtr<UAudioComponent> SimMusicComp;

	enum class EVolleyState : uint8 { WaitArea, Running, Passed, Retry };
	EVolleyState VolleyState = EVolleyState::WaitArea;
	bool bVolleyHit = false;
	float RetryTimer = 0.f;
	bool bEventReceived = false;

	int32 CurrentStep = INDEX_NONE;
	float StepTimer = 0.f;
	bool bRunning = false;
	bool bFinished = false;
};
