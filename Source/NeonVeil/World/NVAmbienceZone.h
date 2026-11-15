#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "NVAmbienceZone.generated.h"

class UAudioComponent;

/**
 * Outdoor ambience (rain, open-air city) that is only fully heard outside: while the player is inside one of the
 * Outdoor boxes every tagged ambient sound plays at its own volume; moving indoors it fades down to IndoorVolume
 * and gets a low-pass (heard through walls), blending over BlendDistance past the box edge (a doorway).
 * Manages the audio components of actors tagged ManagedTag. Checks ten times a second.
 */
UCLASS()
class NEONVEIL_API ANVAmbienceZone : public AActor
{
	GENERATED_BODY()

public:
	ANVAmbienceZone();

	/** Outdoor regions, world space. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Ambience")
	TArray<FBox> Outdoor;

	/** Distance past an outdoor box over which the sound goes from outdoor to indoor. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Ambience", meta = (ClampMin = "1"))
	float BlendDistance = 500.f;

	/** Volume multiplier (relative to each sound's own) once fully indoors. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Ambience", meta = (ClampMin = "0", ClampMax = "1"))
	float IndoorVolume = 0.06f;

	/** Low-pass cutoff once fully indoors (Hz). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Ambience", meta = (ClampMin = "50"))
	float IndoorLowPassHz = 700.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Ambience")
	FName ManagedTag = TEXT("NVOutdoorAmb");

	virtual void Tick(float DeltaSeconds) override;

protected:
	virtual void BeginPlay() override;

private:
	struct FManaged
	{
		TWeakObjectPtr<UAudioComponent> Comp;
		float BaseVolume = 1.f;
	};
	TArray<FManaged> Managed;
	float Current = -1.f;
};
