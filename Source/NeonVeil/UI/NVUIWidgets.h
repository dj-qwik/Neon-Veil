#pragma once

#include "CoreMinimal.h"
#include "Widgets/SCompoundWidget.h"
#include "Widgets/SLeafWidget.h"
#include "Widgets/DeclarativeSyntaxSupport.h"
#include "Styling/SlateColor.h"
#include "UI/NVUIStyle.h"
#include "GameplayTagContainer.h"

class STextBlock;

/**
 * GHOST-OS building blocks. Everything is drawn in code (no textures or Blueprints), so any screen can be
 * assembled from these in C++ and a UMG wrapper can be added later if designers want to lay screens out by hand.
 */

/** Smoked-glass panel with chamfered corners, scanlines, accent trims and a wipe-in / fade-out animation. */
class NEONVEIL_API SNVFrame : public SCompoundWidget
{
public:
	SLATE_BEGIN_ARGS(SNVFrame)
		: _Accent(NVUI::Accent)
		, _Cut(14.f)
		, _Padding(FMargin(18.f, 14.f))
		, _FillAlpha(1.f)
		, _Scanlines(true)
		, _Trims(true)
		, _Spine(false)
		, _AnimateIn(true)
		, _Delay(0.f)
	{}
		SLATE_ATTRIBUTE(FLinearColor, Accent)
		SLATE_ARGUMENT(float, Cut)
		SLATE_ARGUMENT(FMargin, Padding)
		SLATE_ARGUMENT(float, FillAlpha)
		SLATE_ARGUMENT(bool, Scanlines)
		SLATE_ARGUMENT(bool, Trims)
		/** Thick accent bar down the left edge (comms cards). */
		SLATE_ARGUMENT(bool, Spine)
		SLATE_ARGUMENT(bool, AnimateIn)
		SLATE_ARGUMENT(float, Delay)
		/** Optional mono header row ("// HEADER ———"). */
		SLATE_ARGUMENT(FText, Header)
		SLATE_DEFAULT_SLOT(FArguments, Content)
	SLATE_END_ARGS()

	void Construct(const FArguments& InArgs);

	/** Fade and collapse; IsGone() turns true when finished. */
	void PlayOut();
	bool IsGone() const;
	bool IsClosing() const { return OutStart > 0.0; }

	virtual int32 OnPaint(const FPaintArgs& Args, const FGeometry& AllottedGeometry, const FSlateRect& MyCullingRect,
	                      FSlateWindowElementList& OutDrawElements, int32 LayerId, const FWidgetStyle& InWidgetStyle, bool bParentEnabled) const override;

private:
	float Reveal() const;
	float OutAlpha() const;

	TAttribute<FLinearColor> Accent;
	float Cut = 14.f;
	float FillAlpha = 1.f;
	bool bScanlines = true;
	bool bTrims = true;
	bool bSpine = false;
	double StartTime = 0.0;
	double OutStart = -1.0;
};

/** Text that types itself out, with a scrambled leading edge and a blinking cursor. */
class NEONVEIL_API SNVTypeText : public SCompoundWidget
{
public:
	SLATE_BEGIN_ARGS(SNVTypeText)
		: _Font(NVUI::Font(NVUI::EFont::Body, 16.f))
		, _Color(FSlateColor(NVUI::Text))
		, _CharsPerSecond(70.f)
		, _AutoWrap(true)
		, _WrapAt(0.f)
		, _Delay(0.f)
		, _ShowCursor(true)
		, _Justify(ETextJustify::Left)
	{}
		SLATE_ARGUMENT(FText, Text)
		SLATE_ARGUMENT(FSlateFontInfo, Font)
		SLATE_ATTRIBUTE(FSlateColor, Color)
		SLATE_ARGUMENT(float, CharsPerSecond)
		SLATE_ARGUMENT(bool, AutoWrap)
		/** Fixed wrap width (use inside auto-sized containers, where AutoWrap can collapse). 0 = off. */
		SLATE_ARGUMENT(float, WrapAt)
		SLATE_ARGUMENT(float, Delay)
		SLATE_ARGUMENT(bool, ShowCursor)
		SLATE_ARGUMENT(ETextJustify::Type, Justify)
	SLATE_END_ARGS()

	void Construct(const FArguments& InArgs);
	void SetText(const FText& InText);
	bool IsFinished() const;
	/** Jump to the end (skip button). */
	void Finish();

private:
	FText GetShown() const;

	FString Full;
	float CharsPerSecond = 70.f;
	bool bCursor = true;
	double StartTime = 0.0;
};

/** Segmented bar (health, shield, hold progress, loading) with a trailing "damage ghost". */
class NEONVEIL_API SNVMeter : public SLeafWidget
{
public:
	SLATE_BEGIN_ARGS(SNVMeter)
		: _Value(1.f)
		, _Segments(20)
		, _Color(NVUI::Accent)
		, _Width(280.f)
		, _Height(8.f)
		, _Trail(true)
	{}
		SLATE_ATTRIBUTE(float, Value)
		SLATE_ARGUMENT(int32, Segments)
		SLATE_ATTRIBUTE(FLinearColor, Color)
		SLATE_ARGUMENT(float, Width)
		SLATE_ARGUMENT(float, Height)
		SLATE_ARGUMENT(bool, Trail)
	SLATE_END_ARGS()

	void Construct(const FArguments& InArgs);
	virtual FVector2D ComputeDesiredSize(float) const override { return FVector2D(Width, Height); }
	virtual int32 OnPaint(const FPaintArgs& Args, const FGeometry& AllottedGeometry, const FSlateRect& MyCullingRect,
	                      FSlateWindowElementList& OutDrawElements, int32 LayerId, const FWidgetStyle& InWidgetStyle, bool bParentEnabled) const override;

private:
	TAttribute<float> Value;
	TAttribute<FLinearColor> Color;
	int32 Segments = 20;
	float Width = 280.f;
	float Height = 8.f;
	bool bTrail = true;
	mutable float TrailValue = 1.f;
	mutable double LastPaint = 0.0;
};

/** Thin rule with an end diamond, fills its slot horizontally. */
class NEONVEIL_API SNVRule : public SLeafWidget
{
public:
	SLATE_BEGIN_ARGS(SNVRule) : _Color(NVUI::WithAlpha(NVUI::Accent, 0.45f)) {}
		SLATE_ATTRIBUTE(FLinearColor, Color)
	SLATE_END_ARGS()

	void Construct(const FArguments& InArgs) { Color = InArgs._Color; }
	virtual FVector2D ComputeDesiredSize(float) const override { return FVector2D(12.f, 7.f); }
	virtual int32 OnPaint(const FPaintArgs& Args, const FGeometry& AllottedGeometry, const FSlateRect& MyCullingRect,
	                      FSlateWindowElementList& OutDrawElements, int32 LayerId, const FWidgetStyle& InWidgetStyle, bool bParentEnabled) const override;

private:
	TAttribute<FLinearColor> Color;
};

/** Animated signal-strength bars (comms header). */
class NEONVEIL_API SNVSignal : public SLeafWidget
{
public:
	SLATE_BEGIN_ARGS(SNVSignal) : _Color(NVUI::Accent) {}
		SLATE_ATTRIBUTE(FLinearColor, Color)
	SLATE_END_ARGS()

	void Construct(const FArguments& InArgs) { Color = InArgs._Color; Seed = FMath::FRand() * 10.f; }
	virtual FVector2D ComputeDesiredSize(float) const override { return FVector2D(22.f, 12.f); }
	virtual int32 OnPaint(const FPaintArgs& Args, const FGeometry& AllottedGeometry, const FSlateRect& MyCullingRect,
	                      FSlateWindowElementList& OutDrawElements, int32 LayerId, const FWidgetStyle& InWidgetStyle, bool bParentEnabled) const override;

private:
	TAttribute<FLinearColor> Color;
	float Seed = 0.f;
};

/** Key / button glyph in a small chamfered cap: [E], [Triangle]. */
class NEONVEIL_API SNVKeyCap : public SCompoundWidget
{
public:
	SLATE_BEGIN_ARGS(SNVKeyCap) : _Color(NVUI::Accent), _Size(13.f) {}
		SLATE_ATTRIBUTE(FText, Key)
		SLATE_ATTRIBUTE(FLinearColor, Color)
		SLATE_ARGUMENT(float, Size)
	SLATE_END_ARGS()

	void Construct(const FArguments& InArgs);
	virtual int32 OnPaint(const FPaintArgs& Args, const FGeometry& AllottedGeometry, const FSlateRect& MyCullingRect,
	                      FSlateWindowElementList& OutDrawElements, int32 LayerId, const FWidgetStyle& InWidgetStyle, bool bParentEnabled) const override;

private:
	TAttribute<FLinearColor> Color;
};

/** Selectable row for menus and lists (mouse hover + click, or driven by a selection index). */
class NEONVEIL_API SNVButton : public SCompoundWidget
{
public:
	SLATE_BEGIN_ARGS(SNVButton) : _Size(20.f), _Enabled(true) {}
		SLATE_ATTRIBUTE(FText, Text)
		SLATE_ARGUMENT(FText, Index)
		SLATE_ARGUMENT(FText, Detail)
		SLATE_ARGUMENT(float, Size)
		SLATE_ARGUMENT(bool, Enabled)
		SLATE_ATTRIBUTE(bool, Selected)
		SLATE_EVENT(FSimpleDelegate, OnClicked)
		SLATE_EVENT(FSimpleDelegate, OnHovered)
	SLATE_END_ARGS()

	void Construct(const FArguments& InArgs);
	virtual void OnMouseEnter(const FGeometry& MyGeometry, const FPointerEvent& MouseEvent) override;
	virtual FReply OnMouseButtonDown(const FGeometry& MyGeometry, const FPointerEvent& MouseEvent) override;
	virtual FCursorReply OnCursorQuery(const FGeometry& MyGeometry, const FPointerEvent& CursorEvent) const override;
	virtual int32 OnPaint(const FPaintArgs& Args, const FGeometry& AllottedGeometry, const FSlateRect& MyCullingRect,
	                      FSlateWindowElementList& OutDrawElements, int32 LayerId, const FWidgetStyle& InWidgetStyle, bool bParentEnabled) const override;

private:
	bool IsSel() const { return Selected.Get(false) || IsHovered(); }
	TAttribute<bool> Selected;
	FSimpleDelegate OnClicked;
	FSimpleDelegate OnHovered;
	bool bEnabled = true;
	mutable float SelAnim = 0.f;
	mutable double LastPaint = 0.0;
};

/** Tab header for the menu shell. */
class NEONVEIL_API SNVTab : public SCompoundWidget
{
public:
	SLATE_BEGIN_ARGS(SNVTab) {}
		SLATE_ARGUMENT(FText, Text)
		SLATE_ATTRIBUTE(bool, Active)
		SLATE_EVENT(FSimpleDelegate, OnClicked)
	SLATE_END_ARGS()

	void Construct(const FArguments& InArgs);
	virtual FReply OnMouseButtonDown(const FGeometry& MyGeometry, const FPointerEvent& MouseEvent) override;
	virtual FCursorReply OnCursorQuery(const FGeometry& MyGeometry, const FPointerEvent& CursorEvent) const override;
	virtual int32 OnPaint(const FPaintArgs& Args, const FGeometry& AllottedGeometry, const FSlateRect& MyCullingRect,
	                      FSlateWindowElementList& OutDrawElements, int32 LayerId, const FWidgetStyle& InWidgetStyle, bool bParentEnabled) const override;

private:
	TAttribute<bool> Active;
	FSimpleDelegate OnClicked;
};

/** A GHOST-OS line icon. */
class NEONVEIL_API SNVIcon : public SLeafWidget
{
public:
	SLATE_BEGIN_ARGS(SNVIcon) : _Icon(NVUI::EIcon::Implant), _Color(NVUI::Accent), _Size(28.f) {}
		SLATE_ATTRIBUTE(NVUI::EIcon, Icon)
		SLATE_ATTRIBUTE(FLinearColor, Color)
		SLATE_ARGUMENT(float, Size)
	SLATE_END_ARGS()

	void Construct(const FArguments& InArgs) { Icon = InArgs._Icon; Color = InArgs._Color; Size = InArgs._Size; }
	virtual FVector2D ComputeDesiredSize(float) const override { return FVector2D(Size, Size); }
	virtual int32 OnPaint(const FPaintArgs& Args, const FGeometry& AllottedGeometry, const FSlateRect& MyCullingRect,
	                      FSlateWindowElementList& OutDrawElements, int32 LayerId, const FWidgetStyle& InWidgetStyle, bool bParentEnabled) const override;

private:
	TAttribute<NVUI::EIcon> Icon;
	TAttribute<FLinearColor> Color;
	float Size = 28.f;
};

namespace NVUI
{
	/** Icon for a cyberware ability tag (NV.Ability.*). */
	NEONVEIL_API EIcon IconForAbility(const FGameplayTag& AbilityTag);

	/** Shadowed text block in the house style. */
	NEONVEIL_API TSharedRef<STextBlock> MakeText(const TAttribute<FText>& InText, EFont Face, float Size,
	                                             const TAttribute<FSlateColor>& Color = FSlateColor(Text), int32 LetterSpacing = 0, bool bWrap = false);

	/** "// LABEL ———" header row. */
	NEONVEIL_API TSharedRef<SWidget> MakeHeader(const FText& InText, const FLinearColor& Color = Accent);
}
