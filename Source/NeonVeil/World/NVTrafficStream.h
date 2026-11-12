#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "NVTrafficStream.generated.h"

class UInstancedStaticMeshComponent;
class UStaticMesh;
class UMaterialInterface;

/**
 * Veyra-9 flying traffic (Bible §4: "flying transit", "parallax traffic layers").
 * A lane of distant vehicles read as moving light points: one instanced mesh for vehicles travelling
 * along the actor's +X (white/blue headlights toward the viewer side) and one for the opposite
 * direction (red tail lights). Instances wrap around the lane, so the stream is endless and costs a
 * single batched transform update per tick per direction. No collision, no shadows.
 */
UCLASS()
class NEONVEIL_API ANVTrafficStream : public AActor
{
	GENERATED_BODY()

public:
	ANVTrafficStream();

	virtual void OnConstruction(const FTransform& Transform) override;
	virtual void BeginPlay() override;
	virtual void Tick(float DeltaSeconds) override;

	/** Lane length along local X (cm). */
	UPROPERTY(EditAnywhere, Category = "Traffic", meta = (ClampMin = "1000"))
	float LaneLength = 200000.f;

	/** Half-width of the lane bundle across local Y (cm) and half-height across local Z. */
	UPROPERTY(EditAnywhere, Category = "Traffic")
	FVector2D LaneSpread = FVector2D(1200.f, 600.f);

	/** Vehicles per direction. */
	UPROPERTY(EditAnywhere, Category = "Traffic", meta = (ClampMin = "1", ClampMax = "600"))
	int32 VehiclesPerDirection = 90;

	/** Speed range (cm/s). */
	UPROPERTY(EditAnywhere, Category = "Traffic")
	FVector2D SpeedRange = FVector2D(3000.f, 6500.f);

	/** Size of each light body (cm). */
	UPROPERTY(EditAnywhere, Category = "Traffic")
	FVector VehicleScale = FVector(4.f, 1.2f, 0.6f);

	/** If false the reverse (tail-light) direction is not spawned. */
	UPROPERTY(EditAnywhere, Category = "Traffic")
	bool bTwoWay = true;

	UPROPERTY(EditAnywhere, Category = "Traffic")
	int32 Seed = 7;

	UPROPERTY(EditAnywhere, Category = "Traffic")
	TObjectPtr<UStaticMesh> VehicleMesh;

	UPROPERTY(EditAnywhere, Category = "Traffic")
	TObjectPtr<UMaterialInterface> ForwardMaterial;

	UPROPERTY(EditAnywhere, Category = "Traffic")
	TObjectPtr<UMaterialInterface> ReverseMaterial;

protected:
	UPROPERTY(VisibleAnywhere, Category = "Traffic")
	TObjectPtr<UInstancedStaticMeshComponent> Forward;

	UPROPERTY(VisibleAnywhere, Category = "Traffic")
	TObjectPtr<UInstancedStaticMeshComponent> Reverse;

private:
	struct FLaneCar
	{
		float X;
		float Speed;
		float Y;
		float Z;
	};
	TArray<FLaneCar> ForwardCars;
	TArray<FLaneCar> ReverseCars;

	void Build();
	void SetupComponent(UInstancedStaticMeshComponent* C, UMaterialInterface* Mat);
	void UpdateDirection(UInstancedStaticMeshComponent* C, TArray<FLaneCar>& Cars, float Sign, float DeltaSeconds);
};
