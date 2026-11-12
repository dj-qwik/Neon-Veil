#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "GameplayTagContainer.h"
#include "UI/NVSubtitleLine.h"
#include "NVSimulationDirector.generated.h"

class UBoxComponent;
class ANVTrainingTarget;

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
	Wait
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

	void BeginRun();
	void StartStep(int32 Index);
	void CompleteStep();
	void Finish();
	bool IsStepDone(const FNVSimStep& Step) const;

	int32 CurrentStep = INDEX_NONE;
	float StepTimer = 0.f;
	bool bRunning = false;
	bool bFinished = false;
};
