#include "Interaction/NVInteractionComponent.h"
#include "Interaction/NVInteractable.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/PlayerController.h"
#include "Engine/World.h"

UNVInteractionComponent::UNVInteractionComponent()
{
	PrimaryComponentTick.bCanEverTick = true;
	PrimaryComponentTick.TickGroup = TG_PostPhysics;
}

void UNVInteractionComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

	TimeSinceTrace += DeltaTime;
	if (TimeSinceTrace >= TraceInterval)
	{
		TimeSinceTrace = 0.f;
		UpdateFocus();
	}

	if (bUsing)
	{
		AActor* Focus = FocusedActor.Get();
		if (!Focus || !INVInteractable::Execute_CanInteract(Focus, GetOwner()))
		{
			EndUse();
			return;
		}
		const float Hold = INVInteractable::Execute_GetHoldDuration(Focus);
		HoldElapsed += DeltaTime;
		OnHoldProgress.Broadcast(Hold > 0.f ? FMath::Clamp(HoldElapsed / Hold, 0.f, 1.f) : 1.f);
		if (HoldElapsed >= Hold)
		{
			CompleteUse();
		}
	}
}

void UNVInteractionComponent::UpdateFocus()
{
	const APawn* Pawn = Cast<APawn>(GetOwner());
	const APlayerController* PC = Pawn ? Cast<APlayerController>(Pawn->GetController()) : nullptr;
	if (!PC)
	{
		return;
	}

	FVector ViewLoc;
	FRotator ViewRot;
	PC->GetPlayerViewPoint(ViewLoc, ViewRot);
	const FVector End = ViewLoc + ViewRot.Vector() * InteractionRange;

	FCollisionQueryParams Params(SCENE_QUERY_STAT(NVInteract), false, GetOwner());
	FHitResult Hit;
	AActor* NewFocus = nullptr;
	if (GetWorld()->SweepSingleByChannel(Hit, ViewLoc, End, FQuat::Identity, ECC_Visibility, FCollisionShape::MakeSphere(TraceRadius), Params))
	{
		AActor* HitActor = Hit.GetActor();
		if (HitActor && HitActor->Implements<UNVInteractable>() && INVInteractable::Execute_CanInteract(HitActor, GetOwner()))
		{
			NewFocus = HitActor;
		}
	}
	SetFocus(NewFocus);
}

void UNVInteractionComponent::SetFocus(AActor* NewFocus)
{
	AActor* Old = FocusedActor.Get();
	if (Old == NewFocus)
	{
		return;
	}
	if (Old)
	{
		INVInteractable::Execute_SetFocused(Old, false);
	}
	FocusedActor = NewFocus;
	if (bUsing)
	{
		EndUse();
	}

	FText Prompt;
	if (NewFocus)
	{
		INVInteractable::Execute_SetFocused(NewFocus, true);
		Prompt = INVInteractable::Execute_GetInteractionPrompt(NewFocus, GetOwner());
	}
	OnFocusChanged.Broadcast(NewFocus, Prompt);
}

void UNVInteractionComponent::BeginUse()
{
	if (AActor* Focus = FocusedActor.Get())
	{
		bUsing = true;
		HoldElapsed = 0.f;
		if (INVInteractable::Execute_GetHoldDuration(Focus) <= 0.f)
		{
			CompleteUse();
		}
	}
}

void UNVInteractionComponent::EndUse()
{
	if (bUsing)
	{
		bUsing = false;
		HoldElapsed = 0.f;
		OnHoldProgress.Broadcast(0.f);
	}
}

void UNVInteractionComponent::CompleteUse()
{
	AActor* Focus = FocusedActor.Get();
	bUsing = false;
	HoldElapsed = 0.f;
	OnHoldProgress.Broadcast(0.f);
	if (Focus)
	{
		INVInteractable::Execute_Interact(Focus, GetOwner());
		// Force a refresh: the object may no longer be interactable.
		SetFocus(nullptr);
		UpdateFocus();
	}
}
