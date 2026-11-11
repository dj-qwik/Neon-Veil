#include "Combat/NVHealthComponent.h"

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

void UNVHealthComponent::RestoreShield()
{
	Shield = MaxShield;
	OnShieldChanged.Broadcast(this, Shield);
}

float UNVHealthComponent::ApplyDamage(float Amount, AActor* DamageInstigator, FGameplayTag DamageType, bool bWeakPointHit)
{
	if (bDead || Amount <= 0.f || (DamageType.IsValid() && ImmuneDamageTypes.HasTag(DamageType)))
	{
		return 0.f;
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
