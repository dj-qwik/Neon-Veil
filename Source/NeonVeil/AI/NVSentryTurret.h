#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "GameplayTagContainer.h"
#include "NVSentryTurret.generated.h"

class UStaticMeshComponent;
class UPointLightComponent;
class UNVHostileFire;
class USoundBase;

UENUM(BlueprintType)
enum class ENVTurretMode : uint8
{
	Off,
	/** Tracks and fires on the player. */
	Hostile,
	/** Hacked: fires on Directorate drones and troopers in its arc instead. */
	Rerouted
};

/**
 * Armoured ceiling/floor sentry (Bible M01-B). Can't be shot out: the player either reroutes it from a maintenance
 * terminal (RerouteEventTag; it then turns on the Directorate's own units and sends ObjectiveEventOnReroute) or goes
 * around it through the service bypass, behind its field of fire. A visible laser shows where it is aiming.
 */
UCLASS()
class NEONVEIL_API ANVSentryTurret : public AActor
{
	GENERATED_BODY()

public:
	ANVSentryTurret();
	virtual void Tick(float DeltaSeconds) override;

	UFUNCTION(BlueprintCallable, Category = "NeonVeil|Turret")
	void SetMode(ENVTurretMode NewMode);

	UFUNCTION(BlueprintPure, Category = "NeonVeil|Turret")
	ENVTurretMode GetMode() const { return Mode; }

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Turret")
	ENVTurretMode StartMode = ENVTurretMode::Off;
	/** Half-angle of the arc it can traverse, around its actor forward. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Turret")
	float FieldOfFireDeg = 65.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Turret")
	float Range = 4200.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Turret")
	float TurnRateDeg = 70.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Turret")
	float LockTime = 0.45f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Turret")
	int32 BurstShots = 6;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Turret")
	float ShotInterval = 0.09f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Turret")
	float BurstPause = 0.9f;
	/** Gameplay event that hacks it (sent by the maintenance terminal). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Turret")
	FGameplayTag RerouteEventTag;
	/** Sent once when rerouted (the objective it satisfies). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Turret")
	FGameplayTag ObjectiveEventOnReroute;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Turret|FX")
	TObjectPtr<USoundBase> LockSound;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Turret|FX")
	TObjectPtr<USoundBase> RerouteSound;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Turret|FX")
	TObjectPtr<UMaterialInterface> LaserHostile;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Turret|FX")
	TObjectPtr<UMaterialInterface> LaserFriendly;

protected:
	virtual void BeginPlay() override;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	TObjectPtr<USceneComponent> Root;
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	TObjectPtr<UStaticMeshComponent> Base;
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	TObjectPtr<USceneComponent> Head;
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	TObjectPtr<UStaticMeshComponent> HeadMesh;
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	TObjectPtr<UStaticMeshComponent> Barrel;
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	TObjectPtr<UStaticMeshComponent> Laser;
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	TObjectPtr<UPointLightComponent> StatusLight;
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	TObjectPtr<UNVHostileFire> Gun;

private:
	UFUNCTION()
	void HandleGameplayEvent(FGameplayTag EventTag);
	AActor* PickTarget() const;
	bool InArc(const FVector& P) const;

	ENVTurretMode Mode = ENVTurretMode::Off;
	TWeakObjectPtr<AActor> Current;
	float LockTimer = 0.f;
	float FireTimer = 0.f;
	int32 ShotsLeft = 0;
	float SweepTime = 0.f;
	bool bSentReroute = false;
};
