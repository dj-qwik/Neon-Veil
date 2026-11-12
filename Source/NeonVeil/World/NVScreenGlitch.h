#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "UI/NVSubtitleLine.h"
#include "NVScreenGlitch.generated.h"

class UBoxComponent;
class UMaterialInterface;
class UMeshComponent;
class USoundBase;

/**
 * Authored story beat (Bible §4, M00 operations gallery): "show an unexplained 180 ms surveillance
 * discontinuity. AI voice denies anomaly." When the player first enters the volume, every mesh on
 * the target actors (the gallery data screens) is swapped to a static/glitch material for a total of
 * GlitchDuration seconds (split into two short pulses so it reads as a dropped feed, not a flash),
 * a glitch sound plays, and after a beat the denial lines are queued as subtitles. One-shot.
 */
UCLASS()
class NEONVEIL_API ANVScreenGlitch : public AActor
{
	GENERATED_BODY()

public:
	ANVScreenGlitch();

	/** Screens to glitch. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Glitch")
	TArray<TObjectPtr<AActor>> Targets;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Glitch")
	TObjectPtr<UMaterialInterface> GlitchMaterial;

	/** Total visible discontinuity (s). Bible: 180 ms. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Glitch", meta = (ClampMin = "0.02"))
	float GlitchDuration = 0.18f;

	/** Delay after entering before the discontinuity (s). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Glitch", meta = (ClampMin = "0"))
	float StartDelay = 1.2f;

	/** Delay after the discontinuity before the lines play (s). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Glitch", meta = (ClampMin = "0"))
	float LinesDelay = 1.0f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Glitch")
	TObjectPtr<USoundBase> GlitchSound;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Glitch")
	TArray<FNVSubtitleLine> Lines;

	/** QA hook: run the beat immediately. */
	UFUNCTION(BlueprintCallable, Category = "Glitch")
	void TriggerGlitch();

protected:
	virtual void BeginPlay() override;

	UPROPERTY(VisibleAnywhere, Category = "Components")
	TObjectPtr<UBoxComponent> Volume;

private:
	UFUNCTION()
	void HandleBeginOverlap(UPrimitiveComponent* OverlappedComp, AActor* Other, UPrimitiveComponent* OtherComp, int32 BodyIndex, bool bFromSweep, const FHitResult& Sweep);

	void SetGlitched(bool bOn);
	void PulseOff();
	void PulseOn2();
	void End();
	void PlayLines();

	struct FSavedMats
	{
		TWeakObjectPtr<UMeshComponent> Comp;
		TArray<TObjectPtr<UMaterialInterface>> Mats;
	};
	TArray<FSavedMats> Saved;
	FTimerHandle Timer;
	bool bFired = false;
};
