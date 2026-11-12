#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "NVObjectiveDoor.generated.h"

class UStaticMeshComponent;
class USoundBase;

/**
 * Sliding door that opens when an objective becomes active or complete. Re-evaluates after a
 * checkpoint load, so restored progress never leaves the player locked out.
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

private:
	UFUNCTION()
	void HandleObjectiveEvent(FName ObjectiveID);

	UFUNCTION()
	void Evaluate();

	FVector LeftClosed;
	FVector RightClosed;
	float Alpha = 0.f;
	bool bTargetOpen = false;
};
