#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "GameplayTagContainer.h"
#include "NVAbilityComponent.generated.h"

class UNVAbilityData;
class ANVReconDrone;

UENUM(BlueprintType)
enum class ENVAbilityFailReason : uint8
{
	None,
	NoAbility,
	Disabled,
	OnCooldown,
	AlreadyActive
};

USTRUCT(BlueprintType)
struct FNVAbilityRuntime
{
	GENERATED_BODY()

	UPROPERTY(BlueprintReadOnly, Category = "Ability")
	float ActiveTimeLeft = 0.f;

	UPROPERTY(BlueprintReadOnly, Category = "Ability")
	float CooldownLeft = 0.f;

	/** Story-disabled (M01 cyberware failure). Persists through save/load. */
	UPROPERTY(BlueprintReadOnly, Category = "Ability")
	bool bDisabled = false;
};

USTRUCT()
struct FNVMarkedActor
{
	GENERATED_BODY()

	UPROPERTY()
	TWeakObjectPtr<AActor> Actor;

	float ExpiresAt = 0.f;
};

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FNVOnAbilityEvent, FGameplayTag, AbilityTag);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FNVOnAbilityFailed, FGameplayTag, AbilityTag, ENVAbilityFailReason, Reason);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FNVOnTargetsMarked, int32, NewlyMarked);

/**
 * Ghost-7's cyberware (Bible §9, §11): optical disruption, kinetic shield and drone uplink, with
 * cooldowns and story disable/restore. Effects are applied here so detection, damage and HUD code
 * only need to ask simple questions (IsActorCloaked, IsAbilityActive, GetMarkedActors).
 */
UCLASS(ClassGroup = (NeonVeil), meta = (BlueprintSpawnableComponent))
class NEONVEIL_API UNVAbilityComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	UNVAbilityComponent();

	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

	/** Slot order is the HUD order and the input order (Ability1..3). */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Abilities")
	TArray<TObjectPtr<UNVAbilityData>> Abilities;

	UFUNCTION(BlueprintCallable, Category = "NeonVeil|Abilities")
	bool TryActivateSlot(int32 Slot);

	UFUNCTION(BlueprintCallable, Category = "NeonVeil|Abilities")
	bool TryActivate(FGameplayTag AbilityTag);

	/** Ends an active effect early (cloak broken by attacking). Starts the cooldown. */
	UFUNCTION(BlueprintCallable, Category = "NeonVeil|Abilities")
	void EndAbility(FGameplayTag AbilityTag);

	UFUNCTION(BlueprintPure, Category = "NeonVeil|Abilities")
	bool IsAbilityActive(FGameplayTag AbilityTag) const;

	UFUNCTION(BlueprintPure, Category = "NeonVeil|Abilities")
	bool IsAbilityDisabled(FGameplayTag AbilityTag) const;

	/** Story hook for M01: disabled abilities cannot activate and show as offline (QA-04). */
	UFUNCTION(BlueprintCallable, Category = "NeonVeil|Abilities")
	void SetAbilityDisabled(FGameplayTag AbilityTag, bool bDisabled);

	/** 0 = ready, 1 = just started cooling down. */
	UFUNCTION(BlueprintPure, Category = "NeonVeil|Abilities")
	float GetCooldownFraction(int32 Slot) const;

	/** 1 = just activated, 0 = expired. */
	UFUNCTION(BlueprintPure, Category = "NeonVeil|Abilities")
	float GetActiveFraction(int32 Slot) const;

	const FNVAbilityRuntime* GetRuntime(int32 Slot) const { return Runtime.IsValidIndex(Slot) ? &Runtime[Slot] : nullptr; }

	/** Called by the weapon and melee code. Ends optical disruption if it breaks on attack. */
	void NotifyAttacked();

	/** True if Actor has an active optical disruption. Detection systems call this. */
	UFUNCTION(BlueprintPure, Category = "NeonVeil|Abilities")
	static bool IsActorCloaked(const AActor* Actor);

	/** Drone uplink results; expired marks are pruned on tick. */
	TArray<AActor*> GetMarkedActors() const;

	/** Called by the recon drone with everything its scan found. */
	void AddMarks(const TArray<AActor*>& Actors, float Duration);

	/** Save support. */
	TArray<FGameplayTag> GetDisabledTags() const;
	void RestoreDisabledTags(const TArray<FGameplayTag>& Tags);

	/** QA: clear all cooldowns. */
	void DebugResetCooldowns();

	UPROPERTY(BlueprintAssignable, Category = "NeonVeil|Abilities")
	FNVOnAbilityEvent OnAbilityActivated;

	UPROPERTY(BlueprintAssignable, Category = "NeonVeil|Abilities")
	FNVOnAbilityEvent OnAbilityEnded;

	UPROPERTY(BlueprintAssignable, Category = "NeonVeil|Abilities")
	FNVOnAbilityFailed OnAbilityFailed;

	UPROPERTY(BlueprintAssignable, Category = "NeonVeil|Abilities")
	FNVOnTargetsMarked OnTargetsMarked;

protected:
	virtual void BeginPlay() override;

private:
	int32 FindSlot(FGameplayTag AbilityTag) const;
	void StartEffect(int32 Slot);
	void StopEffect(int32 Slot, bool bStartCooldown);

	UPROPERTY(VisibleInstanceOnly, Category = "Abilities")
	TArray<FNVAbilityRuntime> Runtime;

	UPROPERTY()
	TArray<FNVMarkedActor> Marks;

	UPROPERTY()
	TWeakObjectPtr<ANVReconDrone> ActiveDrone;
};
