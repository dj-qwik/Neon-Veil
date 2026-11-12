#include "World/NVTramArrival.h"

#include "Components/AudioComponent.h"
#include "Components/BoxComponent.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Kismet/GameplayStatics.h"
#include "NeonVeil.h"

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
	FrontBarrier->SetRelativeLocation(FVector(Offset, 0.f, 0.f) + FVector(0.f, 0.f, 150.f));
	// The rider is carried by CharacterMovement's based movement (the cabin floor is Movable).
	(void)Delta;
}

void ANVTramArrival::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);

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
		const FVector Local = GetActorTransform().InverseTransformPosition(Player->GetActorLocation());
		if (FMath::Abs(Local.X) > CabinExtent.X || FMath::Abs(Local.Y) > CabinExtent.Y || FMath::Abs(Local.Z) > CabinExtent.Z)
		{
			UE_LOG(LogNeonVeil, Log, TEXT("%s: player not in cabin, arrival skipped"), *GetName());
			SetActorTickEnabled(false);
			return;
		}
		Rider = Player;
		bArriving = true;
		bMoving = false;
		SteadyFrames = 0;
		LastOffset = 0.f;
		LastRealTime = FPlatformTime::Seconds();
		FrontBarrier->SetCollisionEnabled(ECollisionEnabled::QueryAndPhysics);
		ApplyOffset(-Distance);   // park out on the line immediately; glide starts once frames are steady
		UE_LOG(LogNeonVeil, Log, TEXT("%s: C00 tram staged %.0f cm out"), *GetName(), Distance);
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
		Rider.Reset();
		FrontBarrier->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		RideAudio->FadeOut(0.5f, 0.f);
		if (DockSound)
		{
			UGameplayStatics::PlaySound2D(this, DockSound);
		}
		SetActorTickEnabled(false);
		UE_LOG(LogNeonVeil, Log, TEXT("%s: docked (wall %.2f s, %d ticks, elapsed %.2f s)"), *GetName(), FPlatformTime::Seconds() - RideStartTime, RideTicks, Elapsed);
	}
}
