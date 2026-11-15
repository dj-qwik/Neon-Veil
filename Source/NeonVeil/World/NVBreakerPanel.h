#pragma once

#include "CoreMinimal.h"
#include "Interaction/NVInteractableActor.h"
#include "NVBreakerPanel.generated.h"

class UMaterialInterface;

/**
 * Wall-mounted breaker box: a steel housing with a fuse row, a hazard strip, a red/green status lamp pair and a big
 * throw lever. Using it throws the lever down (off -> on), swaps the lamps from red to green and then does everything
 * an NVInteractableActor does (objective event, lines, sound). Actor origin sits on the wall surface at floor
 * height; local +X points out of the wall into the room. All parts are engine cubes, no collision except the housing.
 */
UCLASS()
class NEONVEIL_API ANVBreakerPanel : public ANVInteractableActor
{
	GENERATED_BODY()

public:
	ANVBreakerPanel();

	virtual void OnConstruction(const FTransform& Transform) override;
	virtual void BeginPlay() override;
	virtual void Tick(float DeltaSeconds) override;
	virtual void Interact_Implementation(AActor* Interactor) override;
	virtual void SetFocused_Implementation(bool bFocused) override;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Breaker|Look")
	TObjectPtr<UMaterialInterface> HousingMaterial;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Breaker|Look")
	TObjectPtr<UMaterialInterface> PlateMaterial;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Breaker|Look")
	TObjectPtr<UMaterialInterface> LeverMaterial;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Breaker|Look")
	TObjectPtr<UMaterialInterface> HazardMaterial;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Breaker|Look")
	TObjectPtr<UMaterialInterface> FuseMaterial;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Breaker|Look")
	TObjectPtr<UMaterialInterface> RedLitMaterial;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Breaker|Look")
	TObjectPtr<UMaterialInterface> GreenLitMaterial;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Breaker|Look")
	TObjectPtr<UMaterialInterface> LampOffMaterial;

	/** Lever pitch (degrees) when off (up) and on (thrown down). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Breaker")
	float OffPitch = -25.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Breaker")
	float OnPitch = -150.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Breaker", meta = (ClampMin = "0.05"))
	float ThrowTime = 0.35f;

protected:
	UPROPERTY(VisibleAnywhere, Category = "Components")
	TObjectPtr<UStaticMeshComponent> FacePlate;

	UPROPERTY(VisibleAnywhere, Category = "Components")
	TObjectPtr<UStaticMeshComponent> Hazard;

	UPROPERTY(VisibleAnywhere, Category = "Components")
	TObjectPtr<USceneComponent> LeverPivot;

	UPROPERTY(VisibleAnywhere, Category = "Components")
	TObjectPtr<UStaticMeshComponent> LeverArm;

	UPROPERTY(VisibleAnywhere, Category = "Components")
	TObjectPtr<UStaticMeshComponent> LeverGrip;

	UPROPERTY(VisibleAnywhere, Category = "Components")
	TObjectPtr<UStaticMeshComponent> LampRed;

	UPROPERTY(VisibleAnywhere, Category = "Components")
	TObjectPtr<UStaticMeshComponent> LampGreen;

	UPROPERTY(VisibleAnywhere, Category = "Components")
	TArray<TObjectPtr<UStaticMeshComponent>> Fuses;

private:
	void ApplyLook();
	void SetLamps(bool bOn);
	UStaticMeshComponent* MakePart(FName Name, USceneComponent* Parent, const FVector& Loc, const FVector& Size);

	float ThrowAlpha = 0.f;
	bool bThrowing = false;
};
