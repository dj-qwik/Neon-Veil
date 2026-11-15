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

	GunBash.Damage = 22.f;
	GunBash.Range = 165.f;
	GunBash.SweepRadius = 28.f;
	GunBash.WindUp = 0.1f;
	GunBash.SwingTime = 0.55f;
	GunBash.StaggerDuration = 1.2f;
	GunBash.bCanTakedown = true;

	Fist.Damage = 12.f;
	Fist.Range = 140.f;
	Fist.SweepRadius = 24.f;
	Fist.WindUp = 0.09f;
	Fist.SwingTime = 0.42f;
	Fist.StaggerDuration = 0.5f;
	Fist.bCanTakedown = false;

	Active = GunBash;
}

void UNVMeleeComponent::BeginPlay()
{
	Super::BeginPlay();
	if (!DamageType.IsValid())
	{
		DamageType = NVTags::Damage_Melee;
	}
}

FNVMeleeProfile UNVMeleeComponent::ProfileFor(ENVMeleeStyle Style) const
{
	switch (Style)
	{
	case ENVMeleeStyle::Fist:
		return Fist;
	case ENVMeleeStyle::GunBash:
		return GunBash;
	default:
	{
		FNVMeleeProfile B;
		B.Damage = Damage;
		B.Range = Range;
		B.SweepRadius = SweepRadius;
		B.WindUp = WindUp;
		B.SwingTime = SwingTime;
		B.StaggerDuration = StaggerDuration;
		B.bCanTakedown = true;
		return B;
	}
	}
}

bool UNVMeleeComponent::IsSwinging() const
{
	return GetWorld() && GetWorld()->GetTimeSeconds() - SwingStartTime < Active.SwingTime;
}

float UNVMeleeComponent::GetSwingAlpha() const
{
	if (!GetWorld() || Active.SwingTime <= 0.f)
	{
		return 0.f;
	}
	const float A = (GetWorld()->GetTimeSeconds() - SwingStartTime) / Active.SwingTime;
	return (A >= 0.f && A < 1.f) ? A : 0.f;
}

bool UNVMeleeComponent::Strike(ENVMeleeStyle Style)
{
	if (IsSwinging())
	{
		return false;
	}
	ActiveStyle = Style;
	Active = ProfileFor(Style);
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
	GetWorld()->GetTimerManager().SetTimer(HitTimer, this, &UNVMeleeComponent::ResolveHit, FMath::Max(0.01f, Active.WindUp), false);
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
	const FVector End = Start + Dir * Active.Range;

	FCollisionQueryParams Params(SCENE_QUERY_STAT(NVMeleeSweep), false, GetOwner());
	{
		FHitResult PawnHit;
		if (GetWorld()->SweepSingleByChannel(PawnHit, Start, End, FQuat::Identity, ECC_Pawn, FCollisionShape::MakeSphere(Active.SweepRadius), Params)
			&& NVFriendly::IsFriendly(PawnHit.GetActor()))
		{
			UE_LOG(LogNeonVeil, Log, TEXT("Melee held: %s is friendly"), *PawnHit.GetActor()->GetName());
			return;
		}
	}
	TArray<FHitResult> Hits;
	GetWorld()->SweepMultiByChannel(Hits, Start, End, FQuat::Identity, ECC_Visibility, FCollisionShape::MakeSphere(Active.SweepRadius), Params);

	for (const FHitResult& Hit : Hits)
	{
		AActor* A = Hit.GetActor();
		UNVHealthComponent* Health = A ? A->FindComponentByClass<UNVHealthComponent>() : nullptr;
		if (!Health || Health->IsDead())
		{
			if (Hit.bBlockingHit)
			{
				UE_LOG(LogNeonVeil, Log, TEXT("Melee strike blocked by %s"), *GetNameSafe(A));
				return; // wall in the way
			}
			continue;
		}
		INVStaggerable* Stag = Cast<INVStaggerable>(A);
		const bool bTakedown = Active.bCanTakedown && Stag && Stag->IsStaggered() && Stag->CanBeTakenDown();
		const float Applied = Health->ApplyDamage(bTakedown ? TakedownDamage : Active.Damage, GetOwner(), DamageType, false);
		if (!bTakedown && Stag && !Health->IsDead() && Active.StaggerDuration > 0.f)
		{
			Stag->ApplyStagger(Active.StaggerDuration, GetOwner());
		}
		UE_LOG(LogNeonVeil, Log, TEXT("Melee(%d) %s %s: applied %.1f, hp %.1f"), static_cast<int32>(ActiveStyle), bTakedown ? TEXT("TAKEDOWN on") : TEXT("hit"), *A->GetName(), Applied, Health->GetHealth());
		if (HitSound)
		{
			UGameplayStatics::PlaySound2D(this, HitSound);
		}
		OnMeleeHit.Broadcast(A, bTakedown);
		return;
	}
	UE_LOG(LogNeonVeil, Log, TEXT("Melee swing hit nothing"));
}
