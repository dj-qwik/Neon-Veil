#include "World/NVAmbienceZone.h"

#include "Components/AudioComponent.h"
#include "EngineUtils.h"
#include "GameFramework/Pawn.h"
#include "Kismet/GameplayStatics.h"

ANVAmbienceZone::ANVAmbienceZone()
{
	PrimaryActorTick.bCanEverTick = true;
	PrimaryActorTick.TickInterval = 0.1f;
	SetRootComponent(CreateDefaultSubobject<USceneComponent>(TEXT("Root")));
}

void ANVAmbienceZone::BeginPlay()
{
	Super::BeginPlay();
	for (TActorIterator<AActor> It(GetWorld()); It; ++It)
	{
		if (!It->ActorHasTag(ManagedTag))
		{
			continue;
		}
		TArray<UAudioComponent*> Comps;
		It->GetComponents(Comps);
		for (UAudioComponent* C : Comps)
		{
			FManaged M;
			M.Comp = C;
			M.BaseVolume = C->VolumeMultiplier;
			Managed.Add(M);
		}
	}
}

void ANVAmbienceZone::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	const APawn* P = UGameplayStatics::GetPlayerPawn(this, 0);
	if (!P || Managed.Num() == 0)
	{
		return;
	}
	const FVector Loc = P->GetActorLocation();
	float Dist = TNumericLimits<float>::Max();
	for (const FBox& B : Outdoor)
	{
		Dist = FMath::Min(Dist, FMath::Sqrt(static_cast<float>(B.ComputeSquaredDistanceToPoint(Loc))));
	}
	const float Out = 1.f - FMath::Clamp(Dist / BlendDistance, 0.f, 1.f); // 1 outdoors, 0 indoors
	// ease toward the target so stepping through a door is a soft fade, not a switch
	const float Target = Out;
	const float Next = Current < 0.f ? Target : FMath::FInterpTo(Current, Target, DeltaSeconds, 4.f);
	if (FMath::Abs(Next - Current) < 0.002f)
	{
		return;
	}
	Current = Next;
	const float Vol = FMath::Lerp(IndoorVolume, 1.f, Current);
	// cutoff moves on a log scale: 700 Hz indoors -> fully open outdoors
	const float Hz = FMath::Exp(FMath::Lerp(FMath::Loge(IndoorLowPassHz), FMath::Loge(20000.f), Current));
	for (const FManaged& M : Managed)
	{
		if (UAudioComponent* C = M.Comp.Get())
		{
			C->SetVolumeMultiplier(M.BaseVolume * Vol);
			C->SetLowPassFilterEnabled(Current < 0.98f);
			C->SetLowPassFilterFrequency(Hz);
		}
	}
}
