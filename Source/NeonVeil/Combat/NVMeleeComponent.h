#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "GameplayTagContainer.h"
#include "NVMeleeComponent.generated.h"

class UCameraComponent;
class USoundBase;

DECLARE_DYNAMIC_MULTICAST_DELEGATE(FNVOnMeleeSwing);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FNVOnMeleeHit, AActor*, HitActor, bool, bTakedown);

/**
 * Shock baton (Bible §7). A short wind-up, then a sphere sweep along the aim. Hits stagger targets
 * that support it; a strike on a staggered target is a takedown. Tuning is on the component so a
 * Blueprint child of the player can adjust it.
 */
UCLASS(ClassGroup = (NeonVeil), meta = (BlueprintSpawnableComponent))
class NEONVEIL_API UNVMeleeComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	UNVMeleeComponent();

	UFUNCTION(BlueprintCallable, Category = "NeonVeil|Melee")
	bool Strike();

	UFUNCTION(BlueprintPure, Category = "NeonVeil|Melee")
	bool IsSwinging() const;

	/** 0..1 through the current swing, for viewmodel motion. */
	UFUNCTION(BlueprintPure, Category = "NeonVeil|Melee")
	float GetSwingAlpha() const;

	UPROPERTY(BlueprintAssignable, Category = "NeonVeil|Melee")
	FNVOnMeleeSwing OnSwing;

	UPROPERTY(BlueprintAssignable, Category = "NeonVeil|Melee")
	FNVOnMeleeHit OnMeleeHit;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melee")
	float Damage = 35.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melee")
	float TakedownDamage = 1000.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melee")
	float Range = 190.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melee")
	float SweepRadius = 30.f;

	/** Seconds from button press to the hit check. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melee")
	float WindUp = 0.12f;

	/** Seconds the full swing takes (also the minimum time between strikes). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melee")
	float SwingTime = 0.6f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melee")
	float StaggerDuration = 1.8f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melee")
	FGameplayTag DamageType;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melee")
	TObjectPtr<USoundBase> SwingSound;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melee")
	TObjectPtr<USoundBase> HitSound;

protected:
	virtual void BeginPlay() override;

private:
	void ResolveHit();

	FTimerHandle HitTimer;
	float SwingStartTime = -100.f;
};
