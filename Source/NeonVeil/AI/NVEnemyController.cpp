#include "AI/NVEnemyController.h"
#include "AI/NVGuardCharacter.h"
#include "Abilities/NVAbilityComponent.h"
#include "NeonVeil.h"

#include "Engine/World.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/PlayerController.h"
#include "Navigation/PathFollowingComponent.h"
#include "TimerManager.h"

ANVEnemyController::ANVEnemyController()
{
	PrimaryActorTick.bCanEverTick = true;
	bSetControlRotationFromPawnOrientation = true;
}

void ANVEnemyController::OnPossess(APawn* InPawn)
{
	Super::OnPossess(InPawn);
	Guard = Cast<ANVGuardCharacter>(InPawn);
	if (!Guard.IsValid())
	{
		return;
	}
	SetAIState(Guard->GetWorldPatrol().Num() > 1 ? ENVAIState::Patrol : ENVAIState::Idle);
	// Bible §8 decision cadence: 0.25-0.5 s, jittered so guards don't think in lockstep.
	const float Interval = FMath::FRandRange(0.25f, 0.5f);
	GetWorldTimerManager().SetTimer(ThinkTimer, this, &ANVEnemyController::Think, Interval, true, FMath::FRandRange(0.f, Interval));
	WaitUntil = GetWorld()->GetTimeSeconds() + FMath::FRandRange(0.5f, 2.f);
}

void ANVEnemyController::OnUnPossess()
{
	GetWorldTimerManager().ClearTimer(ThinkTimer);
	Super::OnUnPossess();
}

void ANVEnemyController::SetAIState(ENVAIState NewState)
{
	if (State == NewState)
	{
		return;
	}
	UE_LOG(LogNeonVeil, Log, TEXT("%s: %s -> %s"), *GetNameSafe(GetPawn()), *UEnum::GetValueAsString(State), *UEnum::GetValueAsString(NewState));
	State = NewState;
}

void ANVEnemyController::Think()
{
	ANVGuardCharacter* G = Guard.Get();
	if (!G || State == ENVAIState::Disabled)
	{
		return;
	}
	if (State == ENVAIState::Idle && G->GetWorldPatrol().Num() > 1)
	{
		SetAIState(ENVAIState::Patrol);
	}
	UpdateGlance();
	if (State == ENVAIState::Patrol && !bMoving && !bGlancing && GetWorld()->GetTimeSeconds() >= WaitUntil)
	{
		MoveToNextPoint();
	}
}

void ANVEnemyController::MoveToNextPoint()
{
	ANVGuardCharacter* G = Guard.Get();
	const TArray<FVector>& Route = G->GetWorldPatrol();
	if (Route.Num() == 0)
	{
		return;
	}
	PatrolIndex = (PatrolIndex + 1) % Route.Num();
	const FVector Dest = Route[PatrolIndex];
	bMoving = true;
	const EPathFollowingRequestResult::Type R = MoveToLocation(Dest, 30.f, false, true, true, false); // arrive at the point, not at first overlap
	UE_LOG(LogNeonVeil, Verbose, TEXT("%s move to point %d %s: request %d"), *G->GetName(), PatrolIndex, *Dest.ToCompactString(), int32(R));
	if (R == EPathFollowingRequestResult::Failed)
	{
		// No navmesh here (or an unreachable point): walk straight. Routes are authored in the open.
		bDirectMove = true;
		DirectTarget = Dest;
	}
	else if (R == EPathFollowingRequestResult::AlreadyAtGoal)
	{
		bMoving = false;
		WaitUntil = GetWorld()->GetTimeSeconds() + FMath::FRandRange(G->WaitTimeRange.X, G->WaitTimeRange.Y);
	}
}

void ANVEnemyController::OnMoveCompleted(FAIRequestID RequestID, const FPathFollowingResult& Result)
{
	Super::OnMoveCompleted(RequestID, Result);
	if (const ANVGuardCharacter* G = Guard.Get())
	{
		UE_LOG(LogNeonVeil, Verbose, TEXT("%s move finished: %s at %s"), *G->GetName(), *Result.ToString(), *G->GetActorLocation().ToCompactString());
		bMoving = false;
		WaitUntil = GetWorld()->GetTimeSeconds() + FMath::FRandRange(G->WaitTimeRange.X, G->WaitTimeRange.Y);
	}
}

void ANVEnemyController::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	ANVGuardCharacter* G = Guard.Get();
	if (!G || !bDirectMove)
	{
		return;
	}
	if (bGlancing)
	{
		return; // hold position while acknowledging the player
	}
	FVector To = DirectTarget - G->GetActorLocation();
	To.Z = 0.f;
	if (To.SizeSquared() < FMath::Square(40.f))
	{
		bDirectMove = false;
		bMoving = false;
		WaitUntil = GetWorld()->GetTimeSeconds() + FMath::FRandRange(G->WaitTimeRange.X, G->WaitTimeRange.Y);
		return;
	}
	G->AddMovementInput(To.GetSafeNormal(), 1.f);
}

void ANVEnemyController::UpdateGlance()
{
	ANVGuardCharacter* G = Guard.Get();
	const APlayerController* PC = GetWorld()->GetFirstPlayerController();
	APawn* Player = PC ? PC->GetPawn() : nullptr;
	const float Now = GetWorld()->GetTimeSeconds();

	if (bGlancing)
	{
		if (Now >= GlanceUntil || !Player)
		{
			bGlancing = false;
			ClearFocus(EAIFocusPriority::Gameplay);
			G->GetCharacterMovement()->bUseControllerDesiredRotation = false;
			G->GetCharacterMovement()->bOrientRotationToMovement = true;
			NextGlanceAllowed = Now + 6.f;
			if (bMoving && !bDirectMove)
			{
				ResumeMove(GetCurrentMoveRequestID());
			}
		}
		return;
	}
	if (!Player || Now < NextGlanceAllowed || UNVAbilityComponent::IsActorCloaked(Player))
	{
		return;
	}
	if (FVector::DistSquared(Player->GetActorLocation(), G->GetActorLocation()) > FMath::Square(G->GlanceRadius) || !LineOfSightTo(Player))
	{
		return;
	}
	// Acknowledge Ghost-7: stop, turn to face him for a moment, carry on.
	bGlancing = true;
	GlanceUntil = Now + FMath::FRandRange(1.8f, 2.8f);
	if (bMoving && !bDirectMove)
	{
		PauseMove(GetCurrentMoveRequestID());
	}
	G->GetCharacterMovement()->bOrientRotationToMovement = false;
	G->GetCharacterMovement()->bUseControllerDesiredRotation = true;
	SetFocus(Player, EAIFocusPriority::Gameplay);
	UE_LOG(LogNeonVeil, Log, TEXT("%s acknowledges the player"), *G->GetName());
}
