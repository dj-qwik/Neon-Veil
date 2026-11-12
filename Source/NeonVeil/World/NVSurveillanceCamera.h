#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "NVSurveillanceCamera.generated.h"

class UStaticMeshComponent;
class USpotLightComponent;
class UMaterialInterface;

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FNVOnCameraDetected, AActor*, Detected);

/**
 * Sweeping security camera with a visible vision cone. Builds detection while the player is inside
 * the cone with line of sight and not under optical disruption; fires OnDetected at full detection.
 * Used for the M00 optical-disruption drill; the same actor serves the M01/M02 stealth spaces.
 */
UCLASS(Blueprintable)
class NEONVEIL_API ANVSurveillanceCamera : public AActor
{
	GENERATED_BODY()

public:
	ANVSurveillanceCamera();

	virtual void Tick(float DeltaSeconds) override;
	virtual void OnConstruction(const FTransform& Transform) override;

	UFUNCTION(BlueprintCallable, Category = "NeonVeil|Camera")
	void SetCameraActive(bool bActive);

	UFUNCTION(BlueprintPure, Category = "NeonVeil|Camera")
	bool IsCameraActive() const { return bCameraActive; }

	/** 0..1 detection of the player this frame. */
	UFUNCTION(BlueprintPure, Category = "NeonVeil|Camera")
	float GetDetection() const { return Detection; }

	UPROPERTY(BlueprintAssignable, Category = "NeonVeil|Camera")
	FNVOnCameraDetected OnDetected;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Camera")
	float ViewDistance = 1800.f;

	/** Cone half-angle, degrees. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Camera")
	float HalfAngle = 16.f;

	/** Sweep half-range around the actor's facing, degrees (0 = static). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Camera")
	float SweepAngle = 22.f;

	/** Seconds for one full left-right-left sweep. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Camera")
	float SweepPeriod = 6.f;

	/** Seconds of continuous exposure before detection. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Camera")
	float TimeToDetect = 0.45f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Camera")
	bool bStartActive = false;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Camera")
	TObjectPtr<UMaterialInterface> ConeMaterial;

protected:
	virtual void BeginPlay() override;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	TObjectPtr<USceneComponent> Root;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	TObjectPtr<UStaticMeshComponent> Mount;

	/** Rotates with the sweep; cone and lens hang off it. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	TObjectPtr<USceneComponent> Head;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	TObjectPtr<UStaticMeshComponent> HeadMesh;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	TObjectPtr<UStaticMeshComponent> Cone;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	TObjectPtr<USpotLightComponent> Spot;

private:
	void LayoutCone();
	bool CanSee(const AActor* Target) const;

	bool bCameraActive = false;
	float Detection = 0.f;
	float SweepTime = 0.f;
	float Cooldown = 0.f;
};
