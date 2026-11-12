#include "World/NVScreenGlitch.h"

#include "Components/BoxComponent.h"
#include "Components/MeshComponent.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/PlayerController.h"
#include "Kismet/GameplayStatics.h"
#include "Materials/MaterialInterface.h"
#include "TimerManager.h"
#include "UI/NVHUD.h"
#include "NeonVeil.h"

ANVScreenGlitch::ANVScreenGlitch()
{
	PrimaryActorTick.bCanEverTick = false;
	Volume = CreateDefaultSubobject<UBoxComponent>(TEXT("Volume"));
	Volume->SetBoxExtent(FVector(200.f, 400.f, 200.f));
	Volume->SetCollisionProfileName(TEXT("Trigger"));
	SetRootComponent(Volume);
}

void ANVScreenGlitch::BeginPlay()
{
	Super::BeginPlay();
	Volume->OnComponentBeginOverlap.AddDynamic(this, &ANVScreenGlitch::HandleBeginOverlap);
}

void ANVScreenGlitch::HandleBeginOverlap(UPrimitiveComponent*, AActor* Other, UPrimitiveComponent*, int32, bool, const FHitResult&)
{
	const APawn* Pawn = Cast<APawn>(Other);
	if (bFired || !Pawn || !Pawn->IsPlayerControlled())
	{
		return;
	}
	bFired = true;
	GetWorldTimerManager().SetTimer(Timer, this, &ANVScreenGlitch::TriggerGlitch, FMath::Max(StartDelay, 0.01f), false);
}

void ANVScreenGlitch::TriggerGlitch()
{
	bFired = true;
	UE_LOG(LogNeonVeil, Log, TEXT("%s: surveillance discontinuity (%.0f ms) on %d screens"), *GetName(), GlitchDuration * 1000.f, Targets.Num());
	if (GlitchSound)
	{
		UGameplayStatics::PlaySound2D(this, GlitchSound);
	}
	// two pulses: 55% on, 15% off, 30% on (sums to GlitchDuration)
	SetGlitched(true);
	GetWorldTimerManager().SetTimer(Timer, this, &ANVScreenGlitch::PulseOff, GlitchDuration * 0.55f, false);
}

void ANVScreenGlitch::PulseOff()
{
	SetGlitched(false);
	GetWorldTimerManager().SetTimer(Timer, this, &ANVScreenGlitch::PulseOn2, GlitchDuration * 0.15f, false);
}

void ANVScreenGlitch::PulseOn2()
{
	SetGlitched(true);
	GetWorldTimerManager().SetTimer(Timer, this, &ANVScreenGlitch::End, GlitchDuration * 0.30f, false);
}

void ANVScreenGlitch::End()
{
	SetGlitched(false);
	GetWorldTimerManager().SetTimer(Timer, this, &ANVScreenGlitch::PlayLines, FMath::Max(LinesDelay, 0.01f), false);
}

void ANVScreenGlitch::PlayLines()
{
	if (Lines.Num() == 0)
	{
		return;
	}
	if (APlayerController* PC = GetWorld()->GetFirstPlayerController())
	{
		if (ANVHUD* HUD = Cast<ANVHUD>(PC->GetHUD()))
		{
			HUD->QueueSubtitles(Lines);
		}
	}
}

void ANVScreenGlitch::SetGlitched(bool bOn)
{
	if (bOn)
	{
		if (!GlitchMaterial)
		{
			return;
		}
		if (Saved.Num() == 0)
		{
			for (AActor* A : Targets)
			{
				if (!A)
				{
					continue;
				}
				TArray<UMeshComponent*> Meshes;
				A->GetComponents(Meshes);
				for (UMeshComponent* M : Meshes)
				{
					FSavedMats S;
					S.Comp = M;
					for (int32 i = 0; i < M->GetNumMaterials(); ++i)
					{
						S.Mats.Add(M->GetMaterial(i));
					}
					Saved.Add(MoveTemp(S));
				}
			}
		}
		for (const FSavedMats& S : Saved)
		{
			if (UMeshComponent* M = S.Comp.Get())
			{
				for (int32 i = 0; i < S.Mats.Num(); ++i)
				{
					M->SetMaterial(i, GlitchMaterial);
				}
			}
		}
	}
	else
	{
		for (const FSavedMats& S : Saved)
		{
			if (UMeshComponent* M = S.Comp.Get())
			{
				for (int32 i = 0; i < S.Mats.Num(); ++i)
				{
					M->SetMaterial(i, S.Mats[i]);
				}
			}
		}
	}
}
