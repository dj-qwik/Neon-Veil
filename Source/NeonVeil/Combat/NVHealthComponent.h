#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "GameplayTagContainer.h"
#include "NVHealthComponent.generated.h"

DECLARE_DYNAMIC_MULTICAST_DELEGATE_FiveParams(FNVOnHealthChanged, UNVHealthComponent*, HealthComp, float, NewHealth, float, Delta, AActor*, Instigator, FGameplayTag, DamageType);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FNVOnDeath, UNVHealthComponent*, HealthComp, AActor*, Killer);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FNVOnShieldChanged, UNVHealthComponent*, HealthComp, float, NewShield);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FNVOnShieldBroken, UNVHealthComponent*, HealthComp);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FNVOnDamageBlocked, UNVHealthComponent*, HealthComp, float, BlockedAmount);

/**
 * Health, armor and death for players, enemies and destructible targets.
 * Damage arrives through ApplyDamage so weak-point and armor rules stay in one place.
 */
UCLASS(ClassGroup = (NeonVeil), meta = (BlueprintSpawnableComponent))
class NEONVEIL_API UNVHealthComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	UNVHealthComponent();

	/** Returns the damage actually applied after armor and multipliers. */
	UFUNCTION(BlueprintCallable, Category = "NeonVeil|Health")
	float ApplyDamage(float Amount, AActor* DamageInstigator, FGameplayTag DamageType, bool bWeakPointHit = false);

	UFUNCTION(BlueprintCallable, Category = "NeonVeil|Health")
	float Heal(float Amount);

	UFUNCTION(BlueprintCallable, Category = "NeonVeil|Health")
	void ResetHealth();

	/** Restores a saved value without firing damage events (checkpoint load). */
	UFUNCTION(BlueprintCallable, Category = "NeonVeil|Health")
	void SetHealthDirect(float NewHealth);

	UFUNCTION(BlueprintPure, Category = "NeonVeil|Health")
	float GetHealth() const { return Health; }

	UFUNCTION(BlueprintPure, Category = "NeonVeil|Health")
	float GetMaxHealth() const { return MaxHealth; }

	UFUNCTION(BlueprintPure, Category = "NeonVeil|Health")
	float GetHealthPercent() const { return MaxHealth > 0.f ? Health / MaxHealth : 0.f; }

	UFUNCTION(BlueprintPure, Category = "NeonVeil|Health")
	bool IsDead() const { return bDead; }

	UPROPERTY(BlueprintAssignable, Category = "NeonVeil|Health")
	FNVOnHealthChanged OnHealthChanged;

	UPROPERTY(BlueprintAssignable, Category = "NeonVeil|Health")
	FNVOnDeath OnDeath;

	UPROPERTY(BlueprintAssignable, Category = "NeonVeil|Health")
	FNVOnShieldChanged OnShieldChanged;

	UPROPERTY(BlueprintAssignable, Category = "NeonVeil|Health")
	FNVOnShieldBroken OnShieldBroken;

	/** Fired when IncomingDamageScale removed damage (kinetic shield feedback). */
	UPROPERTY(BlueprintAssignable, Category = "NeonVeil|Health")
	FNVOnDamageBlocked OnDamageBlocked;

	UFUNCTION(BlueprintPure, Category = "NeonVeil|Health")
	float GetShield() const { return Shield; }

	/** Multiplier on all incoming damage, set by abilities (kinetic shield = 0). */
	UPROPERTY(VisibleInstanceOnly, BlueprintReadWrite, Category = "NeonVeil|Health")
	float IncomingDamageScale = 1.f;

	float GetBlockedDamage() const { return BlockedDamage; }
	void ResetBlockedDamage() { BlockedDamage = 0.f; }

	UFUNCTION(BlueprintCallable, Category = "NeonVeil|Health")
	void RestoreShield();

	/** Shield absorbs damage before health. 0 = no shield. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "NeonVeil|Health", meta = (ClampMin = "0"))
	float MaxShield = 0.f;

	/** If false, weak-point hits bypass the shield (teaches weak points in the simulation). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "NeonVeil|Health")
	bool bShieldCoversWeakPoints = false;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "NeonVeil|Health", meta = (ClampMin = "1"))
	float MaxHealth = 100.f;

	/** Flat fraction of incoming damage removed (0..0.9). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "NeonVeil|Health", meta = (ClampMin = "0", ClampMax = "0.9"))
	float ArmorFraction = 0.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "NeonVeil|Health", meta = (ClampMin = "1"))
	float WeakPointMultiplier = 2.f;

	/** Damage types this component ignores (e.g. training rounds on real enemies). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "NeonVeil|Health")
	FGameplayTagContainer ImmuneDamageTypes;

	/** Player health never drops below 1 while true (scripted training volley). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "NeonVeil|Health")
	bool bCannotDie = false;

protected:
	virtual void BeginPlay() override;

private:
	UPROPERTY(VisibleInstanceOnly, Category = "NeonVeil|Health")
	float Health = 100.f;

	UPROPERTY(VisibleInstanceOnly, Category = "NeonVeil|Health")
	float Shield = 0.f;

	bool bDead = false;
	float BlockedDamage = 0.f;
};
