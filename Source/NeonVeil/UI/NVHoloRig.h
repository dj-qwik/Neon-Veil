#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "NVHoloRig.generated.h"

class USkeletalMeshComponent;
class USceneCaptureComponent2D;
class UTextureRenderTarget2D;
class UMaterialInstanceDynamic;

/**
 * Off-world turntable for the GHOST-OS cyberware page: a copy of the operative's body in an unlit hologram material,
 * idling, captured by an orthographic scene capture into a render target. The menu shows the capture through a UI
 * material (brightness = opacity) and lays the implant callouts over it. Lives far below the level, captures only
 * while the page is on screen, and keeps working while the game is paused.
 */
UCLASS(NotPlaceable, Transient)
class NEONVEIL_API ANVHoloRig : public AActor
{
	GENERATED_BODY()

public:
	ANVHoloRig();

	/** The rig for this world, spawned on first use and dressed with the player's body mesh. */
	static ANVHoloRig* Get(UWorld* World, USkeletalMesh* Body);

	/** Call every frame the hologram is visible; capture stops a moment after the last call. */
	void Touch();

	UMaterialInstanceDynamic* GetPresenter() const { return Presenter; }

	/** Where a bone of the hologram body (plus a world-space offset) lands in the widget's local units (see BoxW/BoxH). */
	bool ProjectBone(FName Bone, const FVector& Offset, FVector2f& OutUnits) const;

	/** Local units used by the body-scan widget: a 460 x 540 box, Y = 5 at the head top, Y = 470 at the soles. */
	static constexpr float BoxW = 460.f;
	static constexpr float BoxH = 540.f;

	virtual void Tick(float DeltaSeconds) override;

protected:
	virtual void BeginPlay() override;

private:
	void SetBody(USkeletalMesh* Body);
	void Frame();

	UPROPERTY(VisibleAnywhere)
	TObjectPtr<USceneComponent> Root;

	UPROPERTY(VisibleAnywhere)
	TObjectPtr<USceneComponent> Turntable;

	UPROPERTY(VisibleAnywhere)
	TObjectPtr<USkeletalMeshComponent> Body;

	UPROPERTY(VisibleAnywhere)
	TObjectPtr<USceneCaptureComponent2D> Capture;

	UPROPERTY(Transient)
	TObjectPtr<UTextureRenderTarget2D> Target;

	UPROPERTY(Transient)
	TObjectPtr<UMaterialInstanceDynamic> Presenter;

	double LastTouch = -100.0;
	float CmPerUnit = 0.4f;
	float CentreZ = 90.f;
	float Age = 0.f;
};
