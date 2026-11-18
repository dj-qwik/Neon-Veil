#pragma once

#include "CoreMinimal.h"
#include "Widgets/SLeafWidget.h"
#include "Widgets/DeclarativeSyntaxSupport.h"

/**
 * Full-screen opening title for the prologue. Letterbox bars close in, the title resolves out of an RGB-split glitch,
 * a rule draws out under it, then the act line and place line type in. Everything fades after Duration seconds.
 * Painted entirely in OnPaint, on the UI clock (keeps time while paused).
 */
class NEONVEIL_API SNVOpeningTitle : public SLeafWidget
{
public:
	SLATE_BEGIN_ARGS(SNVOpeningTitle) : _Duration(8.f) {}
		SLATE_ARGUMENT(FText, Title)
		SLATE_ARGUMENT(FText, Subtitle)
		SLATE_ARGUMENT(FText, Tagline)
		SLATE_ARGUMENT(float, Duration)
	SLATE_END_ARGS()

	void Construct(const FArguments& InArgs);
	bool IsFinished() const;

	virtual FVector2D ComputeDesiredSize(float) const override { return FVector2D(1920.f, 1080.f); }
	virtual int32 OnPaint(const FPaintArgs& Args, const FGeometry& AllottedGeometry, const FSlateRect& MyCullingRect,
	                      FSlateWindowElementList& OutDrawElements, int32 LayerId, const FWidgetStyle& InWidgetStyle, bool bParentEnabled) const override;

private:
	FString Title;
	FString Subtitle;
	FString Tagline;
	float Duration = 8.f;
	double Start = 0.0;
};
