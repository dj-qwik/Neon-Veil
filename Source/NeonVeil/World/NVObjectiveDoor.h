#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "NVObjectiveDoor.generated.h"

class UStaticMeshComponent;
class UBoxComponent;
class USoundBase;
class ANVInteractableActor;

/**
 * Sliding door that opens when an objective becomes active or complete, or when one of its OpenWhenUsed
 * interactables (e.g. a palm scanner) is used. Re-evaluates after a checkpoint load, so restored progress never
 * leaves the player locked out.
 */
UCLASS()
class NEONVEIL_API ANVObjectiveDoor : public AActor
{
	GENERATED_BODY()

public:
	ANVObjectiveDoor();

	virtual void Tick(float DeltaSeconds) override;

	/** Open once this objective is complete. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Door")
	FName OpenWhenComplete;

	/** Open once this objective is active (or complete). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Door")
	FName OpenWhenActive;

	/** Local offset of each panel when fully open (left panel uses -Y of this, right +Y). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Door")
	float SlideDistance = 160.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Door")
	float OpenTime = 0.9f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Door")
	TObjectPtr<USoundBase> OpenSound;

	/** Using any of these (scanner panels, switches) opens the door after OpenDelay. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Door")
	TArray<TObjectPtr<ANVInteractableActor>> OpenWhenUsed;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Door", meta = (ClampMin = "0"))
	float OpenDelay = 0.6f;

	/** Half-size of an invisible blocking box across the doorway (for panel meshes without collision). Zero = none.
	 *  Place it with the Blocker component's relative location. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Door")
	FVector BlockerExtent = FVector::ZeroVector;

	UFUNCTION(BlueprintCallable, Category = "NeonVeil")
	void SetOpen(bool bOpen, bool bInstant = false);

	UFUNCTION(BlueprintPure, Category = "NeonVeil")
	bool IsOpen() const { return bTargetOpen; }

protected:
	virtual void BeginPlay() override;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	TObjectPtr<USceneComponent> Root;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	TObjectPtr<UStaticMeshComponent> PanelLeft;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	TObjectPtr<UStaticMeshComponent> PanelRight;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	TObjectPtr<UStaticMeshComponent> Frame;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	TObjectPtr<UBoxComponent> Blocker;

private:
	UFUNCTION()
	void HandleObjectiveEvent(FName ObjectiveID);

	UFUNCTION()
	void Evaluate();

	UFUNCTION()
	void HandleUsed(ANVInteractableActor* Interactable, AActor* Interactor);

	void UpdateBlocker();
	FTimerHandle OpenTimer;

	FVector LeftClosed;
	FVector RightClosed;
	float Alpha = 0.f;
	bool bTargetOpen = false;
};
