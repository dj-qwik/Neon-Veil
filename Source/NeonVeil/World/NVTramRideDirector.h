#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "UI/NVSubtitleLine.h"
#include "NVTramRideDirector.generated.h"

class ANVTramRide;
class UStaticMesh;
class UStaticMeshComponent;
class UMaterialInterface;
class UPointLightComponent;
class USpotLightComponent;
class UAudioComponent;
class USoundBase;
class USoundAttenuation;
class UNiagaraSystem;
class UNiagaraComponent;

/** A subtitle / comms line fired at a ride time (seconds since the tram started moving). */
USTRUCT(BlueprintType)
struct FNVTimedLine
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Ride")
	float Time = 0.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Ride")
	FNVSubtitleLine Line;
};

/**
 * Fills the Crown Line ride: timed comms / inner-monologue lines, and a scripted police pursuit that plays out
 * beside the tram so it can't be missed. The pursuit is choreographed in tram space (X along the track, -Y = the
 * left windows, Z up), so it keeps pace with the car whatever its speed: a suspect flyer overtakes on the left,
 * a patrol car drops in beside the windows and holds its spotlight on the cabin, then both pull ahead trading
 * fire until the patrol car is hit, trails smoke and slams into the nearest facade ahead-left in a fireball.
 * Only runs if the ride actually starts with the player aboard (not on a checkpoint load).
 */
UCLASS()
class NEONVEIL_API ANVTramRideDirector : public AActor
{
	GENERATED_BODY()

public:
	ANVTramRideDirector();
	virtual void BeginPlay() override;
	virtual void Tick(float DeltaSeconds) override;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Ride")
	TObjectPtr<ANVTramRide> Ride;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Ride")
	TArray<FNVTimedLine> Lines;

	/** Ride time at which the pursuit begins (the cars come up from behind). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Chase")
	float ChaseStart = 13.f;

	/** +1: the action plays on the tram's left (-Y) windows, -1: on the right. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Chase")
	float Side = 1.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Chase|Look")
	TObjectPtr<UStaticMesh> SuspectMesh;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Chase|Look")
	TObjectPtr<UMaterialInterface> SuspectPaint;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Chase|Look")
	TObjectPtr<UStaticMesh> PoliceMesh;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Chase|Look")
	TObjectPtr<UMaterialInterface> PolicePaint;
	/** Material slot of the hull paint on the hover-car meshes. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Chase|Look")
	int32 PaintSlot = 1;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Chase|Look")
	FVector CarScale = FVector(6.5f, 2.5f, 1.5f);
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Chase|Look")
	TObjectPtr<UStaticMesh> TracerMesh;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Chase|Look")
	TObjectPtr<UMaterialInterface> PoliceTracer;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Chase|Look")
	TObjectPtr<UMaterialInterface> SuspectTracer;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Chase|Look")
	TObjectPtr<UMaterialInterface> LightBarRed;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Chase|Look")
	TObjectPtr<UMaterialInterface> LightBarBlue;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Chase|FX")
	TObjectPtr<UNiagaraSystem> ExplosionFX;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Chase|FX")
	TObjectPtr<UNiagaraSystem> FireFX;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Chase|FX")
	TObjectPtr<UNiagaraSystem> SmokeFX;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Chase|FX")
	TObjectPtr<UNiagaraSystem> SparksFX;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Chase|FX")
	float ExplosionScale = 6.f;

	/** Gunfire: each shot is a short glowing bolt that flies from the shooter's hull toward the other car. Bolts are
	 *  tracked in tram space every frame (muzzle and target follow the cars), so they always leave the gun and land on
	 *  the hull instead of hanging in the air while the convoy moves on. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Chase|Gunfire")
	float BoltSpeed = 15000.f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Chase|Gunfire")
	float BoltLength = 650.f;
	/** Bolt diameter as a scale on the 1 m cylinder. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Chase|Gunfire")
	float BoltThickness = 0.22f;
	/** Chance a shot lands on the hull (sparks); misses streak close past it. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Chase|Gunfire")
	float SuspectAccuracy = 0.65f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Chase|Gunfire")
	float PoliceAccuracy = 0.55f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Chase|Audio")
	TObjectPtr<USoundBase> SirenSound;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Chase|Audio")
	TObjectPtr<USoundBase> EngineSound;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Chase|Audio")
	TArray<TObjectPtr<USoundBase>> ShotSounds;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Chase|Audio")
	TObjectPtr<USoundBase> ExplosionSound;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Chase|Audio")
	TObjectPtr<USoundAttenuation> Attenuation;
	/** Siren loudness (it sits right outside the windows for several seconds). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Chase|Audio")
	float SirenVolume = 0.4f;
	/** Siren pitch at the moment of impact: it winds down / detunes from 1 to this while the car tumbles. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Chase|Audio")
	float SirenDyingPitch = 0.42f;
	/** Pre-rendered wind-down of the siren (pitch sagging + warble over the tumble). Replaces the loop at the hit;
	 *  without it the live loop is pitched down instead. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Chase|Audio")
	TObjectPtr<USoundBase> SirenDyingSound;
	/** Big layered blast (2D, through the cabin) and the follow-up cook-off explosions. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Chase|Audio")
	TObjectPtr<USoundBase> BigExplosionSound;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Chase|Audio")
	TObjectPtr<USoundBase> SecondaryExplosionSound;
	/** Sub-bass impact on the moment of the explosion. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Chase|Audio")
	TObjectPtr<USoundBase> BassHitSound;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Chase|Audio")
	float BassHitVolume = 1.6f;
	/** Camera trauma at the explosion (0..1.6); the hit on the patrol car gets a small kick too. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Chase|FX")
	float BlastShake = 1.1f;

private:
	struct FKey { float T; FVector P; };
	UStaticMeshComponent* MakeCar(const TCHAR* Name, UStaticMesh* Mesh, UMaterialInterface* Paint, FLinearColor Glow);
	FVector TramLocal(const FVector& L) const;
	static FVector Sample(const TArray<FKey>& Keys, float T);
	void UpdateFrame(float Dt);
	void PlaceCar(UStaticMeshComponent* Car, const FVector& World, float Dt, FVector& PrevWorld, float Roll);
	void FireShot(bool bPolice);
	void UpdateBolts(float Dt);
	FVector Muzzle(const UStaticMeshComponent* Shooter, const FVector& Dir) const;

	struct FBolt { bool bPolice = false; bool bHit = true; float Age = 0.f; float Flight = 0.1f; FVector AimOfs = FVector::ZeroVector; int32 Tracer = -1; };
	TArray<FBolt> Bolts;
	float MuzzleAge[2] = { 1.f, 1.f };
	void Explode(const FVector& At);
	void SayLine(const FNVSubtitleLine& Line);
	void SecondaryBlast(const FVector& At, float Scale, bool bLoud);

	struct FPendingBlast { float Due; FVector At; float Scale; bool bLoud; };
	TArray<FPendingBlast> PendingBlasts;
	float NextSparkBurst = 0.f;
	float ExplodeClock = 0.f;
	bool bCookOffsPlaying = false;

	UPROPERTY(Transient) TObjectPtr<UStaticMeshComponent> Suspect;
	UPROPERTY(Transient) TObjectPtr<UStaticMeshComponent> Police;
	UPROPERTY(Transient) TObjectPtr<UStaticMeshComponent> BarRed;
	UPROPERTY(Transient) TObjectPtr<UStaticMeshComponent> BarBlue;
	UPROPERTY(Transient) TObjectPtr<UPointLightComponent> FlashRed;
	UPROPERTY(Transient) TObjectPtr<UPointLightComponent> FlashBlue;
	UPROPERTY(Transient) TObjectPtr<USpotLightComponent> Spot;
	UPROPERTY(Transient) TObjectPtr<UPointLightComponent> BlastLight;
	UPROPERTY(Transient) TObjectPtr<UAudioComponent> Siren;
	UPROPERTY(Transient) TObjectPtr<UAudioComponent> SirenDying;
	UPROPERTY(Transient) TObjectPtr<UAudioComponent> SuspectEngine;
	UPROPERTY(Transient) TObjectPtr<UNiagaraComponent> SmokeTrail;
	UPROPERTY(Transient) TArray<TObjectPtr<UStaticMeshComponent>> Tracers;
	TArray<bool> TracerBusy;
	UPROPERTY(Transient) TObjectPtr<UPointLightComponent> MuzzleSuspect;
	UPROPERTY(Transient) TObjectPtr<UPointLightComponent> MuzzlePolice;
	int32 SuspectBurst = 0;

	TArray<FKey> SuspectKeys;
	TArray<FKey> PoliceKeys;
	int32 NextLine = 0;
	bool bStarted = false;
	bool bHit = false;
	bool bExploded = false;
	float LastRideTime = -1.f;
	float NextSuspectShot = 0.f;
	float NextPoliceShot = 0.f;
	int32 PoliceBurst = 0;
	float BlastAge = -1.f;
	FVector CrashFrom = FVector::ZeroVector;
	FVector CrashTo = FVector::ZeroVector;
	FVector SuspectPrev = FVector::ZeroVector;
	FVector PolicePrev = FVector::ZeroVector;
	FVector PrevTramLoc = FVector::ZeroVector;
	FVector Fwd = FVector::ForwardVector;
	FVector Right = FVector::RightVector;
	FVector TramLoc = FVector::ZeroVector;
};
