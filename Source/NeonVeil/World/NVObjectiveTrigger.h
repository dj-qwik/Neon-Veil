#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "GameplayTagContainer.h"
#include "UI/NVSubtitleLine.h"
#include "NVObjectiveTrigger.generated.h"

class UBoxComponent;

/**
 * Volume that sends an objective event when the player enters it (optionally after a scan delay).
 * Used for the security arch (M00-O01) and the antechamber approach.
 */
UCLASS()
class NEONVEIL_API ANVObjectiveTrigger : public AActor
{
	GENERATED_BODY()

public:
	ANVObjectiveTrigger();

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Trigger")
	FGameplayTag EventTag;

	/** Only fires while this objective is active. None = always. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Trigger")
	FName RequiredActiveObjective;

	/** Seconds the player must stay inside (e.g. arch scan). 0 = instant. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Trigger", meta = (ClampMin = "0"))
	float Delay = 0.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Trigger")
	FText StartNotice;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Trigger")
	FText CompleteNotice;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Trigger")
	TArray<FNVSubtitleLine> LinesOnComplete;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Trigger")
	bool bOnce = true;

	UFUNCTION(BlueprintImplementableEvent, Category = "NeonVeil")
	void BP_OnScanStarted();

	UFUNCTION(BlueprintImplementableEvent, Category = "NeonVeil")
	void BP_OnFired();

protected:
	virtual void BeginPlay() override;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	TObjectPtr<UBoxComponent> Volume;

private:
	UFUNCTION()
	void HandleBeginOverlap(UPrimitiveComponent* OverlappedComp, AActor* Other, UPrimitiveComponent* OtherComp, int32 BodyIndex, bool bFromSweep, const FHitResult& Sweep);

	UFUNCTION()
	void HandleEndOverlap(UPrimitiveComponent* OverlappedComp, AActor* Other, UPrimitiveComponent* OtherComp, int32 BodyIndex);

	void Fire();
	bool IsArmed() const;

	FTimerHandle DelayTimer;
	bool bFired = false;
};
