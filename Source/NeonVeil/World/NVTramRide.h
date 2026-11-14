#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "GameplayTagContainer.h"
#include "NVTramRide.generated.h"

class USplineComponent;
class USplineMeshComponent;
class UStaticMesh;
class UStaticMeshComponent;
class UMaterialInterface;
class UAudioComponent;
class USoundBase;
class APawn;

/**
 * Continuous tram ride along a spline (prologue hand-off into M00). The player starts standing inside Tram (the
 * Sci-Fi Tram Station BP_Tram); on BeginPlay the tram is placed at the spline start and, once the level has settled,
 * cruises at StartSpeed (matching the speed it left the Veyra Central tunnel with), follows the spline through its
 * turns, brakes uniformly over the last DecelDistance and docks at the spline end. Only the doors on DockDoorSide
 * open. Music plays over the ride. Rails (spline meshes) and support pylons are generated along the path.
 * If the player does not start inside the tram (checkpoint load) the tram is simply parked docked with doors open.
 */
UCLASS()
class NEONVEIL_API ANVTramRide : public AActor
{
	GENERATED_BODY()

public:
	ANVTramRide();

	virtual void OnConstruction(const FTransform& Transform) override;
	virtual void BeginPlay() override;
	virtual void Tick(float DeltaSeconds) override;

	/** The tram actor (BP_Tram). Its origin follows the spline; its +X faces along the path when TramYawOffset is 0. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Ride")
	TObjectPtr<AActor> Tram;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Ride")
	float TramYawOffset = 0.f;

	/** Cruise speed (cm/s) from the first frame: the speed the tram had when it left the station tunnel. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Ride", meta = (ClampMin = "10"))
	float StartSpeed = 1400.f;

	/** Uniform braking over this last stretch of the path. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Ride", meta = (ClampMin = "100"))
	float DecelDistance = 7000.f;

	/** The player counts as aboard when inside this box around the tram origin (tram space). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Ride")
	FVector CabinExtent = FVector(1050.f, 260.f, 350.f);

	/** Tram-local Y sign of the door leaves that open at the dock (+1 / -1; 0 = both sides). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Ride|Doors")
	float DockDoorSide = 1.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Ride|Doors", meta = (ClampMin = "0"))
	float DoorSlide = 70.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Ride|Doors", meta = (ClampMin = "0.1"))
	float DoorTime = 1.2f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Ride|Doors", meta = (ClampMin = "0"))
	float DoorDelay = 0.9f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Ride|Doors")
	bool bFlipDoorDirection = false;

	/** Sent to the objective system when the doors finish opening (optional). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Ride")
	FGameplayTag DockedEventTag;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Ride|Audio")
	TObjectPtr<USoundBase> RideSound;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Ride|Audio")
	TObjectPtr<USoundBase> DockSound;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Ride|Audio")
	TObjectPtr<USoundBase> DoorSound;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Ride|Audio")
	TObjectPtr<USoundBase> Music;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Ride|Audio", meta = (ClampMin = "0"))
	float MusicStartTime = 0.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Ride|Audio", meta = (ClampMin = "0"))
	float MusicVolume = 0.8f;

	/** Music fades out over this many seconds, starting when the doors open. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Ride|Audio", meta = (ClampMin = "0"))
	float MusicFadeOut = 5.f;

	/** Ambient music bed of the destination (auto-activate off): faded in once the doors are open. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Ride|Audio")
	TObjectPtr<AActor> BedAfterDock;

	/** Rail beam deformed along the path (e.g. SM_Monorail_A), offset below the tram origin. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Ride|Track")
	TObjectPtr<UStaticMesh> RailMesh;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Ride|Track")
	float RailZ = -210.f;

	/** Length of one rail segment (the mesh's own length along X). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Ride|Track", meta = (ClampMin = "50"))
	float RailSegment = 800.f;

	/** Support pylons hanging from the rail down to PylonBottomZ (world), every PylonSpacing cm. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Ride|Track")
	TObjectPtr<UStaticMesh> PylonMesh;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Ride|Track")
	TObjectPtr<UMaterialInterface> PylonMaterial;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Ride|Track")
	float PylonSpacing = 4000.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Ride|Track")
	float PylonBottomZ = -9000.f;

	/** No pylons/rails in the first stretch (inside the tunnel portal) or the last one (docking bay). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Ride|Track")
	float PylonSkipStart = 3000.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Ride|Track")
	float PylonSkipEnd = 1500.f;

	UFUNCTION(BlueprintPure, Category = "Ride")
	float GetPathLength() const;

	/** Ride time from start to dock at the configured speeds (seconds). */
	UFUNCTION(BlueprintPure, Category = "Ride")
	float GetRideDuration() const;

protected:
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	TObjectPtr<USplineComponent> Path;

	UPROPERTY(VisibleAnywhere, Category = "Components")
	TObjectPtr<UAudioComponent> RideAudio;

	UPROPERTY(VisibleAnywhere, Category = "Components")
	TObjectPtr<UAudioComponent> MusicAudio;

private:
	struct FLeaf
	{
		TWeakObjectPtr<UStaticMeshComponent> Comp;
		FVector ClosedRel = FVector::ZeroVector;
		float Sign = 1.f;
	};

	void BuildTrack();
	void PlaceTram(float Dist);
	void SetDoorAlpha(float Alpha);
	float DistanceAt(float T) const;

	enum class EPhase : uint8 { Check, Settle, Riding, Docked, Opening, Done };
	EPhase Phase = EPhase::Check;
	TArray<FLeaf> Leaves;
	TWeakObjectPtr<APawn> Rider;
	float PhaseTime = 0.f;
	int32 SteadyFrames = 0;
	double LastRealTime = 0.0;
};
