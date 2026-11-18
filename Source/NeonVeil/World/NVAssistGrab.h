#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "NVAssistGrab.generated.h"

class UBoxComponent;
class UArrowComponent;
class USoundBase;

/**
 * Authored "assisted grab" (Bible M01-C): if the player is in the air inside the volume, they catch the ledge and
 * are pulled up onto it (at the arrow), so a desperate jump in the transit shaft always lands where it should.
 */
UCLASS()
class NEONVEIL_API ANVAssistGrab : public AActor
{
	GENERATED_BODY()

public:
	ANVAssistGrab();
	virtual void Tick(float DeltaSeconds) override;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Grab")
	float PullTime = 0.45f;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Grab")
	TObjectPtr<USoundBase> GrabSound;

protected:
	virtual void BeginPlay() override;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components")
	TObjectPtr<UBoxComponent> Volume;
	/** Where the player ends up (capsule centre), facing along the arrow. */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components", meta = (MakeEditWidget = true))
	TObjectPtr<UArrowComponent> LandPoint;

private:
	TWeakObjectPtr<class ACharacter> Pulling;
	FVector From = FVector::ZeroVector;
	float T = 0.f;
};
