#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "GameplayTagContainer.h"
#include "Combat/NVStaggerable.h"
#include "NVTrainingTarget.generated.h"

class UStaticMeshComponent;
class USkeletalMeshComponent;
class UAnimSequence;
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
class NEONVEIL_API ANVTrainingTarget : public AActor, public INVStaggerable
{
	GENERATED_BODY()

public:
	ANVTrainingTarget();

	virtual void Tick(float DeltaSeconds) override;

	UFUNCTION(BlueprintCallable, Category = "NeonVeil|Target")
	void Activate();

	UFUNCTION(BlueprintCallable, Category = "NeonVeil|Target")
	void ResetTarget();

	/** Hide and stop the target without counting it as cleared. */
	UFUNCTION(BlueprintCallable, Category = "NeonVeil|Target")
	void Deactivate();

	UFUNCTION(BlueprintPure, Category = "NeonVeil|Target")
	bool IsCleared() const { return bCleared; }

	UPROPERTY(BlueprintAssignable, Category = "NeonVeil|Target")
	FNVOnTargetDestroyed OnTargetCleared;

	// INVStaggerable
	virtual void ApplyStagger(float Duration, AActor* StaggerInstigator) override;
	virtual bool IsStaggered() const override { return StaggerTimeLeft > 0.f; }
	virtual bool CanBeTakenDown() const override { return bAllowTakedown; }

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

	/** Vertical hover bob (sim drone). 0 = none. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Target")
	float BobAmplitude = 0.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Target")
	float BobSpeed = 2.f;

	/** Melee dummy: a baton strike staggers it, a second strike while staggered is a takedown. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Target")
	bool bAllowTakedown = true;

	// ---- Hologram combatant figure (optional skeletal component named "Figure", rifle component named "FigureGun") ----

	/** Pose while standing / paused at a patrol end (faces the lane). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Target|Figure")
	TObjectPtr<UAnimSequence> FigureIdleAnim;

	/** Loop while walking a patrol leg (faces the direction of travel). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Target|Figure")
	TObjectPtr<UAnimSequence> FigureWalkAnim;

	/** Ground speed the walk loop was authored at; play rate = patrol speed / this. 0 = measure from root motion (fallback 160). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Target|Figure")
	float FigureWalkAnimSpeed = 0.f;

	/** Walking figures move at this speed (cm/s) instead of PatrolSpeed. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Target|Figure")
	float FigureWalkSpeed = 150.f;

	/** Seconds a walking figure stands at each patrol end, facing the lane, before turning back. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Target|Figure")
	float PatrolEndPause = 1.6f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Target|Figure")
	float FigureTurnRate = 300.f;

	/** Figure relative yaw that makes the mesh itself face the actor's forward (UE skeletal meshes face +Y: -90). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Target|Figure")
	float FigureMeshForwardYaw = -90.f;

	/** Rifle relative to the figure's grip socket (hand_r), measured from the idle pose in the editor. Identity = leave the rifle where it is. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Target|Figure")
	FTransform FigureGunGrip = FTransform::Identity;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Target|Figure")
	FName FigureGunSocket = TEXT("hand_r");

	/** Head weak point follows this bone (offset up by HeadCentreUp). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Target|Figure")
	FName FigureHeadBone = TEXT("head");

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Target|Figure")
	float HeadCentreUp = 9.f;

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

	bool NeedsTick() const;

	void SetupFigure();
	void UpdateFigure(float DeltaSeconds, const FVector& Velocity);
	void PlayFigureAnim(UAnimSequence* Anim, float Rate);

	UPROPERTY(Transient)
	TObjectPtr<USkeletalMeshComponent> HoloFigure;

	UPROPERTY(Transient)
	TObjectPtr<USceneComponent> HoloGun;

	UPROPERTY(Transient)
	TObjectPtr<UAnimSequence> FigureCurrentAnim;

	float FigureFacingYaw = 0.f;     // relative yaw of the figure that faces the lane
	float FigureYaw = 0.f;           // current relative yaw
	float PatrolPauseLeft = 0.f;
	FVector StartLocation;
	FRotator StartRotation;
	float StaggerTimeLeft = 0.f;
	float Age = 0.f;
	float PatrolAlpha = 0.f;
	float PatrolDir = 1.f;
	bool bActive = false;
	bool bCleared = false;
};
