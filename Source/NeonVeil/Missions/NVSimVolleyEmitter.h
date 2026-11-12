#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "GameplayTagContainer.h"
#include "NVSimVolleyEmitter.generated.h"

class UStaticMeshComponent;
class UPointLightComponent;
class USoundBase;

DECLARE_DYNAMIC_MULTICAST_DELEGATE(FNVOnVolleyFinished);

/**
 * Simulation fire emitter for the cover and shield-burst drills (Bible §4: "surviving a scripted
 * incoming volley"). Telegraphs, then fires training rounds as real line traces at the target,
 * so cover and the kinetic shield work exactly as they will against live enemies.
 */
UCLASS(Blueprintable)
class NEONVEIL_API ANVSimVolleyEmitter : public AActor
{
	GENERATED_BODY()

public:
	ANVSimVolleyEmitter();

	virtual void Tick(float DeltaSeconds) override;

	/** Telegraph for WarmupSeconds, then fire at Target for FireSeconds. */
	UFUNCTION(BlueprintCallable, Category = "NeonVeil|Volley")
	void StartVolley(AActor* Target, float WarmupSeconds, float FireSeconds);

	UFUNCTION(BlueprintCallable, Category = "NeonVeil|Volley")
	void StopVolley();

	UFUNCTION(BlueprintPure, Category = "NeonVeil|Volley")
	bool IsWarmingUp() const { return Phase == EPhase::Warmup; }

	UFUNCTION(BlueprintPure, Category = "NeonVeil|Volley")
	bool IsFiring() const { return Phase == EPhase::Firing; }

	UPROPERTY(BlueprintAssignable, Category = "NeonVeil|Volley")
	FNVOnVolleyFinished OnVolleyFinished;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Volley")
	float ShotsPerSecond = 7.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Volley")
	float DamagePerShot = 8.f;

	/** Cone half-angle of shot scatter, degrees. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Volley")
	float SpreadDeg = 1.2f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Volley")
	FGameplayTag DamageType;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Volley")
	TObjectPtr<USoundBase> ShotSound;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Volley")
	TObjectPtr<USoundBase> WarningSound;

protected:
	virtual void BeginPlay() override;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	TObjectPtr<UStaticMeshComponent> Body;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	TObjectPtr<UPointLightComponent> Light;

	/** Pool of thin cylinders used as tracers (TEMP until VFX in M6). */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	TArray<TObjectPtr<UStaticMeshComponent>> Tracers;

private:
	enum class EPhase : uint8 { Idle, Warmup, Firing };

	void FireShot();

	EPhase Phase = EPhase::Idle;
	TWeakObjectPtr<AActor> VolleyTarget;
	float PhaseTimeLeft = 0.f;
	float ShotTimer = 0.f;
	int32 NextTracer = 0;
	TArray<float> TracerTimeLeft;
	int32 ShotsFired = 0;
	int32 ShotsLanded = 0;
};
