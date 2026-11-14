#pragma once

#include "CoreMinimal.h"
#include "GameFramework/PlayerController.h"
#include "NVPlayerController.generated.h"

/**
 * Owns the pause menu (Escape / gamepad Options; P as an editor-safe alternative, since Escape ends play-in-editor).
 * The menu is the GHOST-OS shell (UI/NVMenuShell): tabs switch with Q / E or the shoulder buttons,
 * the SYSTEM tab's items with W / S, arrows, D-pad, Enter / Cross, or the mouse.
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

	/** Menu shell tab (index into NVUI::MenuPages()). */
	int32 GetMenuTab() const { return MenuTab; }
	void SetMenuTab(int32 Tab);
	void SetPauseSelection(int32 Index);
	/** Runs a SYSTEM item (mouse click from the menu shell). */
	void ActivatePauseItem(int32 Index) { Activate(Index); }

	UFUNCTION(BlueprintCallable, Category = "NeonVeil|UI")
	void SetPauseMenuOpen(bool bOpen);

protected:
	virtual void SetupInputComponent() override;

private:
	void TogglePauseMenu();
	void MenuUp();
	void MenuDown();
	void MenuConfirm();
	void MenuPrevTab();
	void MenuNextTab();
	void Activate(int32 Index);
	void QuitToDesktop();

	bool bPauseMenuOpen = false;
	int32 PauseSelection = 0;
	int32 MenuTab = 0;
};
