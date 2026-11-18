#include "World/NVAssistGrab.h"
#include "NeonVeil.h"

#include "Components/ArrowComponent.h"
#include "Components/BoxComponent.h"
#include "Components/CapsuleComponent.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Kismet/GameplayStatics.h"

ANVAssistGrab::ANVAssistGrab()
{
	PrimaryActorTick.bCanEverTick = true;
	Volume = CreateDefaultSubobject<UBoxComponent>(TEXT("Volume"));
	Volume->SetBoxExtent(FVector(150.f, 150.f, 200.f));
	Volume->SetCollisionProfileName(TEXT("Trigger"));
	SetRootComponent(Volume);
	LandPoint = CreateDefaultSubobject<UArrowComponent>(TEXT("LandPoint"));
	LandPoint->SetupAttachment(Volume);
	LandPoint->SetRelativeLocation(FVector(200.f, 0.f, 250.f));
}

void ANVAssistGrab::BeginPlay()
{
	Super::BeginPlay();
}

void ANVAssistGrab::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	if (ACharacter* C = Pulling.Get())
	{
		T += DeltaSeconds / FMath::Max(0.05f, PullTime);
		const float A = FMath::Clamp(T, 0.f, 1.f);
		const FVector To = LandPoint->GetComponentLocation();
		// up first, then over the lip
		const FVector Up(From.X, From.Y, FMath::Max(From.Z, To.Z));
		const FVector P = A < 0.5f ? FMath::Lerp(From, Up, A * 2.f) : FMath::Lerp(Up, To, (A - 0.5f) * 2.f);
		C->SetActorLocation(P, false, nullptr, ETeleportType::TeleportPhysics);
		if (A >= 1.f)
		{
			C->GetCharacterMovement()->SetMovementMode(MOVE_Walking);
			Pulling.Reset();
		}
		return;
	}
	ACharacter* Player = Cast<ACharacter>(UGameplayStatics::GetPlayerPawn(this, 0));
	if (!Player || !Player->GetCharacterMovement()->IsFalling() || !Volume->IsOverlappingActor(Player))
	{
		return;
	}
	UE_LOG(LogNeonVeil, Log, TEXT("%s: assisted grab"), *GetName());
	Pulling = Player;
	From = Player->GetActorLocation();
	T = 0.f;
	Player->GetCharacterMovement()->StopMovementImmediately();
	Player->GetCharacterMovement()->SetMovementMode(MOVE_Flying);
	if (GrabSound)
	{
		UGameplayStatics::PlaySoundAtLocation(this, GrabSound, From);
	}
}
