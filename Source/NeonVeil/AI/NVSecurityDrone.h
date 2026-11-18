#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "GameplayTagContainer.h"
#include "NVSecurityDrone.generated.h"

class USphereComponent;
class UStaticMeshComponent;
class UPointLightComponent;
class UNVHealthComponent;
class UNVHostileFire;
class USoundBase;
class UNiagaraSystem;

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FNVOnDroneDestroyed, class ANVSecurityDrone*, Drone);

/**
 * Directorate security drone (Bible M01-A). Docked and dark until Activate(); then drops from its dock, circles the
 * player at range inside its flight box, and fires telegraphed three-round bursts while it has line of sight.
 * Shoot it down (health component); it falls, burns out, and sends DestroyedEventTag.
 */
UCLASS()
class NEONVEIL_API ANVSecurityDrone : public AActor
{
	GENERATED_BODY()

public:
	ANVSecurityDrone();
	virtual void Tick(float DeltaSeconds) override;

	UFUNCTION(BlueprintCallable, Category = "NeonVeil|Drone")
	void Activate(float Delay = 0.f);

	/** Checkpoint restore: already destroyed, stay out of the scene. */
	UFUNCTION(BlueprintCallable, Category = "NeonVeil|Drone")
	void SetWrecked();

	UFUNCTION(BlueprintPure, Category = "NeonVeil|Drone")
	bool IsDestroyed() const { return bDestroyed; }

	UPROPERTY(BlueprintAssignable, Category = "NeonVeil|Drone")
	FNVOnDroneDestroyed OnDestroyedDrone;

	/** Drone stays inside this world-space box (min / max corners). Zero size = unbounded. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Drone", meta = (MakeEditWidget = true))
	FVector BoundsMin = FVector::ZeroVector;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Drone", meta = (MakeEditWidget = true))
	FVector BoundsMax = FVector::ZeroVector;
	/** Drop from the dock this far (cm) on activation. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Drone")
	float DeployDrop = 220.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Drone")
	float OrbitRadius = 750.f;
	/** Height above the player's feet. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Drone")
	float HoverHeight = 330.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Drone")
	float MoveSpeed = 420.f;
	/** Degrees per second around the player (sign flips now and then). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Drone")
	float OrbitSpeed = 22.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Drone")
	float EngageRange = 2800.f;
	/** Red eye pulse before each burst (readable tell). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Drone")
	float TelegraphTime = 0.6f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Drone")
	int32 BurstShots = 3;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Drone")
	float ShotInterval = 0.12f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Drone")
	FVector2D BurstPause = FVector2D(1.8f, 2.8f);
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Drone")
	FGameplayTag DestroyedEventTag;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Drone|FX")
	TObjectPtr<USoundBase> TelegraphSound;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Drone|FX")
	TObjectPtr<USoundBase> HumSound;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Drone|FX")
	TObjectPtr<USoundBase> DestroyedSound;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Drone|FX")
	TObjectPtr<UNiagaraSystem> DestroyedFX;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Drone|FX")
	TObjectPtr<UNiagaraSystem> SmokeFX;

protected:
	virtual void BeginPlay() override;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	TObjectPtr<USphereComponent> Collision;
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	TObjectPtr<UStaticMeshComponent> Body;
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	TObjectPtr<UStaticMeshComponent> Ring;
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	TObjectPtr<UStaticMeshComponent> Eye;
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	TObjectPtr<UPointLightComponent> EyeLight;
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	TObjectPtr<UNVHostileFire> Gun;
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	TObjectPtr<UNVHealthComponent> Health;

private:
	UFUNCTION()
	void HandleDeath(UNVHealthComponent* HealthComp, AActor* Killer);
	void BeginActive();
	FVector ClampToBounds(const FVector& P) const;

	enum class EState : uint8 { Docked, Deploying, Active, Falling, Gone };
	EState State = EState::Docked;
	bool bDestroyed = false;
	FVector DockLocation;
	float StateTime = 0.f;
	float OrbitAngle = 0.f;
	float OrbitDir = 1.f;
	float NextDirFlip = 0.f;
	// firing: 0 idle (waiting NextBurst), 1 telegraph, 2 burst
	int32 FirePhase = 0;
	float FireTimer = 1.5f;
	int32 ShotsLeft = 0;
	FTimerHandle ActivateTimer;
	TWeakObjectPtr<AActor> Target;
	UPROPERTY(Transient)
	TObjectPtr<class UAudioComponent> Hum;
};
