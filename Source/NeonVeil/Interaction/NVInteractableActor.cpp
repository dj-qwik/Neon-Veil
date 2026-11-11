#include "Interaction/NVInteractableActor.h"
#include "Objectives/NVObjectiveSubsystem.h"
#include "Components/StaticMeshComponent.h"
#include "Kismet/GameplayStatics.h"
#include "Sound/SoundBase.h"
#include "Engine/GameInstance.h"

ANVInteractableActor::ANVInteractableActor()
{
	PrimaryActorTick.bCanEverTick = false;
	Mesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Mesh"));
	SetRootComponent(Mesh);
	Mesh->SetCollisionProfileName(TEXT("BlockAll"));
}

bool ANVInteractableActor::CanInteract_Implementation(AActor* Interactor) const
{
	return bEnabled && !(bSingleUse && UseCount > 0);
}

void ANVInteractableActor::Interact_Implementation(AActor* Interactor)
{
	if (!CanInteract_Implementation(Interactor))
	{
		return;
	}
	++UseCount;
	if (UseSound)
	{
		UGameplayStatics::PlaySoundAtLocation(this, UseSound, GetActorLocation());
	}
	if (CompletionEventTag.IsValid())
	{
		if (UNVObjectiveSubsystem* Objectives = UNVObjectiveSubsystem::Get(this))
		{
			Objectives->SendEvent(CompletionEventTag);
		}
	}
	BP_OnInteracted(Interactor);
	OnInteracted.Broadcast(this, Interactor);
}

void ANVInteractableActor::SetFocused_Implementation(bool bFocused)
{
	Mesh->SetRenderCustomDepth(bFocused);
	Mesh->SetCustomDepthStencilValue(FocusStencilValue);
	BP_OnFocusChanged(bFocused);
}
