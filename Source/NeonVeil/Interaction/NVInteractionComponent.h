#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "NVInteractionComponent.generated.h"

DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FNVOnFocusChanged, AActor*, NewFocus, FText, Prompt);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FNVOnHoldProgress, float, Progress01);

/**
 * Traces from the player camera every few frames, tracks the focused interactable,
 * and handles press / hold-to-use.
 */
UCLASS(ClassGroup = (NeonVeil), meta = (BlueprintSpawnableComponent))
class NEONVEIL_API UNVInteractionComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	UNVInteractionComponent();

	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

	UFUNCTION(BlueprintCallable, Category = "NeonVeil|Interaction")
	void BeginUse();

	UFUNCTION(BlueprintCallable, Category = "NeonVeil|Interaction")
	void EndUse();

	UFUNCTION(BlueprintPure, Category = "NeonVeil|Interaction")
	AActor* GetFocusedActor() const { return FocusedActor.Get(); }

	UPROPERTY(BlueprintAssignable, Category = "NeonVeil|Interaction")
	FNVOnFocusChanged OnFocusChanged;

	UPROPERTY(BlueprintAssignable, Category = "NeonVeil|Interaction")
	FNVOnHoldProgress OnHoldProgress;

	/** Bible §7: works at 2.5 m. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "NeonVeil|Interaction")
	float InteractionRange = 250.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "NeonVeil|Interaction")
	float TraceRadius = 12.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "NeonVeil|Interaction")
	float TraceInterval = 0.05f;

private:
	void UpdateFocus();
	void SetFocus(AActor* NewFocus);
	void CompleteUse();

	TWeakObjectPtr<AActor> FocusedActor;
	float TimeSinceTrace = 0.f;
	bool bUsing = false;
	float HoldElapsed = 0.f;
};
