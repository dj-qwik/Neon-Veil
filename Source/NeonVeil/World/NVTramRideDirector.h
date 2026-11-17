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

private:
	struct FKey { float T; FVector P; };
	UStaticMeshComponent* MakeCar(const TCHAR* Name, UStaticMesh* Mesh, UMaterialInterface* Paint, FLinearColor Glow);
	FVector TramLocal(const FVector& L) const;
	static FVector Sample(const TArray<FKey>& Keys, float T);
	void UpdateFrame(float Dt);
	void PlaceCar(UStaticMeshComponent* Car, const FVector& World, float Dt, FVector& PrevWorld, float Roll);
	void FireShot(const FVector& From, const FVector& To, bool bPolice);
	void Explode(const FVector& At);
	void SayLine(const FNVSubtitleLine& Line);

	UPROPERTY(Transient) TObjectPtr<UStaticMeshComponent> Suspect;
	UPROPERTY(Transient) TObjectPtr<UStaticMeshComponent> Police;
	UPROPERTY(Transient) TObjectPtr<UStaticMeshComponent> BarRed;
	UPROPERTY(Transient) TObjectPtr<UStaticMeshComponent> BarBlue;
	UPROPERTY(Transient) TObjectPtr<UPointLightComponent> FlashRed;
	UPROPERTY(Transient) TObjectPtr<UPointLightComponent> FlashBlue;
	UPROPERTY(Transient) TObjectPtr<USpotLightComponent> Spot;
	UPROPERTY(Transient) TObjectPtr<UPointLightComponent> BlastLight;
	UPROPERTY(Transient) TObjectPtr<UAudioComponent> Siren;
	UPROPERTY(Transient) TObjectPtr<UAudioComponent> SuspectEngine;
	UPROPERTY(Transient) TObjectPtr<UNiagaraComponent> SmokeTrail;
	UPROPERTY(Transient) TArray<TObjectPtr<UStaticMeshComponent>> Tracers;
	TArray<float> TracerLife;

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
