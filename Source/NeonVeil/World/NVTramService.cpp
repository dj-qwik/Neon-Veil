#include "World/NVTramService.h"

#include "Components/AudioComponent.h"
#include "Components/BoxComponent.h"
#include "Components/StaticMeshComponent.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Kismet/GameplayStatics.h"
#include "Objectives/NVObjectiveSubsystem.h"
#include "NeonVeil.h"

ANVTramService::ANVTramService()
{
	PrimaryActorTick.bCanEverTick = true;
	PrimaryActorTick.TickGroup = TG_PrePhysics;
	USceneComponent* Root = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
	SetRootComponent(Root);
	BoardVolume = CreateDefaultSubobject<UBoxComponent>(TEXT("BoardVolume"));
	BoardVolume->SetupAttachment(Root);
	BoardVolume->SetBoxExtent(FVector(650.f, 170.f, 120.f));
	BoardVolume->SetRelativeLocation(FVector(0.f, 0.f, 130.f));
	BoardVolume->SetCollisionProfileName(TEXT("OverlapAllDynamic"));
	BoardVolume->SetGenerateOverlapEvents(true);
	RunAudio = CreateDefaultSubobject<UAudioComponent>(TEXT("RunAudio"));
	RunAudio->SetupAttachment(Root);
	RunAudio->bAutoActivate = false;
}

void ANVTramService::BeginPlay()
{
	Super::BeginPlay();
	if (!Tram)
	{
		UE_LOG(LogNeonVeil, Warning, TEXT("%s: no tram assigned"), *GetName());
		SetActorTickEnabled(false);
		return;
	}
	TramHome = Tram->GetActorLocation();
	TArray<UActorComponent*> Comps;
	Tram->GetComponents(Comps);
	for (UActorComponent* C : Comps)
	{
		if (USceneComponent* SC = Cast<USceneComponent>(C))
		{
			SC->SetMobility(EComponentMobility::Movable);
		}
		const FString Name = C->GetName();
		if (UBoxComponent* Box = Cast<UBoxComponent>(C))
		{
			// the BP's own proximity door logic: replaced by this service
			Box->SetCollisionEnabled(ECollisionEnabled::NoCollision);
			Box->SetGenerateOverlapEvents(false);
		}
		else if (UStaticMeshComponent* SM = Cast<UStaticMeshComponent>(C))
		{
			if (Name.Contains(TEXT("Door")))
			{
				FDoorLeaf L;
				L.Comp = SM;
				L.ClosedRel = SM->GetRelativeLocation();
				L.Sign = Name.Contains(TEXT("Left")) ? 1.f : -1.f;
				if (bFlipDoorDirection)
				{
					L.Sign = -L.Sign;
				}
				Leaves.Add(L);
			}
		}
	}
	SetDoorAlpha(0.f);
	SetOffset(-ArriveDistance);
	Tram->SetActorHiddenInGame(true);
	UE_LOG(LogNeonVeil, Log, TEXT("%s: tram parked %.0f cm out, %d door leaves"), *GetName(), ArriveDistance, Leaves.Num());
}

void ANVTramService::SetOffset(float NewOffset)
{
	Offset = NewOffset;
	if (Tram)
	{
		Tram->SetActorLocation(TramHome + GetActorForwardVector() * Offset, false, nullptr, ETeleportType::None);
	}
}

void ANVTramService::SetDoorAlpha(float Alpha)
{
	const float S = FMath::SmoothStep(0.f, 1.f, FMath::Clamp(Alpha, 0.f, 1.f));
	for (const FDoorLeaf& L : Leaves)
	{
		if (UStaticMeshComponent* C = L.Comp.Get())
		{
			C->SetRelativeLocation(L.ClosedRel + FVector(L.Sign * DoorSlide * S, 0.f, 0.f));
		}
	}
}

void ANVTramService::PlayAtTram(USoundBase* Sound) const
{
	if (Sound && Tram)
	{
		UGameplayStatics::PlaySoundAtLocation(this, Sound, Tram->GetActorLocation() + FVector(0.f, 0.f, 150.f));
	}
}

void ANVTramService::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	const float Dt = FMath::Min(DeltaSeconds, 0.1f);
	PhaseTime += Dt;
	UNVObjectiveSubsystem* Obj = UNVObjectiveSubsystem::Get(this);

	switch (Phase)
	{
	case EPhase::Away:
		if (ArriveOnObjective.IsNone() || (Obj && Obj->IsObjectiveActive(ArriveOnObjective)))
		{
			Phase = EPhase::Arriving;
			PhaseTime = 0.f;
			Tram->SetActorHiddenInGame(false);
			if (RunSound)
			{
				RunAudio->SetSound(RunSound);
				RunAudio->Play();
			}
			if (ArrivalAnnouncement)
			{
				UGameplayStatics::PlaySound2D(this, ArrivalAnnouncement);
			}
			UE_LOG(LogNeonVeil, Log, TEXT("%s: tram arriving"), *GetName());
		}
		break;
	case EPhase::Arriving:
	{
		const float A = FMath::Clamp(PhaseTime / ArriveTime, 0.f, 1.f);
		const float E = 1.f - FMath::Pow(1.f - A, 3.f); // ease-out: glides in, settles at the platform
		SetOffset(-ArriveDistance * (1.f - E));
		RunAudio->SetWorldLocation(Tram->GetActorLocation());
		RunAudio->SetVolumeMultiplier(FMath::Lerp(1.f, 0.f, FMath::Clamp((A - 0.7f) / 0.3f, 0.f, 1.f)));
		if (A >= 1.f)
		{
			RunAudio->Stop();
			PlayAtTram(DockSound);
			PlayAtTram(DoorSound);
			Phase = EPhase::Opening;
			PhaseTime = 0.f;
		}
		break;
	}
	case EPhase::Opening:
		SetDoorAlpha(PhaseTime / DoorTime);
		if (PhaseTime >= DoorTime)
		{
			Phase = EPhase::Boarding;
			PhaseTime = 0.f;
			UE_LOG(LogNeonVeil, Log, TEXT("%s: doors open, boarding"), *GetName());
		}
		break;
	case EPhase::Boarding:
	{
		APawn* P = UGameplayStatics::GetPlayerPawn(this, 0);
		const bool bAboard = P && BoardVolume->IsOverlappingActor(P);
		AboardTime = bAboard ? AboardTime + Dt : 0.f;
		if (AboardTime >= BoardDelay)
		{
			Rider = P;
			PlayAtTram(DoorSound);
			Phase = EPhase::Closing;
			PhaseTime = 0.f;
		}
		break;
	}
	case EPhase::Closing:
		SetDoorAlpha(1.f - PhaseTime / DoorTime);
		if (PhaseTime >= DoorTime + 0.8f)
		{
			Phase = EPhase::Departing;
			PhaseTime = 0.f;
			if (ACharacter* C = Cast<ACharacter>(Rider.Get()))
			{
				C->GetCharacterMovement()->AddTickPrerequisiteActor(this);
			}
			if (RunSound)
			{
				RunAudio->SetSound(RunSound);
				RunAudio->SetVolumeMultiplier(1.f);
				RunAudio->Play();
			}
			UE_LOG(LogNeonVeil, Log, TEXT("%s: departing"), *GetName());
		}
		break;
	case EPhase::Departing:
	{
		const float A = FMath::Clamp(PhaseTime / DepartTime, 0.f, 1.f);
		SetOffset(-DepartDistance * A * A); // ease-in: pulls away slowly, then builds speed
		RunAudio->SetWorldLocation(Tram->GetActorLocation());
		if (!bBoardedSent && PhaseTime >= BoardedEventDelay)
		{
			bBoardedSent = true;
			if (Obj && BoardedEventTag.IsValid())
			{
				Obj->SendEvent(BoardedEventTag);
			}
		}
		if (A >= 1.f)
		{
			if (ACharacter* C = Cast<ACharacter>(Rider.Get()))
			{
				C->GetCharacterMovement()->RemoveTickPrerequisiteActor(this);
			}
			Phase = EPhase::Gone;
			SetActorTickEnabled(false);
		}
		break;
	}
	default:
		break;
	}
}
