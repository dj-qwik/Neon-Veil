#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "GameplayTagContainer.h"
#include "Interaction/NVInteractable.h"
#include "NVInteractableActor.generated.h"

class UStaticMeshComponent;
class USoundBase;

DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FNVOnInteracted, ANVInteractableActor*, Interactable, AActor*, Interactor);

/**
 * General-purpose usable object: terminals, holo-table, biometric panel, scan arch console.
 * On use it broadcasts its CompletionEventTag (consumed by the objective subsystem) and calls BP_OnInteracted.
 */
UCLASS(Blueprintable)
class NEONVEIL_API ANVInteractableActor : public AActor, public INVInteractable
{
	GENERATED_BODY()

public:
	ANVInteractableActor();

	// INVInteractable
	virtual FText GetInteractionPrompt_Implementation(AActor* Interactor) const override { return Prompt; }
	virtual float GetHoldDuration_Implementation() const override { return HoldDuration; }
	virtual bool CanInteract_Implementation(AActor* Interactor) const override;
	virtual void Interact_Implementation(AActor* Interactor) override;
	virtual void SetFocused_Implementation(bool bFocused) override;

	UFUNCTION(BlueprintCallable, Category = "NeonVeil|Interaction")
	void SetEnabled(bool bNewEnabled) { bEnabled = bNewEnabled; }

	UFUNCTION(BlueprintPure, Category = "NeonVeil|Interaction")
	bool HasBeenUsed() const { return UseCount > 0; }

	UPROPERTY(BlueprintAssignable, Category = "NeonVeil|Interaction")
	FNVOnInteracted OnInteracted;

protected:
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	TObjectPtr<UStaticMeshComponent> Mesh;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interaction")
	FText Prompt = NSLOCTEXT("NeonVeil", "DefaultPrompt", "Use");

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interaction", meta = (ClampMin = "0"))
	float HoldDuration = 0.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interaction")
	bool bEnabled = true;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interaction")
	bool bSingleUse = true;

	/** Sent to the objective subsystem on use (e.g. NV.Event.M00.HoloTableReviewed). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interaction")
	FGameplayTag CompletionEventTag;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interaction")
	TObjectPtr<USoundBase> UseSound;

	/** Custom-depth stencil value used by the focus outline post-process. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interaction")
	int32 FocusStencilValue = 1;

	UFUNCTION(BlueprintImplementableEvent, Category = "NeonVeil|Interaction")
	void BP_OnInteracted(AActor* Interactor);

	UFUNCTION(BlueprintImplementableEvent, Category = "NeonVeil|Interaction")
	void BP_OnFocusChanged(bool bFocused);

private:
	int32 UseCount = 0;
};
