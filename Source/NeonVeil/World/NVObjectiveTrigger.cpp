#include "World/NVObjectiveTrigger.h"
#include "Character/NVPlayerCharacter.h"
#include "Objectives/NVObjectiveSubsystem.h"
#include "UI/NVHUD.h"
#include "NeonVeil.h"

#include "Components/BoxComponent.h"
#include "GameFramework/PlayerController.h"
#include "TimerManager.h"

ANVObjectiveTrigger::ANVObjectiveTrigger()
{
	PrimaryActorTick.bCanEverTick = false;
	Volume = CreateDefaultSubobject<UBoxComponent>(TEXT("Volume"));
	SetRootComponent(Volume);
	Volume->SetBoxExtent(FVector(100.f, 150.f, 120.f));
	Volume->SetCollisionProfileName(TEXT("Trigger"));
}

void ANVObjectiveTrigger::BeginPlay()
{
	Super::BeginPlay();
	Volume->OnComponentBeginOverlap.AddDynamic(this, &ANVObjectiveTrigger::HandleBeginOverlap);
	Volume->OnComponentEndOverlap.AddDynamic(this, &ANVObjectiveTrigger::HandleEndOverlap);
}

bool ANVObjectiveTrigger::IsArmed() const
{
	if (bOnce && bFired)
	{
		return false;
	}
	if (!RequiredActiveObjective.IsNone())
	{
		const UNVObjectiveSubsystem* Obj = UNVObjectiveSubsystem::Get(this);
		return Obj && Obj->IsObjectiveActive(RequiredActiveObjective);
	}
	return true;
}

void ANVObjectiveTrigger::HandleBeginOverlap(UPrimitiveComponent*, AActor* Other, UPrimitiveComponent*, int32, bool, const FHitResult&)
{
	if (!Cast<ANVPlayerCharacter>(Other) || !IsArmed())
	{
		return;
	}
	if (Delay <= 0.f)
	{
		Fire();
		return;
	}
	if (!StartNotice.IsEmpty())
	{
		if (APlayerController* PC = GetWorld()->GetFirstPlayerController())
		{
			if (ANVHUD* HUD = Cast<ANVHUD>(PC->GetHUD()))
			{
				HUD->ShowNotice(StartNotice, Delay);
			}
		}
	}
	BP_OnScanStarted();
	GetWorldTimerManager().SetTimer(DelayTimer, this, &ANVObjectiveTrigger::Fire, Delay, false);
}

void ANVObjectiveTrigger::HandleEndOverlap(UPrimitiveComponent*, AActor* Other, UPrimitiveComponent*, int32)
{
	// Walking out mid-scan cancels it; walking back in restarts it.
	if (Cast<ANVPlayerCharacter>(Other) && GetWorldTimerManager().IsTimerActive(DelayTimer))
	{
		GetWorldTimerManager().ClearTimer(DelayTimer);
		UE_LOG(LogNeonVeil, Log, TEXT("%s: scan cancelled (player left)"), *GetName());
	}
}

void ANVObjectiveTrigger::Fire()
{
	if (!IsArmed())
	{
		return;
	}
	bFired = true;
	UE_LOG(LogNeonVeil, Log, TEXT("%s fired %s"), *GetName(), *EventTag.ToString());
	if (APlayerController* PC = GetWorld()->GetFirstPlayerController())
	{
		if (ANVHUD* HUD = Cast<ANVHUD>(PC->GetHUD()))
		{
			if (!CompleteNotice.IsEmpty())
			{
				HUD->ShowNotice(CompleteNotice, 2.5f);
			}
			HUD->QueueSubtitles(LinesOnComplete);
		}
	}
	if (UNVObjectiveSubsystem* Obj = UNVObjectiveSubsystem::Get(this))
	{
		Obj->SendEvent(EventTag);
	}
	BP_OnFired();
}
