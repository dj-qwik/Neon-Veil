#pragma once

#include "CoreMinimal.h"
#include "AIController.h"
#include "NVEnemyController.generated.h"

class ANVGuardCharacter;

/** Bible §8 behaviour states. M00 uses Idle and Patrol; M01 adds the hostile states. */
UENUM(BlueprintType)
enum class ENVAIState : uint8
{
	Idle,
	Patrol,
	Suspicious,
	Investigate,
	Alert,
	Combat,
	Search,
	Retreat,
	Disabled
};

/**
 * Sensing and tactical decisions for agency guards (Bible §11: ANVEnemyController).
 * Decisions run on a 0.25-0.5 s cadence with random jitter (Bible §8), not every frame.
 * M00 behaviour: patrol a route with pauses and turn to acknowledge the player when close.
 * Uses the navmesh when present; walks straight to the next point when it isn't.
 */
UCLASS()
class NEONVEIL_API ANVEnemyController : public AAIController
{
	GENERATED_BODY()

public:
	ANVEnemyController();

	virtual void OnPossess(APawn* InPawn) override;
	virtual void OnUnPossess() override;
	virtual void OnMoveCompleted(FAIRequestID RequestID, const FPathFollowingResult& Result) override;

	UFUNCTION(BlueprintPure, Category = "NeonVeil|AI")
	ENVAIState GetAIState() const { return State; }

	UFUNCTION(BlueprintCallable, Category = "NeonVeil|AI")
	void SetAIState(ENVAIState NewState);

protected:
	virtual void Tick(float DeltaSeconds) override;

private:
	void Think();
	void MoveToNextPoint();
	void UpdateGlance();

	TWeakObjectPtr<ANVGuardCharacter> Guard;
	ENVAIState State = ENVAIState::Idle;
	FTimerHandle ThinkTimer;
	int32 PatrolIndex = 0;
	float WaitUntil = 0.f;
	bool bMoving = false;
	bool bDirectMove = false;
	FVector DirectTarget = FVector::ZeroVector;
	float GlanceUntil = 0.f;
	bool bGlancing = false;
	float NextGlanceAllowed = 0.f;
};
