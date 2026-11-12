#include "Combat/NVMeleeComponent.h"
#include "Combat/NVFriendly.h"
#include "Abilities/NVAbilityComponent.h"
#include "Combat/NVHealthComponent.h"
#include "Combat/NVStaggerable.h"
#include "Core/NVGameplayTags.h"
#include "NeonVeil.h"

#include "Camera/CameraComponent.h"
#include "Engine/World.h"
#include "GameFramework/Controller.h"
#include "GameFramework/Pawn.h"
#include "Kismet/GameplayStatics.h"
#include "TimerManager.h"

UNVMeleeComponent::UNVMeleeComponent()
{
	PrimaryComponentTick.bCanEverTick = false;
}

void UNVMeleeComponent::BeginPlay()
{
	Super::BeginPlay();
	if (!DamageType.IsValid())
	{
		DamageType = NVTags::Damage_Melee;
	}
}

bool UNVMeleeComponent::IsSwinging() const
{
	return GetWorld() && GetWorld()->GetTimeSeconds() - SwingStartTime < SwingTime;
}

float UNVMeleeComponent::GetSwingAlpha() const
{
	if (!GetWorld() || SwingTime <= 0.f)
	{
		return 0.f;
	}
	const float A = (GetWorld()->GetTimeSeconds() - SwingStartTime) / SwingTime;
	return (A >= 0.f && A < 1.f) ? A : 0.f;
}

bool UNVMeleeComponent::Strike()
{
	if (IsSwinging())
	{
		return false;
	}
	SwingStartTime = GetWorld()->GetTimeSeconds();
	if (SwingSound)
	{
		UGameplayStatics::PlaySound2D(this, SwingSound);
	}
	if (UNVAbilityComponent* Abilities = GetOwner()->FindComponentByClass<UNVAbilityComponent>())
	{
		Abilities->NotifyAttacked();
	}
	OnSwing.Broadcast();
	GetWorld()->GetTimerManager().SetTimer(HitTimer, this, &UNVMeleeComponent::ResolveHit, FMath::Max(0.01f, WindUp), false);
	return true;
}

void UNVMeleeComponent::ResolveHit()
{
	const UCameraComponent* Cam = GetOwner()->FindComponentByClass<UCameraComponent>();
	const FVector Start = Cam ? Cam->GetComponentLocation() : GetOwner()->GetActorLocation();
	FVector Dir = GetOwner()->GetActorForwardVector();
	if (const APawn* Pawn = Cast<APawn>(GetOwner()))
	{
		if (const AController* C = Pawn->GetController())
		{
			Dir = C->GetControlRotation().Vector();
		}
	}
	const FVector End = Start + Dir * Range;

	FCollisionQueryParams Params(SCENE_QUERY_STAT(NVMeleeSweep), false, GetOwner());
	{
		FHitResult PawnHit;
		if (GetWorld()->SweepSingleByChannel(PawnHit, Start, End, FQuat::Identity, ECC_Pawn, FCollisionShape::MakeSphere(SweepRadius), Params)
			&& NVFriendly::IsFriendly(PawnHit.GetActor()))
		{
			UE_LOG(LogNeonVeil, Log, TEXT("Baton held: %s is friendly"), *PawnHit.GetActor()->GetName());
			return;
		}
	}
	TArray<FHitResult> Hits;
	GetWorld()->SweepMultiByChannel(Hits, Start, End, FQuat::Identity, ECC_Visibility, FCollisionShape::MakeSphere(SweepRadius), Params);

	for (const FHitResult& Hit : Hits)
	{
		AActor* A = Hit.GetActor();
		UNVHealthComponent* Health = A ? A->FindComponentByClass<UNVHealthComponent>() : nullptr;
		if (!Health || Health->IsDead())
		{
			if (Hit.bBlockingHit)
			{
				UE_LOG(LogNeonVeil, Log, TEXT("Baton strike blocked by %s"), *GetNameSafe(A));
				return; // wall in the way
			}
			continue;
		}
		INVStaggerable* Stag = Cast<INVStaggerable>(A);
		const bool bTakedown = Stag && Stag->IsStaggered() && Stag->CanBeTakenDown();
		const float Applied = Health->ApplyDamage(bTakedown ? TakedownDamage : Damage, GetOwner(), DamageType, false);
		if (!bTakedown && Stag && !Health->IsDead())
		{
			Stag->ApplyStagger(StaggerDuration, GetOwner());
		}
		UE_LOG(LogNeonVeil, Log, TEXT("Baton %s %s: applied %.1f, hp %.1f"), bTakedown ? TEXT("TAKEDOWN on") : TEXT("hit"), *A->GetName(), Applied, Health->GetHealth());
		if (HitSound)
		{
			UGameplayStatics::PlaySound2D(this, HitSound);
		}
		OnMeleeHit.Broadcast(A, bTakedown);
		return;
	}
	UE_LOG(LogNeonVeil, Log, TEXT("Baton swing hit nothing"));
}
