#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "GameplayTagContainer.h"
#include "NVAbilityData.generated.h"

class USoundBase;
class ANVReconDrone;

/**
 * One cyberware ability (Bible §9). All tuning lives here, not in code.
 * The ability component reads the shared fields; the type-specific blocks are read by the effect.
 */
UCLASS(BlueprintType)
class NEONVEIL_API UNVAbilityData : public UPrimaryDataAsset
{
	GENERATED_BODY()

public:
	/** NV.Ability.OpticalDisruption / KineticShield / DroneUplink. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Ability")
	FGameplayTag AbilityTag;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Ability")
	FText DisplayName;

	/** Two or three letters shown on the HUD ability bar. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Ability")
	FText ShortLabel;

	/** Seconds the effect lasts. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Ability", meta = (ClampMin = "0"))
	float Duration = 5.f;

	/** Seconds from the end of the effect until it can be used again. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Ability", meta = (ClampMin = "0"))
	float Cooldown = 15.f;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Ability|Presentation")
	TSoftObjectPtr<USoundBase> ActivateSound;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Ability|Presentation")
	TSoftObjectPtr<USoundBase> EndSound;

	// --- Optical disruption
	/** Firing or striking ends the cloak early. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Ability|Optical Disruption")
	bool bBreaksOnAttack = true;

	// --- Kinetic shield
	/** Fraction of incoming damage removed while active (1 = full block). */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Ability|Kinetic Shield", meta = (ClampMin = "0", ClampMax = "1"))
	float DamageReduction = 1.f;

	// --- Drone uplink
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Ability|Drone Uplink")
	TSubclassOf<ANVReconDrone> DroneClass;

	/** How far ahead of the player the drone flies before it scans. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Ability|Drone Uplink", meta = (ClampMin = "100"))
	float DroneRange = 1800.f;

	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Ability|Drone Uplink", meta = (ClampMin = "100"))
	float ScanRadius = 1500.f;

	/** How long marks stay on the HUD. */
	UPROPERTY(EditDefaultsOnly, BlueprintReadOnly, Category = "Ability|Drone Uplink", meta = (ClampMin = "0"))
	float MarkDuration = 12.f;
};
