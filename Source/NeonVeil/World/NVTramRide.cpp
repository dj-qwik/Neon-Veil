#include "World/NVTramRide.h"

#include "Components/AudioComponent.h"
#include "Sound/AmbientSound.h"
#include "Components/BoxComponent.h"
#include "Components/SplineComponent.h"
#include "Components/SplineMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Kismet/GameplayStatics.h"
#include "Objectives/NVObjectiveSubsystem.h"
#include "NeonVeil.h"

ANVTramRide::ANVTramRide()
{
	PrimaryActorTick.bCanEverTick = true;
	PrimaryActorTick.TickGroup = TG_PrePhysics;

	Path = CreateDefaultSubobject<USplineComponent>(TEXT("Path"));
	SetRootComponent(Path);
	Path->SetMobility(EComponentMobility::Static);

	RideAudio = CreateDefaultSubobject<UAudioComponent>(TEXT("RideAudio"));
	RideAudio->SetupAttachment(Path);
	RideAudio->bAutoActivate = false;
	RideAudio->bAllowSpatialization = false;

	MusicAudio = CreateDefaultSubobject<UAudioComponent>(TEXT("MusicAudio"));
	MusicAudio->SetupAttachment(Path);
	MusicAudio->bAutoActivate = false;
	MusicAudio->bAllowSpatialization = false;
	MusicAudio->bIsMusic = true;
}

float ANVTramRide::GetPathLength() const
{
	return Path ? Path->GetSplineLength() : 0.f;
}

float ANVTramRide::GetRideDuration() const
{
	const float L = GetPathLength();
	const float D = FMath::Min(DecelDistance, L);
	return (L - D) / StartSpeed + 2.f * D / StartSpeed;
}

float ANVTramRide::DistanceAt(float T) const
{
	const float L = GetPathLength();
	const float D = FMath::Min(DecelDistance, L);
	const float V0 = StartSpeed;
	const float T1 = (L - D) / V0;
	const float T2 = 2.f * D / V0;
	if (T <= T1)
	{
		return V0 * T;
	}
	const float U = T - T1;
	if (U >= T2)
	{
		return L;
	}
	// uniform braking from V0 to 0 over D
	return (L - D) + V0 * U - 0.5f * (V0 / T2) * U * U;
}

void ANVTramRide::OnConstruction(const FTransform& Transform)
{
	Super::OnConstruction(Transform);
	BuildTrack();
}

void ANVTramRide::BuildTrack()
{
	if (!Path)
	{
		return;
	}
	const float L = Path->GetSplineLength();
	if (L <= 1.f)
	{
		return;
	}

	// rail beam: one spline-mesh segment per RailSegment, following the path's turns
	if (RailMesh)
	{
		const int32 N = FMath::Max(1, FMath::RoundToInt(L / RailSegment));
		const float Seg = L / N;
		for (int32 i = 0; i < N; ++i)
		{
			const float D0 = Seg * i;
			const float D1 = Seg * (i + 1);
			USplineMeshComponent* SMC = NewObject<USplineMeshComponent>(this, NAME_None, RF_Transactional);
			SMC->CreationMethod = EComponentCreationMethod::UserConstructionScript;
			SMC->SetMobility(EComponentMobility::Static);
			SMC->SetStaticMesh(RailMesh);
			SMC->SetupAttachment(Path);
			const FVector Z(0.f, 0.f, RailZ);
			const FVector P0 = Path->GetLocationAtDistanceAlongSpline(D0, ESplineCoordinateSpace::Local) + Z;
			const FVector P1 = Path->GetLocationAtDistanceAlongSpline(D1, ESplineCoordinateSpace::Local) + Z;
			const FVector T0 = Path->GetTangentAtDistanceAlongSpline(D0, ESplineCoordinateSpace::Local).GetSafeNormal() * Seg;
			const FVector T1 = Path->GetTangentAtDistanceAlongSpline(D1, ESplineCoordinateSpace::Local).GetSafeNormal() * Seg;
			SMC->SetStartAndEnd(P0, T0, P1, T1, false);
			SMC->RegisterComponent();
			AddInstanceComponent(SMC);
		}
	}

	// support pylons down into the city
	if (PylonMesh && PylonSpacing > 100.f)
	{
		for (float D = PylonSkipStart; D <= L - PylonSkipEnd; D += PylonSpacing)
		{
			const FVector Top = Path->GetLocationAtDistanceAlongSpline(D, ESplineCoordinateSpace::World) + FVector(0.f, 0.f, RailZ - 60.f);
			const float H = Top.Z - PylonBottomZ;
			if (H <= 100.f)
			{
				continue;
			}
			UStaticMeshComponent* P = NewObject<UStaticMeshComponent>(this, NAME_None, RF_Transactional);
			P->CreationMethod = EComponentCreationMethod::UserConstructionScript;
			P->SetMobility(EComponentMobility::Static);
			P->SetStaticMesh(PylonMesh);
			if (PylonMaterial)
			{
				P->SetMaterial(0, PylonMaterial);
			}
			P->SetupAttachment(Path);
			const FBoxSphereBounds B = PylonMesh->GetBounds();
			const float MeshH = FMath::Max(1.f, B.BoxExtent.Z * 2.f);
			P->SetWorldLocation(FVector(Top.X, Top.Y, Top.Z - H * 0.5f) - FVector(0.f, 0.f, B.Origin.Z * (H / MeshH)));
			const float Yaw = Path->GetRotationAtDistanceAlongSpline(D, ESplineCoordinateSpace::World).Yaw;
			P->SetWorldRotation(FRotator(0.f, Yaw, 0.f));
			P->SetWorldScale3D(FVector(120.f / FMath::Max(1.f, B.BoxExtent.X * 2.f), 120.f / FMath::Max(1.f, B.BoxExtent.Y * 2.f), H / MeshH));
			P->RegisterComponent();
			AddInstanceComponent(P);
		}
	}
}

void ANVTramRide::BeginPlay()
{
	Super::BeginPlay();
	// path points set from script after spawning never re-ran construction: build the track now if it is missing
	TArray<USplineMeshComponent*> Existing;
	GetComponents(Existing);
	if (Existing.Num() == 0)
	{
		BuildTrack();
	}
	if (!Tram)
	{
		UE_LOG(LogNeonVeil, Warning, TEXT("%s: no tram assigned"), *GetName());
		SetActorTickEnabled(false);
		return;
	}
	TArray<UActorComponent*> Comps;
	Tram->GetComponents(Comps);
	for (UActorComponent* C : Comps)
	{
		if (USceneComponent* SC = Cast<USceneComponent>(C))
		{
			SC->SetMobility(EComponentMobility::Movable);
		}
		if (UBoxComponent* Box = Cast<UBoxComponent>(C))
		{
			// the BP's own proximity door logic is replaced by this ride
			Box->SetCollisionEnabled(ECollisionEnabled::NoCollision);
			Box->SetGenerateOverlapEvents(false);
		}
		else if (UStaticMeshComponent* SM = Cast<UStaticMeshComponent>(C))
		{
			const FString Name = SM->GetName();
			if (Name.Contains(TEXT("Door")))
			{
				FLeaf Leaf;
				Leaf.Comp = SM;
				Leaf.ClosedRel = SM->GetRelativeLocation();
				Leaf.Sign = Name.Contains(TEXT("Left")) ? 1.f : -1.f;
				if (bFlipDoorDirection)
				{
					Leaf.Sign = -Leaf.Sign;
				}
				if (DockDoorSide == 0.f || FMath::Sign(Leaf.ClosedRel.Y) == FMath::Sign(DockDoorSide))
				{
					Leaves.Add(Leaf);
				}
			}
		}
	}
	SetDoorAlpha(0.f);
	// Park at the path start before the pawn spawns: the PlayerStart sits inside the tram there.
	PlaceTram(0.f);
	UE_LOG(LogNeonVeil, Log, TEXT("%s: path %.0f cm, ride %.1f s, %d dock-side door leaves"), *GetName(), GetPathLength(), GetRideDuration(), Leaves.Num());
}

void ANVTramRide::PlaceTram(float Dist)
{
	if (!Tram || !Path)
	{
		return;
	}
	const FVector Loc = Path->GetLocationAtDistanceAlongSpline(Dist, ESplineCoordinateSpace::World);
	const float Yaw = Path->GetRotationAtDistanceAlongSpline(Dist, ESplineCoordinateSpace::World).Yaw + TramYawOffset;
	// no teleport: the rider is carried by CharacterMovement's based movement (position and yaw)
	Tram->SetActorLocationAndRotation(Loc, FRotator(0.f, Yaw, 0.f), false, nullptr, ETeleportType::None);
}

void ANVTramRide::SetDoorAlpha(float Alpha)
{
	const float S = FMath::SmoothStep(0.f, 1.f, FMath::Clamp(Alpha, 0.f, 1.f));
	for (const FLeaf& Leaf : Leaves)
	{
		if (UStaticMeshComponent* C = Leaf.Comp.Get())
		{
			C->SetRelativeLocation(Leaf.ClosedRel + FVector(Leaf.Sign * DoorSlide * S, 0.f, 0.f));
		}
	}
}

void ANVTramRide::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	const float Dt = FMath::Min(DeltaSeconds, 0.1f);
	PhaseTime += Dt;

	switch (Phase)
	{
	case EPhase::Check:
	{
		ACharacter* Player = Cast<ACharacter>(UGameplayStatics::GetPlayerPawn(this, 0));
		if (!Player || (!Player->GetCharacterMovement()->IsMovingOnGround() && PhaseTime < 2.f))
		{
			return; // wait until the pawn exists and stands on the tram floor
		}
		const FVector Local = Tram->GetActorTransform().InverseTransformPosition(Player->GetActorLocation());
		if (FMath::Abs(Local.X) > CabinExtent.X || FMath::Abs(Local.Y) > CabinExtent.Y || FMath::Abs(Local.Z) > CabinExtent.Z)
		{
			UE_LOG(LogNeonVeil, Log, TEXT("%s: player not aboard, tram parked at the dock"), *GetName());
			PlaceTram(GetPathLength());
			SetDoorAlpha(1.f);
			if (AAmbientSound* Bed = Cast<AAmbientSound>(BedAfterDock))
			{
				Bed->GetAudioComponent()->Play();
			}
			Phase = EPhase::Done;
			SetActorTickEnabled(false);
			return;
		}
		Rider = Player;
		// the rider's movement must update after the tram moves each frame (no shudder)
		Player->GetCharacterMovement()->AddTickPrerequisiteActor(this);
		Phase = EPhase::Settle;
		PhaseTime = 0.f;
		SteadyFrames = 0;
		LastRealTime = FPlatformTime::Seconds();
		return;
	}
	case EPhase::Settle:
	{
		// level-load hitches would otherwise eat the first metres of the ride
		const double Now = FPlatformTime::Seconds();
		const float RealStep = static_cast<float>(Now - LastRealTime);
		LastRealTime = Now;
		SteadyFrames = RealStep < 0.1f ? SteadyFrames + 1 : 0;
		// short: the player arrives from the station tunnel already moving, a long hold would read as a stop
		if (SteadyFrames < 3 && PhaseTime < 0.4f)
		{
			return;
		}
		Phase = EPhase::Riding;
		PhaseTime = 0.f;
		if (RideSound)
		{
			RideAudio->SetSound(RideSound);
			RideAudio->Play();
		}
		if (Music)
		{
			MusicAudio->SetSound(Music);
			MusicAudio->SetVolumeMultiplier(MusicVolume);
			MusicAudio->FadeIn(1.5f, MusicVolume, MusicStartTime);
		}
		UE_LOG(LogNeonVeil, Log, TEXT("%s: ride started (%.0f cm, %.1f s)"), *GetName(), GetPathLength(), GetRideDuration());
		return;
	}
	case EPhase::Riding:
	{
		const float L = GetPathLength();
		const float D = DistanceAt(PhaseTime);
		PlaceTram(D);
		const float Speed = (DistanceAt(PhaseTime + 0.05f) - D) / 0.05f;
		RideAudio->SetVolumeMultiplier(FMath::Clamp(0.25f + 0.75f * Speed / StartSpeed, 0.f, 1.f));
		RideAudio->SetPitchMultiplier(FMath::Lerp(0.8f, 1.f, FMath::Clamp(Speed / StartSpeed, 0.f, 1.f)));
		if (D >= L)
		{
			RideAudio->FadeOut(0.6f, 0.f);
			if (DockSound)
			{
				UGameplayStatics::PlaySound2D(this, DockSound);
			}
			if (ACharacter* C = Cast<ACharacter>(Rider.Get()))
			{
				C->GetCharacterMovement()->RemoveTickPrerequisiteActor(this);
			}
			Phase = EPhase::Docked;
			PhaseTime = 0.f;
			UE_LOG(LogNeonVeil, Log, TEXT("%s: docked"), *GetName());
		}
		return;
	}
	case EPhase::Docked:
		if (PhaseTime >= DoorDelay)
		{
			if (DoorSound)
			{
				UGameplayStatics::PlaySound2D(this, DoorSound);
			}
			Phase = EPhase::Opening;
			PhaseTime = 0.f;
		}
		return;
	case EPhase::Opening:
		SetDoorAlpha(PhaseTime / DoorTime);
		if (PhaseTime >= DoorTime)
		{
			if (MusicAudio->IsPlaying())
			{
				MusicAudio->FadeOut(MusicFadeOut, 0.f);
			}
			if (AAmbientSound* Bed = Cast<AAmbientSound>(BedAfterDock))
			{
				Bed->GetAudioComponent()->FadeIn(MusicFadeOut);
			}
			if (DockedEventTag.IsValid())
			{
				if (UNVObjectiveSubsystem* Obj = UNVObjectiveSubsystem::Get(this))
				{
					Obj->SendEvent(DockedEventTag);
				}
			}
			Phase = EPhase::Done;
			UE_LOG(LogNeonVeil, Log, TEXT("%s: doors open"), *GetName());
		}
		return;
	default:
		// keep ticking only while the music fades
		if (!MusicAudio->IsPlaying())
		{
			SetActorTickEnabled(false);
		}
		return;
	}
}
