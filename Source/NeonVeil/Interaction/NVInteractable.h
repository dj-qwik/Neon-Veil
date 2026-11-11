#pragma once

#include "CoreMinimal.h"
#include "UObject/Interface.h"
#include "NVInteractable.generated.h"

UINTERFACE(MinimalAPI, BlueprintType)
class UNVInteractable : public UInterface
{
	GENERATED_BODY()
};

/**
 * Anything the player can use: scan arch panel, holo-table, terminals, biometric panel.
 * Implement in C++ or Blueprint.
 */
class NEONVEIL_API INVInteractable
{
	GENERATED_BODY()

public:
	/** Player-facing verb + object, e.g. "Review assignment". */
	UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = "NeonVeil|Interaction")
	FText GetInteractionPrompt(AActor* Interactor) const;

	/** Seconds the use input must be held. 0 = press. */
	UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = "NeonVeil|Interaction")
	float GetHoldDuration() const;

	UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = "NeonVeil|Interaction")
	bool CanInteract(AActor* Interactor) const;

	UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = "NeonVeil|Interaction")
	void Interact(AActor* Interactor);

	UFUNCTION(BlueprintNativeEvent, BlueprintCallable, Category = "NeonVeil|Interaction")
	void SetFocused(bool bFocused);
};
