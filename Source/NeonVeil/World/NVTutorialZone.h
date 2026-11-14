#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "GameplayTagContainer.h"
#include "NVTutorialZone.generated.h"

class UBoxComponent;

UENUM(BlueprintType)
enum class ENVTutorialAction : uint8
{
	/** Sprint for SprintSeconds (accumulated) while inside. */
	Sprint,
	Jump,
	Crouch,
	Slide,
	Vault,
	/** Just walk through: completes on leaving the far side (or never; the hint clears on exit). */
	None
};

/**
 * Movement tutorial volume (prologue station). While the player is inside it shows a device-aware
 * instruction ("Sprint {Sprint}") and completes when the player performs the action, then shows a short
 * notice and optionally sends an event. The hint also clears when the player walks out without doing it,
 * so nothing ever blocks progress; the geometry around the zone (a low barrier, a half-shut gate) is what
 * invites the move.
 */
UCLASS()
class NEONVEIL_API ANVTutorialZone : public AActor
{
	GENERATED_BODY()

public:
	ANVTutorialZone();

	virtual void Tick(float DeltaSeconds) override;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Tutorial")
	ENVTutorialAction Action = ENVTutorialAction::Sprint;

	/** Shown while inside. Tokens: {Jump} {Sprint} {Crouch} {Interact} ... */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Tutorial", meta = (MultiLine = true))
	FText Instruction;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Tutorial")
	FText CompleteNotice;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Tutorial", meta = (ClampMin = "0.1"))
	float SprintSeconds = 1.5f;

	/** Only teaches while this objective is active (None = always). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Tutorial")
	FName RequiredActiveObjective;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Tutorial")
	FGameplayTag CompleteEventTag;

	UFUNCTION(BlueprintPure, Category = "Tutorial")
	bool IsDone() const { return bDone; }

protected:
	UPROPERTY(VisibleAnywhere, Category = "Components")
	TObjectPtr<UBoxComponent> Volume;

private:
	void SetHint(bool bShow);
	void Complete();

	bool bInside = false;
	bool bDone = false;
	bool bWasGrounded = true;
	float SprintAccum = 0.f;
};
