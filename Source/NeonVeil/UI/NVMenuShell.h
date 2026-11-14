#pragma once

#include "CoreMinimal.h"
#include "Widgets/SCompoundWidget.h"
#include "Widgets/DeclarativeSyntaxSupport.h"

class ANVHUD;
class ANVPlayerController;

/** What a menu page can reach when it builds itself. */
struct FNVMenuContext
{
	TWeakObjectPtr<ANVHUD> HUD;
	TWeakObjectPtr<ANVPlayerController> PC;
};

/**
 * One tab of the GHOST-OS menu. Future systems (cyberware loadout, upgrades, skill trees, codex, settings) plug in by
 * registering a page with the same Id to replace a placeholder, or a new Id to add a tab.
 */
struct FNVMenuPage
{
	FName Id;
	FText Label;
	TFunction<TSharedRef<SWidget>(const FNVMenuContext&)> Build;
};

namespace NVUI
{
	/** Registered pages in tab order (SYSTEM, CYBERWARE, UPGRADES, SKILLS, COMMS by default). */
	NEONVEIL_API TArray<FNVMenuPage>& MenuPages();

	/** Adds a page, or replaces the page with the same Id. InsertAt < 0 appends. */
	NEONVEIL_API void RegisterMenuPage(const FNVMenuPage& Page, int32 InsertAt = INDEX_NONE);
}

/** Full-screen pause / system menu: backdrop, title bar with tabs, the active page, and input hints. */
class NEONVEIL_API SNVMenuShell : public SCompoundWidget
{
public:
	SLATE_BEGIN_ARGS(SNVMenuShell) {}
		SLATE_ARGUMENT(FNVMenuContext, Context)
	SLATE_END_ARGS()

	void Construct(const FArguments& InArgs);
	virtual int32 OnPaint(const FPaintArgs& Args, const FGeometry& AllottedGeometry, const FSlateRect& MyCullingRect,
	                      FSlateWindowElementList& OutDrawElements, int32 LayerId, const FWidgetStyle& InWidgetStyle, bool bParentEnabled) const override;

private:
	FNVMenuContext Ctx;
	double OpenTime = 0.0;
};
