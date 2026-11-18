#include "Combat/NVHealthComponent.h"
#include "Engine/World.h"

UNVHealthComponent::UNVHealthComponent()
{
	PrimaryComponentTick.bCanEverTick = false;
}

void UNVHealthComponent::BeginPlay()
{
	Super::BeginPlay();
	Health = MaxHealth;
	Shield = MaxShield;
	bDead = false;
}

void UNVHealthComponent::GrantInvulnerability(float Seconds)
{
	if (const UWorld* World = GetWorld())
	{
		InvulnerableUntil = FMath::Max(InvulnerableUntil, World->GetTimeSeconds() + FMath::Max(0.f, Seconds));
	}
}

bool UNVHealthComponent::IsInvulnerable() const
{
	const UWorld* World = GetWorld();
	return World && World->GetTimeSeconds() < InvulnerableUntil;
}

void UNVHealthComponent::RestoreShield()
{
	Shield = MaxShield;
	OnShieldChanged.Broadcast(this, Shield);
}

float UNVHealthComponent::ApplyDamage(float Amount, AActor* DamageInstigator, FGameplayTag DamageType, bool bWeakPointHit)
{
	if (bDead || Amount <= 0.f || IsInvulnerable() || (DamageType.IsValid() && ImmuneDamageTypes.HasTag(DamageType)))
	{
		return 0.f;
	}

	if (IncomingDamageScale < 1.f)
	{
		const float Blocked = Amount * (1.f - FMath::Max(0.f, IncomingDamageScale));
		BlockedDamage += Blocked;
		Amount -= Blocked;
		OnDamageBlocked.Broadcast(this, Blocked);
		if (Amount <= 0.f)
		{
			return 0.f;
		}
	}

	float Final = Amount * (1.f - ArmorFraction);
	if (bWeakPointHit)
	{
		Final *= WeakPointMultiplier;
	}

	if (Shield > 0.f && (!bWeakPointHit || bShieldCoversWeakPoints))
	{
		const float Absorbed = FMath::Min(Shield, Final);
		Shield -= Absorbed;
		Final -= Absorbed;
		OnShieldChanged.Broadcast(this, Shield);
		if (Shield <= 0.f)
		{
			OnShieldBroken.Broadcast(this);
		}
		if (Final <= 0.f)
		{
			return Absorbed;
		}
	}

	const float Floor = bCannotDie ? 1.f : 0.f;
	const float OldHealth = Health;
	Health = FMath::Max(Floor, Health - Final);
	const float Applied = OldHealth - Health;

	OnHealthChanged.Broadcast(this, Health, -Applied, DamageInstigator, DamageType);

	if (Health <= 0.f)
	{
		bDead = true;
		OnDeath.Broadcast(this, DamageInstigator);
	}
	return Applied;
}

float UNVHealthComponent::Heal(float Amount)
{
	if (bDead || Amount <= 0.f)
	{
		return 0.f;
	}
	const float OldHealth = Health;
	Health = FMath::Min(MaxHealth, Health + Amount);
	const float Applied = Health - OldHealth;
	if (Applied > 0.f)
	{
		OnHealthChanged.Broadcast(this, Health, Applied, nullptr, FGameplayTag());
	}
	return Applied;
}

void UNVHealthComponent::ResetHealth()
{
	bDead = false;
	Health = MaxHealth;
	Shield = MaxShield;
	OnHealthChanged.Broadcast(this, Health, 0.f, nullptr, FGameplayTag());
}

void UNVHealthComponent::SetHealthDirect(float NewHealth)
{
	Health = FMath::Clamp(NewHealth, 0.f, MaxHealth);
	bDead = Health <= 0.f;
	OnHealthChanged.Broadcast(this, Health, 0.f, nullptr, FGameplayTag());
}
