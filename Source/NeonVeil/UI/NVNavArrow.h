#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "NVNavArrow.generated.h"

class UStaticMeshComponent;
class UMaterialInstanceDynamic;
class UMaterialInterface;

/**
 * Wayfinding aid: a short, half-transparent green arrow that slides out from under the player's feet and points
 * toward the current objective for a few seconds, then fades away. Pure visual: no collision, no shadow, no
 * physics, no navigation influence. It follows the walkable route (nav-mesh path) when one reaches the goal, and
 * the straight bearing otherwise.
 *
 * The goal of the first active objective is found automatically: an actor tagged "NVGoal:<ObjectiveID>" first,
 * then interactables / triggers / lifts / trams tied to that objective (by required objective or completion event),
 * nearest one wins.
 */
UCLASS(NotPlaceable)
class NEONVEIL_API ANVNavArrow : public AActor
{
	GENERATED_BODY()

public:
	ANVNavArrow();

	virtual void Tick(float DeltaSeconds) override;

	/** Shows the arrow for Duration seconds. Returns false (and shows nothing) if no goal could be found. */
	bool Show(APawn* ForPawn);

	/** Draws the arrow (projected from its spot on the floor) onto the HUD canvas. */
	void DrawOnCanvas(class UCanvas* Canvas, APlayerController* PC) const;

	/** World position of the current objective's goal. */
	static bool FindObjectiveGoal(const UObject* WorldContext, const FVector& From, FVector& OutGoal);

	UPROPERTY(EditAnywhere, Category = "Nav Arrow")
	float Duration = 3.5f;

	UPROPERTY(EditAnywhere, Category = "Nav Arrow")
	float MaxOpacity = 0.6f;

	UPROPERTY(EditAnywhere, Category = "Nav Arrow")
	FLinearColor Color = FLinearColor(0.15f, 1.f, 0.35f, 1.f);

protected:
	UPROPERTY(VisibleAnywhere, Category = "Components")
	TObjectPtr<USceneComponent> Pivot;

	UPROPERTY(VisibleAnywhere, Category = "Components")
	TObjectPtr<UStaticMeshComponent> Shaft;

	UPROPERTY(VisibleAnywhere, Category = "Components")
	TObjectPtr<UStaticMeshComponent> Head;

	UPROPERTY(Transient)
	TObjectPtr<UMaterialInstanceDynamic> MID;

	UPROPERTY(Transient)
	TObjectPtr<UMaterialInstanceDynamic> MIDRim;

	UPROPERTY()
	TObjectPtr<class UTexture2D> WhiteTex;

private:
	void UpdateDirection();
	void Place(float DeltaSeconds);

	TWeakObjectPtr<APawn> Pawn;
	FVector Goal = FVector::ZeroVector;
	float Age = 0.f;
	float ShowTime = 0.f;
	bool bShowing = false;
	bool bLoggedMid = false;
	float LastOpacity = -1.f;
	float CurrentScale = 1.f;
	float CurrentOpacity = 0.f;
	mutable bool bLoggedDraw = false;

	float RepathTimer = 0.f;
	float Yaw = 0.f;
	float TargetYaw = 0.f;
};
