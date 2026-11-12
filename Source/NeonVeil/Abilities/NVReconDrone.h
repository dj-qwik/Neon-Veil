#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "NVReconDrone.generated.h"

class UStaticMeshComponent;
class UPointLightComponent;
class UNVAbilityComponent;

/**
 * Drone uplink (Bible §9): flies ahead along the player's aim, hovers, and repeatedly scans for
 * actors with health it can see, marking them on the owner's HUD. Recalled when the ability ends.
 * Placeholder sphere + light until the M5 art pass.
 */
UCLASS(Blueprintable)
class NEONVEIL_API ANVReconDrone : public AActor
{
	GENERATED_BODY()

public:
	ANVReconDrone();

	virtual void Tick(float DeltaSeconds) override;

	void Launch(UNVAbilityComponent* InOwner, const FVector& Direction, float Range, float InScanRadius, float InMarkDuration, float InLifetime);
	void Recall();

protected:
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	TObjectPtr<UStaticMeshComponent> Body;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	TObjectPtr<UPointLightComponent> Light;

	UPROPERTY(EditDefaultsOnly, Category = "Drone")
	float FlySpeed = 1400.f;

	UPROPERTY(EditDefaultsOnly, Category = "Drone")
	float ScanInterval = 0.5f;

	/** Hover this far above the launch point (clamped under ceilings) to see over low cover. */
	UPROPERTY(EditDefaultsOnly, Category = "Drone")
	float HoverHeight = 400.f;

	UFUNCTION(BlueprintImplementableEvent, Category = "NeonVeil|Drone")
	void BP_OnScan(int32 Found);

private:
	void Scan();

	TWeakObjectPtr<UNVAbilityComponent> OwnerAbilities;
	FVector Target = FVector::ZeroVector;
	float ScanRadius = 1500.f;
	float MarkDuration = 12.f;
	float ScanTimer = 0.f;
	float Age = 0.f;
	bool bArrived = false;
	bool bReturning = false;
};
