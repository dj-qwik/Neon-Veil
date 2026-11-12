#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "NVDirectorReflection.generated.h"

class UBoxComponent;
class UAnimationAsset;
class USkeletalMeshComponent;
class USoundBase;

/**
 * Bible §4 M00: "Director's reflection on dark glass should briefly appear subtly out of sync; do not reveal
 * clone plot yet."
 * Real = the Director standing at the antechamber's dark glass. Mirror = a duplicate mirrored across the glass
 * plane (negative scale), seen through the smoked glass so it reads as his reflection. Both play the same idle.
 * The first time the player is inside Volume and looks at the reflection for LookTime seconds, the mirror's
 * animation holds for LagTime (it falls behind the real body), then runs slightly fast for CatchUp seconds
 * until it is back in step. One-shot; no audio cue, no UI.
 */
UCLASS()
class NEONVEIL_API ANVDirectorReflection : public AActor
{
	GENERATED_BODY()

public:
	ANVDirectorReflection();

	virtual void BeginPlay() override;
	virtual void Tick(float DeltaSeconds) override;

	UPROPERTY(VisibleAnywhere, Category = "Reflection")
	TObjectPtr<UBoxComponent> Volume;

	UPROPERTY(EditAnywhere, Category = "Reflection")
	TObjectPtr<AActor> Real;

	UPROPERTY(EditAnywhere, Category = "Reflection")
	TObjectPtr<AActor> Mirror;

	/** Looping idle for both bodies (single-node playback). Optional if the actors already animate. */
	UPROPERTY(EditAnywhere, Category = "Reflection")
	TObjectPtr<UAnimationAsset> IdleAnim;

	UPROPERTY(EditAnywhere, Category = "Reflection")
	float LookTime = 0.6f;

	UPROPERTY(EditAnywhere, Category = "Reflection")
	float LagTime = 0.35f;

	UPROPERTY(EditAnywhere, Category = "Reflection")
	float CatchUp = 1.4f;

	/** cos of the max angle between the view and the reflection that counts as looking at it. */
	UPROPERTY(EditAnywhere, Category = "Reflection")
	float LookDot = 0.93f;

private:
	static USkeletalMeshComponent* FindBody(AActor* Actor);
	void SetMirrorRate(float Rate);

	float Looked = 0.f;
	float StateTime = 0.f;
	int32 Phase = 0; // 0 waiting, 1 lagging, 2 out of sync, 3 done
};
