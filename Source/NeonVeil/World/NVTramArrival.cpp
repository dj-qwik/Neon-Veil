#include "World/NVTramArrival.h"

#include "Components/AudioComponent.h"
#include "Components/BoxComponent.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Kismet/GameplayStatics.h"
#include "NeonVeil.h"
#include "HAL/IConsoleManager.h"

static TAutoConsoleVariable<int32> CVarTramRiderAfterCabin(TEXT("nv.TramRiderAfterCabin"), 1,
	TEXT("1: the rider's movement ticks after the tram cabin moves (no shudder). 0: unordered (A/B test)."));

ANVTramArrival::ANVTramArrival()
{
	PrimaryActorTick.bCanEverTick = true;
	PrimaryActorTick.TickGroup = TG_PrePhysics;

	USceneComponent* Root = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
	SetRootComponent(Root);
	FrontBarrier = CreateDefaultSubobject<UBoxComponent>(TEXT("FrontBarrier"));
	FrontBarrier->SetupAttachment(Root);
	FrontBarrier->SetBoxExtent(FVector(10.f, 300.f, 200.f));
	FrontBarrier->SetCollisionProfileName(TEXT("BlockAllDynamic"));
	FrontBarrier->SetMobility(EComponentMobility::Movable);
	RideAudio = CreateDefaultSubobject<UAudioComponent>(TEXT("RideAudio"));
	RideAudio->SetupAttachment(Root);
	RideAudio->bAutoActivate = false;
}

void ANVTramArrival::BeginPlay()
{
	Super::BeginPlay();
	Home.Reset();
	for (AActor* P : Parts)
	{
		Home.Add(P ? P->GetActorLocation() : FVector::ZeroVector);
	}
	FrontBarrier->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	DoorClosed.Reset();
	for (AActor* D : Doors)
	{
		DoorClosed.Add(D ? D->GetActorLocation() : FVector::ZeroVector);
	}
	SetDoorAlpha(0.f);
	// Park out on the line before the player spawns: the PlayerStart sits inside the parked cabin, so the only
	// movement the rider experiences is the smooth glide (a 100 m one-frame jump is not carried by based movement).
	ApplyOffset(-Distance);
}

void ANVTramArrival::SetDoorAlpha(float Alpha)
{
	DoorAlpha = FMath::Clamp(Alpha, 0.f, 1.f);
	// the leaves ride with the tram (not in Parts) and slide open once docked
	const FVector Ride = GetActorForwardVector() * LastOffset;
	const float S = FMath::SmoothStep(0.f, 1.f, DoorAlpha);
	for (int32 i = 0; i < Doors.Num() && i < DoorClosed.Num(); ++i)
	{
		if (AActor* D = Doors[i])
		{
			const FVector Open = DoorOpenOffsets.IsValidIndex(i) ? DoorOpenOffsets[i] : FVector::ZeroVector;
			D->SetActorLocation(DoorClosed[i] + Ride + Open * S, false, nullptr, ETeleportType::TeleportPhysics);
		}
	}
}

void ANVTramArrival::BeginDoorOpen()
{
	if (Doors.Num() == 0)
	{
		SetActorTickEnabled(false);
		return;
	}
	bDoorOpening = true;
	DoorElapsed = 0.f;
	SetActorTickEnabled(true);
}

void ANVTramArrival::ApplyOffset(float Offset)
{
	const FVector Dir = GetActorForwardVector();
	const float Delta = Offset - LastOffset;
	LastOffset = Offset;
	for (int32 i = 0; i < Parts.Num(); ++i)
	{
		if (AActor* P = Parts[i])
		{
			P->SetActorLocation(Home[i] + Dir * Offset, false, nullptr, ETeleportType::None);
		}
	}
	SetDoorAlpha(DoorAlpha);
	FrontBarrier->SetRelativeLocation(FVector(Offset, 0.f, 0.f) + FVector(0.f, 0.f, 150.f));
	// The rider is carried by CharacterMovement's based movement (the cabin floor is Movable).
	(void)Delta;
}

void ANVTramArrival::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);

	if (bDoorOpening)
	{
		DoorElapsed += FMath::Min(DeltaSeconds, 0.1f);
		const float T = DoorElapsed - DoorDelay;
		if (T >= 0.f && !bDoorSoundPlayed)
		{
			bDoorSoundPlayed = true;
			if (DoorSound && Doors.Num() > 0 && Doors[0])
			{
				UGameplayStatics::PlaySoundAtLocation(this, DoorSound, Doors[0]->GetActorLocation());
			}
		}
		if (T >= 0.f)
		{
			SetDoorAlpha(T / DoorOpenTime);
		}
		if (DoorAlpha >= 1.f)
		{
			bDoorOpening = false;
			SetActorTickEnabled(false);
			UE_LOG(LogNeonVeil, Log, TEXT("%s: tram door open"), *GetName());
		}
		return;
	}

	if (!bChecked)
	{
		bChecked = true;
		ACharacter* Player = Cast<ACharacter>(UGameplayStatics::GetPlayerPawn(this, 0));
		if (!Player || (!Player->GetCharacterMovement()->IsMovingOnGround() && Elapsed < 2.f))
		{
			bChecked = false;   // wait until the pawn exists and stands on the cabin floor
			Elapsed += DeltaSeconds;
			return;
		}
		Elapsed = 0.f;
		// cabin box test against where the tram is parked right now
		const FVector Local = GetActorTransform().InverseTransformPosition(Player->GetActorLocation() - GetActorForwardVector() * LastOffset);
		if (FMath::Abs(Local.X) > CabinExtent.X || FMath::Abs(Local.Y) > CabinExtent.Y || FMath::Abs(Local.Z) > CabinExtent.Z)
		{
			UE_LOG(LogNeonVeil, Log, TEXT("%s: player not in cabin, arrival skipped"), *GetName());
			ApplyOffset(0.f);
			SetDoorAlpha(1.f);
			SetActorTickEnabled(false);
			return;
		}
		Rider = Player;
		// The rider's movement must update after the cabin moves each frame; otherwise the two PrePhysics ticks
		// swap order frame to frame and the rider is carried one frame late, then early (visible shudder).
		if (CVarTramRiderAfterCabin.GetValueOnGameThread() != 0)
		{
			Player->GetCharacterMovement()->AddTickPrerequisiteActor(this);
		}
		bArriving = true;
		bMoving = false;
		SteadyFrames = 0;
		LastRealTime = FPlatformTime::Seconds();
		// With a door, the closed door holds the player in; the invisible barrier is only the fallback.
		FrontBarrier->SetCollisionEnabled(Doors.Num() > 0 ? ECollisionEnabled::NoCollision : ECollisionEnabled::QueryAndPhysics);
		UE_LOG(LogNeonVeil, Log, TEXT("%s: C00 rider aboard, tram %.0f cm out"), *GetName(), Distance);
		return;
	}
	if (!bArriving)
	{
		return;
	}
	const double Now = FPlatformTime::Seconds();
	const float RealStep = static_cast<float>(Now - LastRealTime);
	LastRealTime = Now;
	if (!bMoving)
	{
		// Level start hitches (streaming, shader warm-up) would otherwise eat the opening of the ride.
		SteadyFrames = (RealStep < 0.1f) ? SteadyFrames + 1 : 0;
		if (SteadyFrames < 15)
		{
			return;
		}
		bMoving = true;
		Elapsed = 0.f;
		RideStartTime = Now;
		RideTicks = 0;
		if (RideSound)
		{
			RideAudio->SetSound(RideSound);
			RideAudio->Play();
		}
		UE_LOG(LogNeonVeil, Log, TEXT("%s: C00 arrival started (%.0f cm over %.1f s)"), *GetName(), Distance, Duration);
		return;
	}
	++RideTicks;
	if (Rider.IsValid() && Parts.Num() > 0 && Parts[0])
	{
		// (previous frame, after the rider moved) rider position along the travel axis relative to the cabin: should stay constant while seated/standing
		// world-space rider position relative to the cabin (2D); jitter = max second difference (uneven steps)
		const FVector RelV = Rider->GetActorLocation() - Parts[0]->GetActorLocation();
		const float Rel = FVector::DotProduct(RelV, GetActorForwardVector());
		static FVector P1, P2;
		if (RideTicks <= 2)
		{
			RiderRelMin = RiderRelMax = RiderRelPrev = Rel;
			RiderRelJitter = 0.f;
			P2 = P1 = RelV;
		}
		RiderRelMin = FMath::Min(RiderRelMin, Rel);
		RiderRelMax = FMath::Max(RiderRelMax, Rel);
		RiderRelJitter = FMath::Max(RiderRelJitter, (RelV - 2.f * P1 + P2).Size2D());
		P2 = P1;
		P1 = RelV;
		RiderRelPrev = Rel;
	}
	// Wall-clock steps keep the ride at Duration; a single long hitch is capped so the tram never jumps.
	Elapsed += FMath::Min(RealStep, 0.1f);
	const float A = FMath::Clamp(Elapsed / Duration, 0.f, 1.f);
	// ease-out cubic: fast glide in, gentle stop at the platform
	const float E = 1.f - FMath::Pow(1.f - A, 3.f);
	ApplyOffset(-Distance * (1.f - E));

	RideAudio->SetVolumeMultiplier(FMath::Lerp(1.f, 0.f, FMath::Clamp((A - 0.75f) / 0.25f, 0.f, 1.f)));
	if (A >= 1.f)
	{
		bArriving = false;
		if (ACharacter* C = Cast<ACharacter>(Rider.Get()))
		{
			C->GetCharacterMovement()->RemoveTickPrerequisiteActor(this);
		}
		Rider.Reset();
		FrontBarrier->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		RideAudio->FadeOut(0.5f, 0.f);
		if (DockSound)
		{
			UGameplayStatics::PlaySound2D(this, DockSound);
		}
		BeginDoorOpen();
		UE_LOG(LogNeonVeil, Log, TEXT("%s: rider vs cabin along track: range %.1f cm, max step unevenness %.2f cm"), *GetName(), RiderRelMax - RiderRelMin, RiderRelJitter);
		UE_LOG(LogNeonVeil, Log, TEXT("%s: docked (wall %.2f s, %d ticks, elapsed %.2f s)"), *GetName(), FPlatformTime::Seconds() - RideStartTime, RideTicks, Elapsed);
	}
}
