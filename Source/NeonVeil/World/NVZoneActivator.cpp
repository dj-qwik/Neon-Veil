#include "World/NVZoneActivator.h"

#include "Components/PrimitiveComponent.h"
#include "EngineUtils.h"
#include "GameFramework/Pawn.h"
#include "Kismet/GameplayStatics.h"
#include "Particles/ParticleSystemComponent.h"

ANVZoneActivator::ANVZoneActivator()
{
	PrimaryActorTick.bCanEverTick = true;
	PrimaryActorTick.TickInterval = 0.5f;
	SetRootComponent(CreateDefaultSubobject<USceneComponent>(TEXT("Root")));
}

void ANVZoneActivator::BeginPlay()
{
	Super::BeginPlay();
	for (TActorIterator<AActor> It(GetWorld()); It; ++It)
	{
		if (It->ActorHasTag(ManagedTag))
		{
			Managed.Add(*It);
		}
	}
}

void ANVZoneActivator::Apply(bool bOn)
{
	for (AActor* A : Managed)
	{
		if (!A)
		{
			continue;
		}
		A->SetActorTickEnabled(bOn);
		TArray<UActorComponent*> Comps;
		A->GetComponents(Comps);
		for (UActorComponent* C : Comps)
		{
			if (UParticleSystemComponent* P = Cast<UParticleSystemComponent>(C))
			{
				if (bOn) { P->Activate(); } else { P->DeactivateImmediate(); }
			}
			if (UPrimitiveComponent* Prim = Cast<UPrimitiveComponent>(C))
			{
				Prim->SetVisibility(bOn);
			}
			C->SetComponentTickEnabled(bOn);
		}
	}
}

void ANVZoneActivator::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	const APawn* P = UGameplayStatics::GetPlayerPawn(this, 0);
	if (!P)
	{
		return;
	}
	const FBox Region = FBox(RegionMin, RegionMax).ExpandBy(Margin);
	const bool bOn = Region.IsInsideOrOn(P->GetActorLocation());
	if (State != static_cast<int8>(bOn))
	{
		State = static_cast<int8>(bOn);
		Apply(bOn);
	}
}
