#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "NVRoomLightSwitch.generated.h"

class ANVInteractableActor;
class ULightComponent;
class UMeshComponent;
class UMaterialInterface;
class USoundBase;

/**
 * Two-state room lighting, driven by any number of switch panels: "show" mode (as authored: dim room, holograms
 * on) and "work lights" (room lights brought up, the dimmed *_Atrium material copies swapped back to their parents,
 * holograms flicker off). Each use toggles; the change ramps over RampTime. Panel prompts follow the state.
 */
UCLASS()
class NEONVEIL_API ANVRoomLightSwitch : public AActor
{
	GENERATED_BODY()

public:
	ANVRoomLightSwitch();
	virtual void BeginPlay() override;
	virtual void Tick(float DeltaSeconds) override;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Switch")
	TArray<TObjectPtr<ANVInteractableActor>> Panels;

	/** Lights brought up by BrightScale (their authored, dimmed intensity is the "show" level). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Switch")
	TArray<TObjectPtr<AActor>> Lights;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Switch")
	float BrightScale = 6.3f;

	/** Actors whose mesh materials named "*<DimSuffix>" are swapped to their parent material in work-light mode. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Switch")
	TArray<TObjectPtr<AActor>> MaterialActors;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Switch")
	FString DimSuffix = TEXT("_Atrium");

	/** Holograms hidden (with their lights) in work-light mode. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Switch")
	TArray<TObjectPtr<AActor>> Holograms;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Switch")
	float RampTime = 1.4f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Switch")
	FText PromptLightsUp = NSLOCTEXT("NeonVeil", "RoomLightsUp", "Raise room lights");

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Switch")
	FText PromptShow = NSLOCTEXT("NeonVeil", "RoomShow", "Dim lights / start orrery");

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Switch")
	TObjectPtr<USoundBase> LightsUpSound;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Switch")
	TObjectPtr<USoundBase> ShowSound;

	/** Glitchy flicker played at the first hologram as it cuts out / powers back on. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Switch")
	TObjectPtr<USoundBase> HologramOffSound;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Switch")
	TObjectPtr<USoundBase> HologramOnSound;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Switch")
	float HologramSoundVolume = 1.2f;

	UFUNCTION(BlueprintCallable, Category = "NeonVeil")
	void Toggle();

	UFUNCTION(BlueprintPure, Category = "NeonVeil")
	bool AreWorkLightsOn() const { return bWorkLights; }

private:
	UFUNCTION()
	void HandleUsed(ANVInteractableActor* Interactable, AActor* Interactor);

	void SetMaterials(bool bParent);
	void SetHologramsVisible(bool bVisible);
	void UpdatePrompts();

	struct FLightBase { TWeakObjectPtr<ULightComponent> Light; float Base; };
	struct FMatSlot { TWeakObjectPtr<UMeshComponent> Mesh; int32 Index; TWeakObjectPtr<UMaterialInterface> Dim; TWeakObjectPtr<UMaterialInterface> Full; };
	TArray<FLightBase> LightBases;
	TArray<FMatSlot> MatSlots;
	bool bWorkLights = false;
	bool bMaterialsFull = false;
	float Alpha = 0.f;        // 0 = show, 1 = work lights
	float FlickerTime = -1.f; // >= 0 while the holograms flicker out / in
	float NextFlicker = 0.f;
};
