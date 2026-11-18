#include "AI/NVEnemyController.h"
#include "AI/NVGuardCharacter.h"
#include "AI/NVHostileFire.h"
#include "Combat/NVHealthComponent.h"
#include "UI/NVHUD.h"
#include "EngineUtils.h"
#include "NavigationSystem.h"
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
	LastThinkTime = GetWorld()->GetTimeSeconds();
	if (UNVHealthComponent* H = Guard->GetHealth())
	{
		H->OnHealthChanged.AddUniqueDynamic(this, &ANVEnemyController::HandleDamaged);
	}
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
	StateEnteredTime = GetWorld() ? GetWorld()->GetTimeSeconds() : 0.f;
}

void ANVEnemyController::Think()
{
	ANVGuardCharacter* G = Guard.Get();
	if (!G || State == ENVAIState::Disabled)
	{
		return;
	}
	const float Now = GetWorld()->GetTimeSeconds();
	const float Interval = FMath::Max(0.05f, Now - LastThinkTime);
	LastThinkTime = Now;
	if (G->IsHostile() && ThinkHostile(Interval))
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
	if (G && State == ENVAIState::Combat)
	{
		TickCombat(DeltaSeconds);
	}
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

// ---------------------------------------------------------------------------------------------- hostile (M01+)

bool ANVEnemyController::SeesPlayer(APawn* Player) const
{
	const ANVGuardCharacter* G = Guard.Get();
	if (!G || !Player)
	{
		return false;
	}
	const FVector Eye = G->GetActorLocation() + FVector(0.f, 0.f, 60.f);
	const FVector To = Player->GetActorLocation() - Eye;
	if (To.SizeSquared() > FMath::Square(G->SightRange))
	{
		return false;
	}
	// in combat they track all round; on patrol only inside the cone (or very close)
	const bool bClose = To.SizeSquared() < FMath::Square(250.f);
	if (State != ENVAIState::Combat && !bClose
		&& FVector::DotProduct(G->GetActorForwardVector(), To.GetSafeNormal()) < FMath::Cos(FMath::DegreesToRadians(G->SightHalfAngle)))
	{
		return false;
	}
	return UNVHostileFire::CanSee(GetWorld(), G, Eye, Player);
}

void ANVEnemyController::SetCombatMovement(bool bCombat)
{
	ANVGuardCharacter* G = Guard.Get();
	if (!G || bCombatMovement == bCombat)
	{
		return;
	}
	bCombatMovement = bCombat;
	UCharacterMovementComponent* M = G->GetCharacterMovement();
	M->MaxWalkSpeed = bCombat ? G->RunSpeed : G->WalkSpeed;
	M->MaxAcceleration = bCombat ? 1400.f : 380.f;
	M->bOrientRotationToMovement = !bCombat;
	M->bUseControllerDesiredRotation = bCombat;
	M->RotationRate = FRotator(0.f, bCombat ? 360.f : 150.f, 0.f);
}

void ANVEnemyController::AlertTo(const FVector& Where)
{
	const ANVGuardCharacter* G = Guard.Get();
	if (G && G->IsHostile() && State != ENVAIState::Disabled && State != ENVAIState::Combat)
	{
		EnterCombat(Where, false);
	}
}

void ANVEnemyController::EnterCombat(const FVector& Where, bool bAlertAllies)
{
	ANVGuardCharacter* G = Guard.Get();
	if (!G)
	{
		return;
	}
	LastKnown = Where;
	LastSeenTime = GetWorld()->GetTimeSeconds();   // treat the alert as a fresh sighting
	bGlancing = false;
	bDirectMove = false;
	StopMovement();
	bMoving = false;
	SetCombatMovement(true);
	SetAIState(ENVAIState::Combat);
	FireTimer = FMath::FRandRange(0.35f, 0.8f);   // reaction time before the first burst
	ShotsLeft = 0;
	NextReposition = GetWorld()->GetTimeSeconds() + FMath::FRandRange(2.f, 4.f);
	if (APawn* P = GetWorld()->GetFirstPlayerController() ? GetWorld()->GetFirstPlayerController()->GetPawn() : nullptr)
	{
		SetFocus(P, EAIFocusPriority::Gameplay);
	}
	if (bAlertAllies)
	{
		// shout: hostile troopers within earshot join in
		for (TActorIterator<ANVGuardCharacter> It(GetWorld()); It; ++It)
		{
			if (*It != G && It->IsHostile() && FVector::DistSquared(It->GetActorLocation(), G->GetActorLocation()) < FMath::Square(1800.f))
			{
				if (ANVEnemyController* C = Cast<ANVEnemyController>(It->GetController()))
				{
					C->AlertTo(Where);
				}
			}
		}
	}
}

void ANVEnemyController::HandleDamaged(UNVHealthComponent* HealthComp, float NewHealth, float Delta, AActor* DamageInstigator, FGameplayTag DamageType)
{
	ANVGuardCharacter* G = Guard.Get();
	if (!G || Delta >= 0.f || NewHealth <= 0.f || !DamageInstigator)
	{
		return;
	}
	if (!G->IsHostile())
	{
		return;   // M00 citizens are never shot at (weapon refuses), but don't turn them on a stray hit either
	}
	if (State != ENVAIState::Combat)
	{
		EnterCombat(DamageInstigator->GetActorLocation(), true);
	}
	LastKnown = DamageInstigator->GetActorLocation();
}

bool ANVEnemyController::ThinkHostile(float Interval)
{
	ANVGuardCharacter* G = Guard.Get();
	const APlayerController* PC = GetWorld()->GetFirstPlayerController();
	APawn* Player = PC ? PC->GetPawn() : nullptr;
	const float Now = GetWorld()->GetTimeSeconds();
	const bool bSees = SeesPlayer(Player);
	if (bSees)
	{
		LastKnown = Player->GetActorLocation();
		LastSeenTime = Now;
	}

	if (State == ENVAIState::Combat)
	{
		// lost him for a while: go and look where he was
		if (Now - LastSeenTime > 4.f)
		{
			SetAIState(ENVAIState::Search);
			ClearFocus(EAIFocusPriority::Gameplay);
			MoveToLocation(LastKnown, 120.f, true, true, true, false);
			bMoving = true;
		}
		else if (!bSees && Now - LastSeenTime > 1.f && !bMoving)
		{
			// push toward his last position to regain sight
			MoveToLocation(LastKnown, 300.f, true, true, true, false);
			bMoving = true;
		}
		else if (bSees && Now >= NextReposition)
		{
			// sidestep to a nearby point so he isn't a statue
			FNavLocation Out;
			UNavigationSystemV1* Nav = FNavigationSystem::GetCurrent<UNavigationSystemV1>(GetWorld());
			const FVector Side = FVector::CrossProduct((LastKnown - G->GetActorLocation()).GetSafeNormal2D(), FVector::UpVector) * (FMath::RandBool() ? 1.f : -1.f);
			if (Nav && Nav->ProjectPointToNavigation(G->GetActorLocation() + Side * FMath::FRandRange(200.f, 380.f), Out, FVector(150.f, 150.f, 200.f)))
			{
				MoveToLocation(Out.Location, 40.f, false, true, true, false);
				bMoving = true;
			}
			NextReposition = Now + FMath::FRandRange(2.5f, 4.5f);
		}
		return true;
	}

	if (State == ENVAIState::Search)
	{
		if (bSees)
		{
			EnterCombat(LastKnown, true);
		}
		else if (Now - StateEnteredTime > 9.f)
		{
			SetCombatMovement(false);
			Suspicion = 0.35f;
			SetAIState(G->GetWorldPatrol().Num() > 1 ? ENVAIState::Patrol : ENVAIState::Idle);
			bMoving = false;
			WaitUntil = Now + 1.f;
		}
		return true;
	}

	// patrol / idle: build suspicion while he is in view, faster when close
	if (bSees)
	{
		const float D = FVector::Dist(Player->GetActorLocation(), G->GetActorLocation());
		const float Rate = FMath::GetMappedRangeValueClamped(FVector2D(300.f, G->SightRange), FVector2D(3.f, 0.6f), D) / FMath::Max(0.2f, G->SpotTime);
		Suspicion = FMath::Min(1.f, Suspicion + Interval * Rate);
		if (State != ENVAIState::Suspicious)
		{
			SetAIState(ENVAIState::Suspicious);
			if (bMoving && !bDirectMove)
			{
				PauseMove(GetCurrentMoveRequestID());
			}
			G->GetCharacterMovement()->bOrientRotationToMovement = false;
			G->GetCharacterMovement()->bUseControllerDesiredRotation = true;
			SetFocus(Player, EAIFocusPriority::Gameplay);
		}
		if (Suspicion >= 1.f)
		{
			EnterCombat(LastKnown, true);
			return true;
		}
	}
	else
	{
		Suspicion = FMath::Max(0.f, Suspicion - Interval * 0.25f);
		if (State == ENVAIState::Suspicious && Suspicion <= 0.05f)
		{
			ClearFocus(EAIFocusPriority::Gameplay);
			G->GetCharacterMovement()->bUseControllerDesiredRotation = false;
			G->GetCharacterMovement()->bOrientRotationToMovement = true;
			SetAIState(G->GetWorldPatrol().Num() > 1 ? ENVAIState::Patrol : ENVAIState::Idle);
			if (bMoving && !bDirectMove)
			{
				ResumeMove(GetCurrentMoveRequestID());
			}
		}
	}
	if (APlayerController* PCm = GetWorld()->GetFirstPlayerController())
	{
		if (ANVHUD* HUD = Cast<ANVHUD>(PCm->GetHUD()))
		{
			if (Suspicion > 0.02f)
			{
				HUD->SetDetection(Suspicion);
			}
		}
	}
	if (State == ENVAIState::Suspicious)
	{
		return true;   // hold and stare while deciding
	}
	if (State == ENVAIState::Patrol && !bMoving && !bDirectMove && Now >= WaitUntil)
	{
		MoveToNextPoint();
	}
	return true;
}

void ANVEnemyController::TickCombat(float DeltaSeconds)
{
	ANVGuardCharacter* G = Guard.Get();
	APlayerController* PC = GetWorld()->GetFirstPlayerController();
	APawn* Player = PC ? PC->GetPawn() : nullptr;
	if (!G || !Player || !G->GetGun())
	{
		return;
	}
	FireTimer -= DeltaSeconds;
	if (FireTimer > 0.f)
	{
		return;
	}
	const float Now = GetWorld()->GetTimeSeconds();
	// only fire with a current sighting, facing roughly the right way
	const FVector To = (Player->GetActorLocation() - G->GetActorLocation()).GetSafeNormal2D();
	if (Now - LastSeenTime > 0.3f || FVector::DotProduct(G->GetActorForwardVector(), To) < 0.85f)
	{
		FireTimer = 0.1f;
		return;
	}
	if (ShotsLeft <= 0)
	{
		ShotsLeft = G->BurstShots;
	}
	G->GetGun()->Fire(Player, UNVHostileFire::AimPointOn(Player));
	--ShotsLeft;
	FireTimer = ShotsLeft > 0 ? 0.13f : FMath::FRandRange(G->BurstPause.X, G->BurstPause.Y);
}
