#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "UI/NVSubtitleLine.h"
#include "NVSkyCarLiftoff.generated.h"

class ACharacter;
class UAudioComponent;
class UBoxComponent;
class UMaterialInstanceDynamic;
class UNiagaraSystem;
class UPointLightComponent;
class USoundAttenuation;
class USoundBase;
class USpotLightComponent;
class UStaticMeshComponent;

/**
 * A parked sky car that performs a one-shot cinematic departure:
 *  1. (optional) an NPC driver walks to BoardPoint, climbs in, the canopy swings shut;
 *  2. when the player comes within LightsOnDistance the car wakes: headlights blink on, glow strips and underglow
 *     rise, idle hum starts;
 *  3. within LiftoffDistance it spools up, rises straight up on its thrusters, turns and climbs away along a curve
 *     into the traffic lane at JoinPoint, then cruises off and disappears.
 * A static Blocker box (enabled once the driver is aboard) keeps the player close but off the car.
 */
UCLASS()
class NEONVEIL_API ANVSkyCarLiftoff : public AActor
{
	GENERATED_BODY()

public:
	ANVSkyCarLiftoff();
	virtual void BeginPlay() override;
	virtual void Tick(float DeltaSeconds) override;

	// --- components
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components") TObjectPtr<USceneComponent> Root;
	/** Everything that flies hangs off CarRoot. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components") TObjectPtr<USceneComponent> CarRoot;
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components") TObjectPtr<UStaticMeshComponent> Body;
	/** Pivot = the canopy hinge (place it with its relative location). */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components") TObjectPtr<UStaticMeshComponent> Canopy;
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components") TObjectPtr<USpotLightComponent> HeadL;
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components") TObjectPtr<USpotLightComponent> HeadR;
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components") TObjectPtr<UPointLightComponent> TailL;
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components") TObjectPtr<UPointLightComponent> TailR;
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components") TObjectPtr<UPointLightComponent> UnderF;
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components") TObjectPtr<UPointLightComponent> UnderR;
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components") TObjectPtr<UPointLightComponent> Cabin;
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components") TObjectPtr<UAudioComponent> Hum;
	/** Stays put at the parking spot: keeps the player from touching / climbing the car. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components") TObjectPtr<UBoxComponent> Blocker;

	// --- driver
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SkyCar|Driver") TObjectPtr<ACharacter> Driver;
	/** Local to the car: where the driver stops beside the cockpit / where they end up seated. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SkyCar|Driver") FVector BoardPoint = FVector(20.f, 175.f, 0.f);
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SkyCar|Driver") FVector SeatPoint = FVector(20.f, 30.f, 60.f);
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SkyCar|Driver") float BoardRadius = 30.f;
	/** The driver is walked to the car by this actor (its AI is switched off): delay, then pace. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SkyCar|Driver") float DriverStartDelay = 1.5f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SkyCar|Driver") float DriverWalkSpeed = 165.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SkyCar|Driver") float ClimbTime = 1.1f;
	/** Canopy rotation when open (relative to closed). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SkyCar|Driver") FRotator CanopyOpen = FRotator(-50.f, 0.f, 0.f);
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SkyCar|Driver") float CanopyCloseTime = 1.6f;

	// --- triggers
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SkyCar") float LightsOnDistance = 2600.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SkyCar") float LiftoffDistance = 650.f;
	/** Seconds the car idles with lights on before it may lift off. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SkyCar") float MinIdleBeforeLiftoff = 2.f;
	/** If the player lingers within LingerDistance this long after lights-on, it goes anyway. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SkyCar") float LingerDistance = 1500.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SkyCar") float LingerTime = 20.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SkyCar") FVector BlockerExtent = FVector(400.f, 250.f, 320.f);

	// --- flight
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SkyCar|Flight") float SpoolTime = 1.8f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SkyCar|Flight") float HoverHeight = 750.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SkyCar|Flight") float RiseTime = 5.f;
	/** World point in the traffic lane the car merges into, and the lane's direction there. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SkyCar|Flight") FVector JoinPoint = FVector::ZeroVector;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SkyCar|Flight") FVector JoinDirection = FVector(0.f, 1.f, 0.f);
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SkyCar|Flight") float DepartTime = 9.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SkyCar|Flight") float CruiseSpeed = 5200.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SkyCar|Flight") float CruiseTime = 9.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SkyCar|Flight") float MaxBank = 28.f;

	// --- look
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SkyCar|Look") FName GlowParam = TEXT("Glow");
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SkyCar|Look") float GlowOn = 1.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SkyCar|Look") float GlowThrust = 3.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SkyCar|Look") TObjectPtr<UNiagaraSystem> LiftDustFX;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SkyCar|Look") float LiftDustScale = 3.f;

	// --- audio / lines
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SkyCar|Audio") TObjectPtr<USoundBase> CanopySound;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SkyCar|Audio") TObjectPtr<USoundBase> PowerUpSound;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SkyCar|Audio") TObjectPtr<USoundBase> HumSound;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SkyCar|Audio") TObjectPtr<USoundBase> LiftoffSound;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SkyCar|Audio") TObjectPtr<USoundAttenuation> Attenuation;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SkyCar|Audio") float LiftoffVolume = 1.6f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SkyCar|Lines") TArray<FNVSubtitleLine> LinesOnLightsOn;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SkyCar|Lines") TArray<FNVSubtitleLine> LinesOnLiftoff;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "SkyCar|Lines") float LiftoffLineDelay = 4.5f;

private:
	enum class EPhase : uint8 { WaitDriver, Climb, Closing, Parked, Lit, Spool, Rise, Depart, Cruise, Gone };
	EPhase Phase = EPhase::Parked;
	float PhaseTime = 0.f;
	void SetPhase(EPhase P) { Phase = P; PhaseTime = 0.f; }

	void SetGlow(float G);
	void Say(const TArray<FNVSubtitleLine>& Lines);
	float PlayerDistance() const;
	void PlaceCar(const FVector& Pos, const FRotator& Rot);

	TArray<TObjectPtr<UMaterialInstanceDynamic>> GlowMIDs;
	FVector ParkPos, ClimbFrom, P1, C1, C2, P3, PrevPos;
	FRotator ParkRot, CurRot;
	float PrevYaw = 0.f, Bank = 0.f;
	bool bLiftLineSaid = false;
	float HeadBase = 0.f, TailBase = 0.f, UnderBase = 0.f, CabinBase = 0.f;
};
