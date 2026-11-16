#include "Interaction/NVInteractionComponent.h"

#include "Components/PrimitiveComponent.h"
#include "Engine/OverlapResult.h"
#include "Engine/World.h"
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
		HoldProgress = Hold > 0.f ? FMath::Clamp(HoldElapsed / Hold, 0.f, 1.f) : 1.f;
		OnHoldProgress.Broadcast(HoldProgress);
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
	// Range is measured from the character, not the camera: in third person the camera sits a few metres behind
	// Ghost, so add the camera-to-character distance along the view (the trace ignores Ghost himself).
	const FVector Dir = ViewRot.Vector();
	const float CameraBehind = FMath::Max(0.f, static_cast<float>(FVector::DotProduct(Pawn->GetPawnViewLocation() - ViewLoc, Dir)));
	const FVector End = ViewLoc + Dir * (InteractionRange + CameraBehind);

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
	// Third person: the over-the-shoulder camera puts the crosshair beside Ghost, so a precise aim at a small box on
	// the wall is fiddly. If the view trace found nothing, take the usable thing in reach that Ghost and the camera
	// are both roughly facing, with a clear line from Ghost to it.
	if (!NewFocus && CameraBehind > 50.f)
	{
		const FVector Eye = Pawn->GetPawnViewLocation();
		TArray<FOverlapResult> Overlaps;
		FCollisionQueryParams OverlapParams(SCENE_QUERY_STAT(NVInteractNear), false, GetOwner());
		GetWorld()->OverlapMultiByChannel(Overlaps, Eye, FQuat::Identity, ECC_Visibility, FCollisionShape::MakeSphere(InteractionRange), OverlapParams);
		const FVector Dir2D = Dir.GetSafeNormal2D();
		float BestScore = -1.f;
		for (const FOverlapResult& O : Overlaps)
		{
			AActor* A = O.GetActor();
			if (!A || A == NewFocus || !A->Implements<UNVInteractable>() || !INVInteractable::Execute_CanInteract(A, GetOwner()))
			{
				continue;
			}
			const FVector Target = O.GetComponent() ? O.GetComponent()->Bounds.Origin : A->GetActorLocation();
			const FVector To = Target - Eye;
			const float Facing = FVector::DotProduct(To.GetSafeNormal2D(), Dir2D);
			if (Facing < ThirdPersonFacingCos || To.Size() > InteractionRange)
			{
				continue;
			}
			FHitResult Block;
			if (GetWorld()->LineTraceSingleByChannel(Block, Eye, Target, ECC_Visibility, OverlapParams) && Block.GetActor() != A)
			{
				continue;
			}
			const float Score = Facing - To.Size() / (InteractionRange * 4.f);
			if (Score > BestScore)
			{
				BestScore = Score;
				NewFocus = A;
			}
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
		HoldProgress = 0.f;
		OnHoldProgress.Broadcast(0.f);
	}
}

void UNVInteractionComponent::CompleteUse()
{
	AActor* Focus = FocusedActor.Get();
	bUsing = false;
	HoldElapsed = 0.f;
	HoldProgress = 0.f;
	OnHoldProgress.Broadcast(0.f);
	if (Focus)
	{
		INVInteractable::Execute_Interact(Focus, GetOwner());
		// Force a refresh: the object may no longer be interactable.
		SetFocus(nullptr);
		UpdateFocus();
	}
}
