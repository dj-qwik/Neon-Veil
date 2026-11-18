#pragma once

#include "CoreMinimal.h"
#include "Components/SceneComponent.h"
#include "GameplayTagContainer.h"
#include "NVHostileFire.generated.h"

class UStaticMeshComponent;
class UMaterialInterface;
class USoundBase;
class UNiagaraSystem;

/**
 * Shared hostile gunfire for M01+ enemies (security drones, sentry turrets, Directorate troopers): one hitscan
 * shot with spread, blocked by walls and cover, damage through UNVHealthComponent, plus a short tracer from a pool.
 * Add the component to an enemy and call Fire(). Tracers live in world space and fade after TracerLife.
 */
UCLASS(ClassGroup = (NeonVeil), meta = (BlueprintSpawnableComponent))
class NEONVEIL_API UNVHostileFire : public USceneComponent
{
	GENERATED_BODY()

public:
	UNVHostileFire();
	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

	/** Fire one shot from this component's location toward AimPoint. Returns true if it hit Target. */
	UFUNCTION(BlueprintCallable, Category = "NeonVeil|HostileFire")
	bool Fire(AActor* Target, const FVector& AimPoint);

	/** A good point to aim at on Target: a random height on its capsule, else its location. */
	static FVector AimPointOn(const AActor* Target);

	/** True if nothing but Target blocks the line from From to Target's eye/centre (cloaked targets are never seen). */
	static bool CanSee(const UWorld* World, const AActor* Self, const FVector& From, const AActor* Target);

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "HostileFire")
	float Damage = 6.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "HostileFire")
	float SpreadDeg = 2.5f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "HostileFire")
	float Range = 4000.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "HostileFire")
	FGameplayTag DamageType;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "HostileFire")
	TObjectPtr<UMaterialInterface> TracerMaterial;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "HostileFire")
	float TracerThickness = 0.035f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "HostileFire")
	float TracerLife = 0.06f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "HostileFire")
	TObjectPtr<USoundBase> ShotSound;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "HostileFire")
	float ShotVolume = 0.7f;
	/** Small burst where a shot strikes a wall (not the target). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "HostileFire")
	TObjectPtr<UNiagaraSystem> ImpactFX;

protected:
	virtual void BeginPlay() override;

private:
	UPROPERTY(Transient)
	TArray<TObjectPtr<UStaticMeshComponent>> Tracers;
	TArray<float> TracerTime;
	int32 NextTracer = 0;
};
