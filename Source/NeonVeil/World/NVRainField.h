#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "NVRainField.generated.h"

class UInstancedStaticMeshComponent;
class UStaticMesh;
class UMaterialInterface;

/**
 * Volumetric rain beyond the sealed glass (Bible §4 / §14: "rain is multi-layered").
 * Thousands of thin streak quads scattered through a box. Each instance carries per-instance custom data
 * (phase, fall speed, brightness, box height); the material (M_NV_RainDrop) moves it down with World Position
 * Offset and wraps it to the top, so the fall costs no CPU and nothing tiles: every streak has its own
 * position, speed, length, width, brightness and slant, and the field has real parallax as the player moves.
 * Built once (construction / BeginPlay); no tick, no collision, no shadows.
 */
UCLASS()
class NEONVEIL_API ANVRainField : public AActor
{
	GENERATED_BODY()

public:
	ANVRainField();

	virtual void OnConstruction(const FTransform& Transform) override;
	virtual void BeginPlay() override;

	/** Half-size of the rain volume (cm), actor-local. */
	UPROPERTY(EditAnywhere, Category = "Rain")
	FVector Extent = FVector(2000.f, 500.f, 900.f);

	UPROPERTY(EditAnywhere, Category = "Rain", meta = (ClampMin = "1", ClampMax = "40000"))
	int32 Count = 3000;

	/** Fall speed range (cm/s). */
	UPROPERTY(EditAnywhere, Category = "Rain")
	FVector2D SpeedRange = FVector2D(850.f, 1150.f);

	/** Streak length range (cm). Longer reads as motion blur at distance. */
	UPROPERTY(EditAnywhere, Category = "Rain")
	FVector2D LengthRange = FVector2D(35.f, 70.f);

	/** Streak width range (cm). */
	UPROPERTY(EditAnywhere, Category = "Rain")
	FVector2D WidthRange = FVector2D(0.6f, 1.3f);

	/** Per-streak brightness range (multiplies the material colour and opacity). */
	UPROPERTY(EditAnywhere, Category = "Rain")
	FVector2D BrightnessRange = FVector2D(0.35f, 1.f);

	/** Wind slant (degrees from vertical) and random spread around it. */
	UPROPERTY(EditAnywhere, Category = "Rain")
	float Slant = 6.f;

	UPROPERTY(EditAnywhere, Category = "Rain")
	float SlantJitter = 2.5f;

	/** Streaks face actor-local ±Y; random yaw spread so they never look like a flat card. */
	UPROPERTY(EditAnywhere, Category = "Rain")
	float YawJitter = 35.f;

	UPROPERTY(EditAnywhere, Category = "Rain")
	int32 Seed = 1;

	UPROPERTY(EditAnywhere, Category = "Rain")
	TObjectPtr<UMaterialInterface> Material;

	UPROPERTY(EditAnywhere, Category = "Rain")
	TObjectPtr<UStaticMesh> StreakMesh;

	UPROPERTY(VisibleAnywhere, Category = "Rain")
	TObjectPtr<UInstancedStaticMeshComponent> Streaks;

private:
	void Build();
};
