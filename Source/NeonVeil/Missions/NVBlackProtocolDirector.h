#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "GameplayTagContainer.h"
#include "UI/NVSubtitleLine.h"
#include "NVBlackProtocolDirector.generated.h"

class ALight;
class ANVObjectiveDoor;
class ANVSecurityDrone;
class ANVSentryTurret;
class ANVGuardCharacter;
class ANVInteractableActor;
class USoundBase;
class UAudioComponent;
class UNiagaraSystem;

/** A prop that moves between two transforms (ceiling shutters, lift doors, surgical arms). */
USTRUCT(BlueprintType)
struct FNVMover
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Mover")
	TObjectPtr<AActor> Actor = nullptr;
	/** Offset added to the start location when "on". */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Mover")
	FVector Offset = FVector::ZeroVector;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Mover")
	FRotator Rotation = FRotator::ZeroRotator;

	FTransform Start;
	float Alpha = 0.f;
	float Target = 0.f;
	float Speed = 1.f;
};

/**
 * M01 Black Protocol (Bible §05), running in the Glass Crown map straight after M00. One actor drives the authored
 * beats and puts the world back in the right state after a checkpoint load (QA-03):
 *  A  antechamber lockdown: AION's revocation, HUD glitch (< 0.6 s), alarm, emergency lighting, shutters, doors
 *     sealed, two security drones; troopers turn hostile only after AION re-designates the threat. The emergency
 *     door opens when both drones are down.
 *  B  server artery: intermittent power (flickering lights). Turret reroute / bypass live on their own actors.
 *  C  transit shaft: the service lift fails mid-descent (three beats: jolt, plunge, brake), then assisted grabs.
 *  D  medical reclamation: surgical rigs strip the cyberware one system at a time; health left low; the damaged
 *     agency tag becomes collectable.
 *  E  waste conduit: ammunition cut to a few rounds for the stealth escape (troopers are placed hostile).
 *  F  spillway: a plain objective trigger ends the mission.
 */
UCLASS()
class NEONVEIL_API ANVBlackProtocolDirector : public AActor
{
	GENERATED_BODY()

public:
	ANVBlackProtocolDirector();
	virtual void Tick(float DeltaSeconds) override;

	// ----- A: lockdown
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "A Lockdown")
	TArray<FNVSubtitleLine> RevocationLines;
	/** AION re-designates the threat; troopers turn. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "A Lockdown")
	TArray<FNVSubtitleLine> DesignationLines;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "A Lockdown")
	TArray<FNVSubtitleLine> DoorOpenLines;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "A Lockdown")
	TArray<TObjectPtr<ALight>> LightsToAlarm;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "A Lockdown")
	FLinearColor AlarmColor = FLinearColor(1.f, 0.08f, 0.05f);
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "A Lockdown")
	float AlarmIntensityScale = 0.55f;
	/** Off until the lockdown (emergency strips, rotating beacons). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "A Lockdown")
	TArray<TObjectPtr<ALight>> EmergencyLights;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "A Lockdown")
	TArray<FNVMover> Shutters;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "A Lockdown")
	TArray<TObjectPtr<ANVObjectiveDoor>> DoorsToSeal;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "A Lockdown")
	TArray<TObjectPtr<ANVSecurityDrone>> LockdownDrones;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "A Lockdown")
	TObjectPtr<ANVObjectiveDoor> EmergencyDoor;
	/** Troopers that come in after the re-designation (placed out of sight, made hostile and alerted). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "A Lockdown")
	TArray<TObjectPtr<ANVGuardCharacter>> LockdownTroopers;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "A Lockdown")
	TObjectPtr<ANVObjectiveDoor> TrooperDoor;
	/** Every M00 citizen/guard in the tower that should turn on him once re-designated (they were friendly). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "A Lockdown")
	TArray<TObjectPtr<ANVGuardCharacter>> GuardsToTurn;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "A Lockdown")
	float DesignationDelay = 14.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "A Lockdown")
	TObjectPtr<USoundBase> AlarmSound;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "A Lockdown")
	TObjectPtr<USoundBase> GlitchSound;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "A Lockdown")
	TObjectPtr<USoundBase> ShutterSound;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "A Lockdown")
	TObjectPtr<USoundBase> CombatMusic;

	// ----- B: artery
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "B Artery")
	TArray<TObjectPtr<ALight>> FlickerLights;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "B Artery")
	TObjectPtr<ANVSentryTurret> ArteryTurret;

	// ----- C: shaft
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "C Shaft")
	TObjectPtr<AActor> LiftCab;
	/** Cab parts that move with it (walls, floor, lights) are attached to LiftCab in the level. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "C Shaft")
	FNVMover LiftGate;
	/** Panel that blows out at the brake so he can get to the maintenance ledge. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "C Shaft")
	TObjectPtr<AActor> LiftHatch;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "C Shaft")
	float LiftCruiseDrop = 1300.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "C Shaft")
	float LiftPlungeDrop = 1500.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "C Shaft")
	TArray<FNVSubtitleLine> LiftLines;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "C Shaft")
	TObjectPtr<USoundBase> LiftJoltSound;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "C Shaft")
	TObjectPtr<USoundBase> LiftBrakeSound;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "C Shaft")
	TObjectPtr<UNiagaraSystem> SparksFX;

	// ----- D: reclamation
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "D Reclamation")
	TArray<FNVMover> SurgicalArms;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "D Reclamation")
	TObjectPtr<ANVObjectiveDoor> SuiteDoor;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "D Reclamation")
	TArray<TObjectPtr<ALight>> SuiteLights;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "D Reclamation")
	TObjectPtr<ANVInteractableActor> AgencyTag;
	/** Played across the stripping, one group per system (AION clinical, Ghost-7 in pain). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "D Reclamation")
	TArray<FNVSubtitleLine> ReclamationLines;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "D Reclamation")
	TArray<FNVSubtitleLine> RecoveryLines;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "D Reclamation")
	float HealthAfter = 35.f;
	/** First system goes offline after AION's opening line; then one every StripInterval (match the VO). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "D Reclamation")
	float FirstStripDelay = 5.9f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "D Reclamation")
	float StripInterval = 2.9f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "D Reclamation")
	TObjectPtr<USoundBase> ImplantSound;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "D Reclamation")
	TObjectPtr<USoundBase> PowerFaultSound;

	// ----- E: conduit
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "E Conduit")
	int32 ConduitMagAmmo = 6;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "E Conduit")
	int32 ConduitReserveAmmo = 6;

protected:
	virtual void BeginPlay() override;

private:
	UFUNCTION()
	void HandleObjectiveActivated(FName ObjectiveID);
	UFUNCTION()
	void HandleObjectiveCompleted(FName ObjectiveID);
	UFUNCTION()
	void HandleGameplayEvent(FGameplayTag EventTag);

	void ApplyRestoredState();
	void StartLockdown();
	void ApplyLockdownWorld(bool bInstant);
	void Designate(bool bInstant);
	void CheckDrones();
	void StartLift();
	void StartReclamation();
	void StripNext();
	void FinishReclamation();
	void CutAmmo();
	void Say(const TArray<FNVSubtitleLine>& Lines);
	void GlitchHUD(float Seconds);
	void InitMovers(TArray<FNVMover>& Movers);
	void InitMover(FNVMover& M);
	void TickMovers(TArray<FNVMover>& Movers, float Dt);
	void TickMover(FNVMover& M, float Dt);
	static void SetMovers(TArray<FNVMover>& Movers, float Target, float Speed, bool bInstant);
	static void SetMover(FNVMover& M, float Target, float Speed, bool bInstant);
	bool IsM01Running() const;
	bool IsDone(const TCHAR* ObjectiveID) const;

	bool bLockdownStarted = false;
	bool bDesignated = false;
	bool bEmergencyOpen = false;
	bool bLiftStarted = false;
	bool bReclaimStarted = false;
	FTimerHandle SeqTimer;
	FTimerHandle DesignateTimer;
	FTimerHandle GlitchTimer;
	float NextFlicker = 0.f;
	// lift
	int32 LiftPhase = 0;   // 0 idle, 1 gate closing, 2 cruise, 3 jolt hold, 4 plunge, 5 braked
	float LiftTime = 0.f;
	float LiftVel = 0.f;
	FVector LiftStart = FVector::ZeroVector;
	float LiftTravelled = 0.f;
	// reclamation
	int32 StripIndex = 0;
	UPROPERTY(Transient)
	TObjectPtr<UAudioComponent> Alarm;
	TMap<TWeakObjectPtr<ALight>, float> BaseIntensity;
};
