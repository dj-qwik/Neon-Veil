#pragma once

#include "CoreMinimal.h"
#include "GameFramework/PlayerController.h"
#include "NVPlayerController.generated.h"

/**
 * Owns the pause menu (Escape / gamepad Options; P as an editor-safe alternative, since Escape ends play-in-editor).
 * The menu is drawn by ANVHUD on the canvas; navigation works with keyboard, mouse and gamepad.
 */
UCLASS()
class NEONVEIL_API ANVPlayerController : public APlayerController
{
	GENERATED_BODY()

public:
	ANVPlayerController();

	bool IsPauseMenuOpen() const { return bPauseMenuOpen; }
	int32 GetPauseSelection() const { return PauseSelection; }
	static const TArray<FText>& GetPauseItems();

	/** Set by the HUD each frame it draws the menu: item rects in screen pixels, for mouse hover/click. */
	TArray<FBox2D> PauseItemRects;

	UFUNCTION(BlueprintCallable, Category = "NeonVeil|UI")
	void SetPauseMenuOpen(bool bOpen);

protected:
	virtual void SetupInputComponent() override;
	virtual void PlayerTick(float DeltaTime) override;

private:
	void TogglePauseMenu();
	void MenuUp();
	void MenuDown();
	void MenuConfirm();
	void MenuClick();
	void Activate(int32 Index);
	void QuitToDesktop();

	bool bPauseMenuOpen = false;
	int32 PauseSelection = 0;
};
