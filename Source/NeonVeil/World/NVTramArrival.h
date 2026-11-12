#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "NVTramArrival.generated.h"

class UBoxComponent;
class USoundBase;
class UAudioComponent;

/**
 * Cinematic C00 (Bible §4): 12-18 s arrival-tram reveal with the camera player-driven, then control
 * on tram exit. On a fresh start the tram parts (and the player standing inside) begin Distance cm
 * back along the rail and glide in with an ease-out; the player can look around the whole time and
 * a barrier at the open tram front holds them until the tram docks. Skipped automatically when the
 * player does not start inside the tram (checkpoint loads). Parts must be Movable.
 */
UCLASS()
class NEONVEIL_API ANVTramArrival : public AActor
{
	GENERATED_BODY()

public:
	ANVTramArrival();

	virtual void BeginPlay() override;
	virtual void Tick(float DeltaSeconds) override;

	/** Actors that make up the tram (floor, shell, windows, interior lights). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Tram")
	TArray<TObjectPtr<AActor>> Parts;

	/** Distance the tram travels (along this actor's +X) before docking. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Tram", meta = (ClampMin = "0"))
	float Distance = 6000.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Tram", meta = (ClampMin = "1"))
	float Duration = 14.f;

	/** Player must start within this box (relative to this actor) for the arrival to play. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Tram")
	FVector CabinExtent = FVector(700.f, 300.f, 300.f);

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Tram")
	TObjectPtr<USoundBase> RideSound;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Tram")
	TObjectPtr<USoundBase> DockSound;

	UFUNCTION(BlueprintPure, Category = "Tram")
	bool IsArriving() const { return bArriving; }

protected:
	/** Holds the player inside until docked (sits across the open front). */
	UPROPERTY(VisibleAnywhere, Category = "Components")
	TObjectPtr<UBoxComponent> FrontBarrier;

	UPROPERTY(VisibleAnywhere, Category = "Components")
	TObjectPtr<UAudioComponent> RideAudio;

private:
	void ApplyOffset(float Offset);

	TArray<FVector> Home;
	TWeakObjectPtr<APawn> Rider;
	float Elapsed = 0.f;
	float LastOffset = 0.f;
	double LastRealTime = 0.0;
	double RideStartTime = 0.0;
	int32 RideTicks = 0;
	int32 SteadyFrames = 0;
	bool bMoving = false;
	bool bArriving = false;
	bool bChecked = false;
};
