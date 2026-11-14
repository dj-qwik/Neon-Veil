#include "World/NVElevator.h"

#include "Components/AudioComponent.h"
#include "Components/BoxComponent.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Kismet/GameplayStatics.h"
#include "Objectives/NVObjectiveSubsystem.h"
#include "NeonVeil.h"

ANVElevator::ANVElevator()
{
	PrimaryActorTick.bCanEverTick = true;
	PrimaryActorTick.TickGroup = TG_PrePhysics;

	USceneComponent* Root = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
	SetRootComponent(Root);
	CabVolume = CreateDefaultSubobject<UBoxComponent>(TEXT("CabVolume"));
	CabVolume->SetupAttachment(Root);
	CabVolume->SetBoxExtent(FVector(130.f, 130.f, 120.f));
	CabVolume->SetRelativeLocation(FVector(0.f, 0.f, 120.f));
	CabVolume->SetCollisionProfileName(TEXT("OverlapAllDynamic"));
	CabVolume->SetGenerateOverlapEvents(true);
	RideAudio = CreateDefaultSubobject<UAudioComponent>(TEXT("RideAudio"));
	RideAudio->SetupAttachment(Root);
	RideAudio->bAutoActivate = false;
}

void ANVElevator::BeginPlay()
{
	Super::BeginPlay();
	CabHome.Reset();
	for (AActor* P : CabParts)
	{
		CabHome.Add(P ? P->GetActorLocation() : FVector::ZeroVector);
	}
	LowerClosed.Reset();
	for (AActor* D : LowerDoors)
	{
		LowerClosed.Add(D ? D->GetActorLocation() : FVector::ZeroVector);
	}
	UpperClosed.Reset();
	for (AActor* D : UpperDoors)
	{
		UpperClosed.Add(D ? D->GetActorLocation() : FVector::ZeroVector);
	}
	SetDoors(LowerDoors, LowerClosed, LowerDoorOpenOffsets, 1.f, FVector::ZeroVector);
	SetDoors(UpperDoors, UpperClosed, UpperDoorOpenOffsets, 0.f, FVector::ZeroVector);
	SetCabAlpha(0.f);
}

void ANVElevator::SetCabAlpha(float Alpha)
{
	CabAlpha = Alpha;
	const FVector Offset = Travel * Alpha;
	for (int32 i = 0; i < CabParts.Num() && i < CabHome.Num(); ++i)
	{
		if (AActor* P = CabParts[i])
		{
			P->SetActorLocation(CabHome[i] + Offset, false, nullptr, ETeleportType::None);
		}
	}
}

void ANVElevator::SetDoors(const TArray<TObjectPtr<AActor>>& Doors, const TArray<FVector>& Closed, const TArray<FVector>& Offsets, float OpenAlpha, const FVector& Carry)
{
	const float S = FMath::SmoothStep(0.f, 1.f, FMath::Clamp(OpenAlpha, 0.f, 1.f));
	for (int32 i = 0; i < Doors.Num() && i < Closed.Num(); ++i)
	{
		if (AActor* D = Doors[i])
		{
			const FVector Open = Offsets.IsValidIndex(i) ? Offsets[i] : FVector::ZeroVector;
			D->SetActorLocation(Closed[i] + Carry + Open * S, false, nullptr, ETeleportType::TeleportPhysics);
		}
	}
}

bool ANVElevator::PlayerInCab(APawn*& OutPawn) const
{
	OutPawn = UGameplayStatics::GetPlayerPawn(this, 0);
	return OutPawn && CabVolume->IsOverlappingActor(OutPawn);
}

void ANVElevator::PlayAt(USoundBase* Sound) const
{
	if (Sound)
	{
		UGameplayStatics::PlaySoundAtLocation(this, Sound, GetActorLocation() + Travel * CabAlpha + FVector(0.f, 0.f, 150.f));
	}
}

void ANVElevator::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	const float Dt = FMath::Min(DeltaSeconds, 0.1f);
	PhaseTime += Dt;

	switch (Phase)
	{
	case EPhase::Waiting:
	{
		APawn* Pawn = nullptr;
		const UNVObjectiveSubsystem* Obj = UNVObjectiveSubsystem::Get(this);
		const bool bArmed = RequiredActiveObjective.IsNone() || (Obj && Obj->IsObjectiveActive(RequiredActiveObjective));
		if (bArmed && PlayerInCab(Pawn))
		{
			InCabTime += Dt;
			if (InCabTime >= StartDelay)
			{
				Rider = Pawn;
				Phase = EPhase::Closing;
				PhaseTime = 0.f;
				PlayAt(DoorSound);
				UE_LOG(LogNeonVeil, Log, TEXT("%s: rider aboard, closing doors"), *GetName());
			}
		}
		else
		{
			InCabTime = 0.f;
		}
		break;
	}
	case EPhase::Closing:
		SetDoors(LowerDoors, LowerClosed, LowerDoorOpenOffsets, 1.f - PhaseTime / DoorTime, FVector::ZeroVector);
		if (PhaseTime >= DoorTime + 0.3f)
		{
			Phase = EPhase::Riding;
			PhaseTime = 0.f;
			// carry the rider after the cab has moved this frame (no shudder; see NVTramArrival)
			if (ACharacter* C = Cast<ACharacter>(Rider.Get()))
			{
				C->GetCharacterMovement()->AddTickPrerequisiteActor(this);
			}
			if (RideSound)
			{
				RideAudio->SetSound(RideSound);
				RideAudio->Play();
			}
		}
		break;
	case EPhase::Riding:
	{
		const float A = FMath::Clamp(PhaseTime / RideTime, 0.f, 1.f);
		// ease in and out, like a real car: gentle start, gentle stop
		SetCabAlpha(FMath::InterpEaseInOut(0.f, 1.f, A, 2.2f));
		RideAudio->SetWorldLocation(GetActorLocation() + Travel * CabAlpha);
		if (A >= 1.f)
		{
			if (ACharacter* C = Cast<ACharacter>(Rider.Get()))
			{
				C->GetCharacterMovement()->RemoveTickPrerequisiteActor(this);
			}
			RideAudio->FadeOut(0.4f, 0.f);
			PlayAt(ArriveSound);
			PlayAt(DoorSound);
			Phase = EPhase::Opening;
			PhaseTime = 0.f;
		}
		break;
	}
	case EPhase::Opening:
		SetDoors(UpperDoors, UpperClosed, UpperDoorOpenOffsets, PhaseTime / DoorTime, FVector::ZeroVector);
		if (PhaseTime >= DoorTime)
		{
			Phase = EPhase::Done;
			SetActorTickEnabled(false);
			if (ArrivedEventTag.IsValid())
			{
				if (UNVObjectiveSubsystem* Obj = UNVObjectiveSubsystem::Get(this))
				{
					Obj->SendEvent(ArrivedEventTag);
				}
			}
			UE_LOG(LogNeonVeil, Log, TEXT("%s: arrived at the upper landing"), *GetName());
		}
		break;
	default:
		break;
	}
}
