#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "GameplayTagContainer.h"
#include "NVMeleeComponent.generated.h"

class UCameraComponent;
class USoundBase;

DECLARE_DYNAMIC_MULTICAST_DELEGATE(FNVOnMeleeSwing);

/** What the strike is made with. The baton is its own weapon slot; the Melee button bashes with whatever is in hand. */
UENUM(BlueprintType)
enum class ENVMeleeStyle : uint8
{
	Baton,      // shock baton (equipped weapon, Fire)
	GunBash,    // butt-stroke / pistol-whip with the current gun (Melee button)
	Fist        // unarmed punch (Melee button, nothing in hand)
};

/** Tuning for one melee style. */
USTRUCT(BlueprintType)
struct FNVMeleeProfile
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melee")
	float Damage = 20.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melee")
	float Range = 160.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melee")
	float SweepRadius = 28.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melee")
	float WindUp = 0.12f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melee")
	float SwingTime = 0.55f;

	/** 0 = no stagger. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melee")
	float StaggerDuration = 1.2f;

	/** A strike on a staggered target finishes it. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melee")
	bool bCanTakedown = true;
};
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
	bool Strike(ENVMeleeStyle Style = ENVMeleeStyle::GunBash);

	/** The style of the swing in progress (or the last one). */
	UFUNCTION(BlueprintPure, Category = "NeonVeil|Melee")
	ENVMeleeStyle GetSwingStyle() const { return ActiveStyle; }

	UFUNCTION(BlueprintPure, Category = "NeonVeil|Melee")
	bool IsSwinging() const;

	/** 0..1 through the current swing, for viewmodel motion. */
	UFUNCTION(BlueprintPure, Category = "NeonVeil|Melee")
	float GetSwingAlpha() const;

	UPROPERTY(BlueprintAssignable, Category = "NeonVeil|Melee")
	FNVOnMeleeSwing OnSwing;

	UPROPERTY(BlueprintAssignable, Category = "NeonVeil|Melee")
	FNVOnMeleeHit OnMeleeHit;

	// --- Shock baton (the fields below predate the other styles and stay the baton's tuning)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melee")
	float Damage = 35.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melee")
	float TakedownDamage = 1000.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melee")
	float Range = 190.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melee")
	float SweepRadius = 30.f;

	/** Seconds from button press to the hit check (lands with the overhead chop of the viewmodel). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melee")
	float WindUp = 0.38f;

	/** Seconds the full swing takes (also the minimum time between strikes). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melee")
	float SwingTime = 0.75f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melee")
	float StaggerDuration = 1.8f;

	/** Butt-stroke / pistol-whip with the gun in hand. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melee")
	FNVMeleeProfile GunBash;

	/** Unarmed punch: quick, light, a short flinch, no takedown. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Melee")
	FNVMeleeProfile Fist;

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

	FNVMeleeProfile ProfileFor(ENVMeleeStyle Style) const;

	FTimerHandle HitTimer;
	float SwingStartTime = -100.f;
	FNVMeleeProfile Active;
	ENVMeleeStyle ActiveStyle = ENVMeleeStyle::GunBash;
};
