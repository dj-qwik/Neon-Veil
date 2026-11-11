#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "GameplayTagContainer.h"
#include "NVTrainingTarget.generated.h"

class UStaticMeshComponent;
class UNVHealthComponent;
class USoundBase;
class UNiagaraSystem;

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FNVOnTargetDestroyed, ANVTrainingTarget*, Target);

/**
 * Holographic simulation target for the combat suite (M00-O02).
 * Moving targets patrol between two points; shielded targets take damage only through
 * the weak point until the shield breaks.
 */
UCLASS(Blueprintable)
class NEONVEIL_API ANVTrainingTarget : public AActor
{
	GENERATED_BODY()

public:
	ANVTrainingTarget();

	virtual void Tick(float DeltaSeconds) override;

	UFUNCTION(BlueprintCallable, Category = "NeonVeil|Target")
	void Activate();

	UFUNCTION(BlueprintCallable, Category = "NeonVeil|Target")
	void ResetTarget();

	UFUNCTION(BlueprintPure, Category = "NeonVeil|Target")
	bool IsCleared() const { return bCleared; }

	UPROPERTY(BlueprintAssignable, Category = "NeonVeil|Target")
	FNVOnTargetDestroyed OnTargetCleared;

protected:
	virtual void BeginPlay() override;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	TObjectPtr<USceneComponent> Root;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	TObjectPtr<UStaticMeshComponent> Body;

	/** Component tag "WeakPoint" marks it for the weapon trace. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	TObjectPtr<UStaticMeshComponent> WeakPoint;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	TObjectPtr<UStaticMeshComponent> ShieldMesh;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	TObjectPtr<UNVHealthComponent> Health;

	/** Local-space offset of the far end of the patrol. Zero = static target. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Target", meta = (MakeEditWidget = true))
	FVector PatrolOffset = FVector::ZeroVector;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Target")
	float PatrolSpeed = 180.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Target")
	bool bStartActive = false;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Target")
	TObjectPtr<USoundBase> ClearedSound;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Target")
	TObjectPtr<USoundBase> ShieldBreakSound;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Target")
	TObjectPtr<UNiagaraSystem> ClearedEffect;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Target")
	TObjectPtr<UNiagaraSystem> ShieldBreakEffect;

	/** Blueprint presentation hooks (hologram flicker, material pulses). */
	UFUNCTION(BlueprintImplementableEvent, Category = "NeonVeil|Target")
	void BP_OnActivated();

	UFUNCTION(BlueprintImplementableEvent, Category = "NeonVeil|Target")
	void BP_OnHit(bool bWeakPoint);

	UFUNCTION(BlueprintImplementableEvent, Category = "NeonVeil|Target")
	void BP_OnShieldBroken();

	UFUNCTION(BlueprintImplementableEvent, Category = "NeonVeil|Target")
	void BP_OnCleared();

private:
	UFUNCTION()
	void HandleHealthChanged(UNVHealthComponent* HealthComp, float NewHealth, float Delta, AActor* InstigatorActor, FGameplayTag DamageType);

	UFUNCTION()
	void HandleShieldBroken(UNVHealthComponent* HealthComp);

	UFUNCTION()
	void HandleDeath(UNVHealthComponent* HealthComp, AActor* Killer);

	void SetTargetVisible(bool bVisible);

	FVector StartLocation;
	float PatrolAlpha = 0.f;
	float PatrolDir = 1.f;
	bool bActive = false;
	bool bCleared = false;
};
