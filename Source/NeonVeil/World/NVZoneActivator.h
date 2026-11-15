#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "NVZoneActivator.generated.h"

/**
 * Switches a set of tagged actors on only while the player is near a region (e.g. the station's steam and dust
 * emitters while the player is down on the street or in the lift). Deactivated actors stop ticking, their particle
 * systems stop and their primitives hide. Checks twice a second.
 */
UCLASS()
class NEONVEIL_API ANVZoneActivator : public AActor
{
	GENERATED_BODY()

public:
	ANVZoneActivator();

	/** World-space region (min/max corners). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Zone")
	FVector RegionMin = FVector::ZeroVector;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Zone")
	FVector RegionMax = FVector::ZeroVector;

	/** Extra distance around the region at which things wake up. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Zone")
	float Margin = 1500.f;

	/** Actors carrying this tag are managed. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Zone")
	FName ManagedTag = TEXT("NVZoneFX");

	virtual void Tick(float DeltaSeconds) override;

protected:
	virtual void BeginPlay() override;

private:
	void Apply(bool bOn);

	UPROPERTY(Transient)
	TArray<TObjectPtr<AActor>> Managed;

	int8 State = -1;
};
