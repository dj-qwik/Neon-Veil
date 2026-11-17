#pragma once

#include "CoreMinimal.h"
#include "Camera/CameraModifier.h"
#include "NVBlastShake.generated.h"

/**
 * Camera shake for nearby blasts: a "trauma" value that kicks up and decays, driving Perlin-noise offsets of the view
 * location, rotation and FOV. Purely visual (the aim / control rotation is untouched). Use UNVBlastShake::Kick.
 */
UCLASS()
class NEONVEIL_API UNVBlastShake : public UCameraModifier
{
	GENERATED_BODY()

public:
	/** Adds trauma (0..1+) to the local player's camera; Decay is trauma lost per second. */
	static void Kick(const UObject* WorldContext, float Trauma, float Decay = 0.8f);

	virtual bool ModifyCamera(float DeltaTime, FMinimalViewInfo& InOutPOV) override;

	UPROPERTY(EditAnywhere, Category = "Shake")
	float MaxPitchYaw = 3.2f;
	UPROPERTY(EditAnywhere, Category = "Shake")
	float MaxRoll = 4.f;
	UPROPERTY(EditAnywhere, Category = "Shake")
	float MaxOffset = 9.f;
	UPROPERTY(EditAnywhere, Category = "Shake")
	float Frequency = 17.f;

private:
	float Trauma = 0.f;
	float DecayRate = 0.8f;
	float Clock = 0.f;
};
