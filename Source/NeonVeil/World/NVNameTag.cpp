#include "World/NVNameTag.h"
#include "Components/SceneComponent.h"

namespace
{
	TArray<TWeakObjectPtr<ANVNameTag>>& Registry()
	{
		static TArray<TWeakObjectPtr<ANVNameTag>> R;
		return R;
	}
}

ANVNameTag::ANVNameTag()
{
	PrimaryActorTick.bCanEverTick = false;
	RootComponent = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
	RootComponent->SetMobility(EComponentMobility::Movable);
}

const TArray<TWeakObjectPtr<ANVNameTag>>& ANVNameTag::All()
{
	Registry().RemoveAll([](const TWeakObjectPtr<ANVNameTag>& T) { return !T.IsValid(); });
	return Registry();
}

void ANVNameTag::BeginPlay()
{
	Super::BeginPlay();
	Registry().AddUnique(this);
}

void ANVNameTag::EndPlay(const EEndPlayReason::Type Reason)
{
	Registry().Remove(this);
	Super::EndPlay(Reason);
}
