#include "UI/NVUIWidgets.h"

#include "Widgets/Text/STextBlock.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/Layout/SBox.h"
#include "Rendering/DrawElements.h"


namespace
{
	float EaseOut(float T) { return 1.f - FMath::Pow(1.f - FMath::Clamp(T, 0.f, 1.f), 3.f); }

	float StepAnim(float& Value, double& Last, float Target, float Rate)
	{
		const double T = NVUI::Now();
		const float Dt = Last > 0.0 ? static_cast<float>(FMath::Min(T - Last, 0.1)) : 1.f;
		Last = T;
		Value = FMath::FInterpConstantTo(Value, Target, Dt, Rate);
		return Value;
	}
}

// ================================================================ helpers

TSharedRef<STextBlock> NVUI::MakeText(const TAttribute<FText>& InText, NVUI::EFont Face, float Size, const TAttribute<FSlateColor>& Color, int32 LetterSpacing, bool bWrap)
{
	return SNew(STextBlock)
		.Text(InText)
		.Font(NVUI::Font(Face, Size, LetterSpacing))
		.ColorAndOpacity(Color)
		.AutoWrapText(bWrap)
		.ShadowOffset(FVector2D(1.f, 1.f))
		.ShadowColorAndOpacity(FLinearColor(0.f, 0.f, 0.f, 0.6f));
}

TSharedRef<SWidget> NVUI::MakeHeader(const FText& InText, const FLinearColor& Color)
{
	return SNew(SHorizontalBox)
		+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center)
		[
			NVUI::MakeText(FText::Format(NSLOCTEXT("NeonVeil", "UIHeaderFmt", "// {0}"), InText.ToUpper()), NVUI::EFont::Mono, 12.f, FSlateColor(Color), 120)
		]
		+ SHorizontalBox::Slot().FillWidth(1.f).VAlign(VAlign_Center).Padding(10.f, 1.f, 0.f, 0.f)
		[
			SNew(SNVRule).Color(NVUI::WithAlpha(Color, 0.4f))
		];
}

// ================================================================ SNVFrame

void SNVFrame::Construct(const FArguments& InArgs)
{
	Accent = InArgs._Accent;
	Cut = InArgs._Cut;
	FillAlpha = InArgs._FillAlpha;
	bScanlines = InArgs._Scanlines;
	bTrims = InArgs._Trims;
	bSpine = InArgs._Spine;
	StartTime = InArgs._AnimateIn ? NVUI::Now() + InArgs._Delay : -100.0;

	TSharedRef<SWidget> Body = InArgs._Content.Widget;
	if (!InArgs._Header.IsEmpty())
	{
		Body = SNew(SVerticalBox)
			+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 0.f, 0.f, 8.f)
			[
				NVUI::MakeHeader(InArgs._Header, Accent.Get())
			]
			+ SVerticalBox::Slot().AutoHeight()
			[
				Body
			];
	}
	FMargin Pad = InArgs._Padding;
	if (bSpine)
	{
		Pad.Left += 6.f;
	}
	ChildSlot.Padding(Pad)
	[
		Body
	];
}

float SNVFrame::Reveal() const
{
	return FMath::Clamp(static_cast<float>((NVUI::Now() - StartTime) / 0.32), 0.f, 1.f);
}

float SNVFrame::OutAlpha() const
{
	return OutStart < 0.0 ? 1.f : 1.f - FMath::Clamp(static_cast<float>((NVUI::Now() - OutStart) / 0.25), 0.f, 1.f);
}

void SNVFrame::PlayOut()
{
	if (OutStart < 0.0)
	{
		OutStart = NVUI::Now();
	}
}

bool SNVFrame::IsGone() const
{
	return OutStart > 0.0 && NVUI::Now() - OutStart >= 0.25;
}

int32 SNVFrame::OnPaint(const FPaintArgs& Args, const FGeometry& G, const FSlateRect& Culling, FSlateWindowElementList& Out,
                        int32 LayerId, const FWidgetStyle& Style, bool bParentEnabled) const
{
	const float R = Reveal();
	if (R <= 0.f)
	{
		return LayerId;
	}
	const float Alpha = OutAlpha();
	const FVector2f Size(G.GetLocalSize());
	const float H = Size.Y;
	const float W = FMath::Max(Cut * 2.f + 4.f, Size.X * EaseOut(R));
	const float C = FMath::Min(Cut, FMath::Min(W, H) * 0.5f);
	const FLinearColor Tint = Style.GetColorAndOpacityTint() * FLinearColor(1.f, 1.f, 1.f, Alpha);
	const FLinearColor Acc = Accent.Get();

	NVUI::FPainter P(G, Tint);
	P.PolyV(NVUI::ChamferPoints(FVector2f::ZeroVector, FVector2f(W, H), C, false), NVUI::WithAlpha(NVUI::GlassLight, FillAlpha), NVUI::WithAlpha(NVUI::Glass, FillAlpha));
	if (bScanlines)
	{
		for (float Y = 2.f; Y < H - 1.f; Y += 3.f)
		{
			const float X0 = Y < C ? C - Y : 0.f;
			const float X1 = Y > H - C ? W - (Y - (H - C)) : W;
			P.Rect(FVector2f(X0, Y), FVector2f(X1 - X0, 1.f), FLinearColor(1.f, 1.f, 1.f, 0.02f));
		}
		// slow glint band drifting down the glass
		const float Band = static_cast<float>(FMath::Frac(NVUI::Now() * 0.12 + StartTime * 0.37)) * (H + 60.f) - 30.f;
		const float B0 = FMath::Clamp(Band - 18.f, C, H - C), B1 = FMath::Clamp(Band + 18.f, C, H - C);
		if (B1 > B0)
		{
			P.RectV(FVector2f(0.f, B0), FVector2f(W, (B1 - B0) * 0.5f), FLinearColor(1.f, 1.f, 1.f, 0.f), NVUI::WithAlpha(Acc, 0.035f));
			P.RectV(FVector2f(0.f, (B0 + B1) * 0.5f), FVector2f(W, (B1 - B0) * 0.5f), NVUI::WithAlpha(Acc, 0.035f), FLinearColor(1.f, 1.f, 1.f, 0.f));
		}
	}
	if (bSpine)
	{
		P.Rect(FVector2f(0.f, C), FVector2f(3.f, H - C), Acc);
		P.RectH(FVector2f(3.f, C), FVector2f(18.f, H - C), NVUI::WithAlpha(Acc, 0.12f), NVUI::WithAlpha(Acc, 0.f));
	}
	if (bTrims)
	{
		P.Rect(FVector2f(C, 0.f), FVector2f(FMath::Min(96.f, W * 0.35f), 2.f), Acc);
		for (int32 i = 0; i < 3; ++i)
		{
			P.Rect(FVector2f(W - C - 14.f - i * 9.f, H - 5.f), FVector2f(6.f, 2.f), NVUI::WithAlpha(Acc, 0.75f));
		}
		P.Rect(FVector2f(W - 6.f, 4.f), FVector2f(2.f, 2.f), NVUI::WithAlpha(Acc, 0.85f));
	}
	if (R < 1.f)
	{
		// wipe edge
		P.RectH(FVector2f(W - 28.f, 0.f), FVector2f(28.f, H), NVUI::WithAlpha(Acc, 0.f), NVUI::WithAlpha(Acc, 0.3f));
		P.Rect(FVector2f(W - 2.f, 0.f), FVector2f(2.f, H), Acc);
	}
	P.Flush(Out, LayerId);

	const TArray<FVector2f> Outline = NVUI::ChamferPoints(FVector2f(0.5f, 0.5f), FVector2f(W - 1.f, H - 1.f), C, true);
	NVUI::Lines(Out, LayerId + 1, G, Outline, NVUI::WithAlpha(Acc, 0.3f) * Tint, 1.f);
	NVUI::Lines(Out, LayerId + 1, G, { Outline[5], Outline[0] }, Acc * Tint, 1.5f);
	NVUI::Lines(Out, LayerId + 1, G, { Outline[2], Outline[3] }, Acc * Tint, 1.5f);

	float ContentA = FMath::Clamp((R - 0.45f) / 0.4f, 0.f, 1.f) * Alpha;
	if (R < 1.f && FMath::Frac(NVUI::Now() * 28.0) < 0.3)
	{
		ContentA *= 0.35f;
	}
	FWidgetStyle CS(Style);
	CS.BlendColorAndOpacityTint(FLinearColor(1.f, 1.f, 1.f, ContentA));
	return SCompoundWidget::OnPaint(Args, G, Culling, Out, LayerId + 2, CS, bParentEnabled);
}

// ================================================================ SNVTypeText

void SNVTypeText::Construct(const FArguments& InArgs)
{
	Full = InArgs._Text.ToString();
	CharsPerSecond = FMath::Max(1.f, InArgs._CharsPerSecond);
	bCursor = InArgs._ShowCursor;
	StartTime = NVUI::Now() + InArgs._Delay;
	ChildSlot
	[
		SNew(STextBlock)
		.Text(this, &SNVTypeText::GetShown)
		.Font(InArgs._Font)
		.ColorAndOpacity(InArgs._Color)
		.AutoWrapText(InArgs._AutoWrap && InArgs._WrapAt <= 0.f)
		.WrapTextAt(InArgs._WrapAt)
		.Justification(InArgs._Justify)
		.ShadowOffset(FVector2D(1.f, 1.f))
		.ShadowColorAndOpacity(FLinearColor(0.f, 0.f, 0.f, 0.65f))
	];
}

void SNVTypeText::SetText(const FText& InText)
{
	Full = InText.ToString();
	StartTime = NVUI::Now();
}

bool SNVTypeText::IsFinished() const
{
	return (NVUI::Now() - StartTime) * CharsPerSecond >= Full.Len();
}

void SNVTypeText::Finish()
{
	StartTime = NVUI::Now() - (Full.Len() + 1) / CharsPerSecond;
}

FText SNVTypeText::GetShown() const
{
	const double TNow = NVUI::Now();
	const double T = TNow - StartTime;
	if (T < 0.0)
	{
		return FText::GetEmpty();
	}
	const int32 N = FMath::Min(Full.Len(), static_cast<int32>(T * CharsPerSecond));
	FString S = Full.Left(N);
	if (N < Full.Len())
	{
		static const TCHAR Glyphs[] = TEXT("#$%&*+/<=>?@[]_{|}~01");
		const int32 NG = UE_ARRAY_COUNT(Glyphs) - 1;
		const int32 Frame = static_cast<int32>(TNow * 30.0);
		for (int32 k = 0; k < 2 && N + k < Full.Len(); ++k)
		{
			if (FChar::IsWhitespace(Full[N + k]))
			{
				break;
			}
			S.AppendChar(Glyphs[FMath::Abs(Frame * 7 + k * 13 + N) % NG]);
		}
		if (bCursor)
		{
			S.AppendChar(TEXT('_'));
		}
	}
	else if (bCursor && T * CharsPerSecond < Full.Len() + CharsPerSecond * 1.5 && FMath::Frac(TNow * 2.5) < 0.5)
	{
		S.AppendChar(TEXT('_'));
	}
	return FText::FromString(S);
}

// ================================================================ SNVMeter

void SNVMeter::Construct(const FArguments& InArgs)
{
	Value = InArgs._Value;
	Color = InArgs._Color;
	Segments = FMath::Max(1, InArgs._Segments);
	Width = InArgs._Width;
	Height = InArgs._Height;
	bTrail = InArgs._Trail;
	TrailValue = FMath::Clamp(Value.Get(), 0.f, 1.f);
}

int32 SNVMeter::OnPaint(const FPaintArgs& Args, const FGeometry& G, const FSlateRect& Culling, FSlateWindowElementList& Out,
                        int32 LayerId, const FWidgetStyle& Style, bool bParentEnabled) const
{
	const FVector2f Size(G.GetLocalSize());
	const float V = FMath::Clamp(Value.Get(), 0.f, 1.f);
	const double TNow = NVUI::Now();
	const float Dt = LastPaint > 0.0 ? static_cast<float>(FMath::Min(TNow - LastPaint, 0.1)) : 0.f;
	LastPaint = TNow;
	TrailValue = V >= TrailValue ? V : FMath::Max(V, TrailValue - Dt * 0.35f);

	const FLinearColor C = Color.Get();
	const FLinearColor CDark(C.R * 0.6f, C.G * 0.6f, C.B * 0.6f, C.A);
	const float Gap = Segments > 1 ? 2.f : 0.f;
	const float SegW = (Size.X - Gap * (Segments - 1)) / Segments;
	NVUI::FPainter P(G, Style.GetColorAndOpacityTint());
	for (int32 i = 0; i < Segments; ++i)
	{
		const float X = i * (SegW + Gap);
		const float F0 = static_cast<float>(i) / Segments, F1 = static_cast<float>(i + 1) / Segments;
		const float Fill = FMath::Clamp((V - F0) / (F1 - F0), 0.f, 1.f);
		const float TrailF = FMath::Clamp((TrailValue - F0) / (F1 - F0), 0.f, 1.f);
		P.Rect(FVector2f(X, 0.f), FVector2f(SegW, Size.Y), NVUI::WithAlpha(C, 0.13f));
		if (Fill > 0.f)
		{
			P.RectV(FVector2f(X, 0.f), FVector2f(SegW * Fill, Size.Y), C, CDark);
		}
		if (bTrail && TrailF > Fill)
		{
			P.Rect(FVector2f(X + SegW * Fill, 0.f), FVector2f(SegW * (TrailF - Fill), Size.Y), FLinearColor(1.f, 1.f, 1.f, 0.5f));
		}
	}
	if (V > 0.f)
	{
		P.RectV(FVector2f(0.f, -4.f), FVector2f(Size.X * V, 4.f), NVUI::WithAlpha(C, 0.f), NVUI::WithAlpha(C, 0.22f));
	}
	return P.Flush(Out, LayerId);
}

// ================================================================ SNVRule / SNVSignal

int32 SNVRule::OnPaint(const FPaintArgs& Args, const FGeometry& G, const FSlateRect& Culling, FSlateWindowElementList& Out,
                       int32 LayerId, const FWidgetStyle& Style, bool bParentEnabled) const
{
	const FVector2f S(G.GetLocalSize());
	const FLinearColor C = Color.Get();
	NVUI::FPainter P(G, Style.GetColorAndOpacityTint());
	P.RectH(FVector2f(0.f, FMath::FloorToFloat(S.Y * 0.5f)), FVector2f(FMath::Max(0.f, S.X - 9.f), 1.f), C, NVUI::WithAlpha(C, 0.35f));
	P.Diamond(FVector2f(S.X - 3.5f, S.Y * 0.5f), 3.f, C);
	return P.Flush(Out, LayerId);
}

int32 SNVSignal::OnPaint(const FPaintArgs& Args, const FGeometry& G, const FSlateRect& Culling, FSlateWindowElementList& Out,
                         int32 LayerId, const FWidgetStyle& Style, bool bParentEnabled) const
{
	const FVector2f S(G.GetLocalSize());
	const FLinearColor C = Color.Get();
	const float Wobble = FMath::Sin(static_cast<float>(NVUI::Now()) * 3.1f + Seed) + FMath::Sin(static_cast<float>(NVUI::Now()) * 7.3f + Seed * 2.f) * 0.5f;
	const int32 Lit = Wobble > 0.8f ? 4 : (Wobble > -0.9f ? 3 : 2);
	NVUI::FPainter P(G, Style.GetColorAndOpacityTint());
	for (int32 i = 0; i < 4; ++i)
	{
		const float BH = S.Y * (0.3f + 0.7f * i / 3.f);
		P.Rect(FVector2f(i * 5.5f, S.Y - BH), FVector2f(3.5f, BH), i < Lit ? C : NVUI::WithAlpha(C, 0.2f));
	}
	return P.Flush(Out, LayerId);
}

// ================================================================ SNVKeyCap

void SNVKeyCap::Construct(const FArguments& InArgs)
{
	Color = InArgs._Color;
	TAttribute<FLinearColor> Col = InArgs._Color;
	ChildSlot.Padding(FMargin(8.f, 2.f, 8.f, 1.f)).HAlign(HAlign_Center).VAlign(VAlign_Center)
	[
		NVUI::MakeText(InArgs._Key, NVUI::EFont::Mono, InArgs._Size, TAttribute<FSlateColor>::CreateLambda([Col]() { return FSlateColor(Col.Get()); }), 40)
	];
}

int32 SNVKeyCap::OnPaint(const FPaintArgs& Args, const FGeometry& G, const FSlateRect& Culling, FSlateWindowElementList& Out,
                         int32 LayerId, const FWidgetStyle& Style, bool bParentEnabled) const
{
	const FVector2f S(G.GetLocalSize());
	const FLinearColor C = Color.Get();
	const FLinearColor Tint = Style.GetColorAndOpacityTint();
	NVUI::FPainter P(G, Tint);
	P.Poly(NVUI::ChamferPoints(FVector2f::ZeroVector, S, 5.f, false), FLinearColor(0.f, 0.02f, 0.03f, 0.75f));
	P.Rect(FVector2f(2.f, S.Y - 3.f), FVector2f(S.X - 9.f, 1.f), NVUI::WithAlpha(C, 0.35f));
	P.Flush(Out, LayerId);
	NVUI::Lines(Out, LayerId + 1, G, NVUI::ChamferPoints(FVector2f(0.5f, 0.5f), S - FVector2f(1.f, 1.f), 5.f, true), NVUI::WithAlpha(C, 0.85f) * Tint, 1.f);
	return SCompoundWidget::OnPaint(Args, G, Culling, Out, LayerId + 2, Style, bParentEnabled);
}

// ================================================================ SNVButton

void SNVButton::Construct(const FArguments& InArgs)
{
	Selected = InArgs._Selected;
	OnClicked = InArgs._OnClicked;
	OnHovered = InArgs._OnHovered;
	bEnabled = InArgs._Enabled;

	auto MainColor = TAttribute<FSlateColor>::CreateLambda([this]()
	{
		if (!bEnabled)
		{
			return FSlateColor(NVUI::WithAlpha(NVUI::TextDim, 0.5f));
		}
		return FSlateColor(IsSel() ? NVUI::Accent : NVUI::Text);
	});
	auto IndexColor = TAttribute<FSlateColor>::CreateLambda([this]()
	{
		return FSlateColor(IsSel() ? NVUI::Accent : NVUI::WithAlpha(NVUI::TextDim, 0.8f));
	});

	ChildSlot.Padding(FMargin(18.f, 8.f, 22.f, 8.f))
	[
		SNew(SHorizontalBox)
		+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(0.f, 0.f, 14.f, 0.f)
		[
			NVUI::MakeText(InArgs._Index, NVUI::EFont::Mono, 12.f, IndexColor)
		]
		+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center)
		[
			NVUI::MakeText(InArgs._Text, NVUI::EFont::BodySemi, InArgs._Size, MainColor, 60)
		]
		+ SHorizontalBox::Slot().FillWidth(1.f).HAlign(HAlign_Right).VAlign(VAlign_Center).Padding(24.f, 0.f, 0.f, 0.f)
		[
			NVUI::MakeText(InArgs._Detail, NVUI::EFont::Mono, 11.f, FSlateColor(NVUI::WithAlpha(NVUI::TextDim, 0.8f)))
		]
	];
}

void SNVButton::OnMouseEnter(const FGeometry& MyGeometry, const FPointerEvent& MouseEvent)
{
	SCompoundWidget::OnMouseEnter(MyGeometry, MouseEvent);
	OnHovered.ExecuteIfBound();
}

FReply SNVButton::OnMouseButtonDown(const FGeometry& MyGeometry, const FPointerEvent& MouseEvent)
{
	if (MouseEvent.GetEffectingButton() == EKeys::LeftMouseButton && bEnabled)
	{
		OnClicked.ExecuteIfBound();
		return FReply::Handled();
	}
	return FReply::Unhandled();
}

FCursorReply SNVButton::OnCursorQuery(const FGeometry& MyGeometry, const FPointerEvent& CursorEvent) const
{
	return FCursorReply::Cursor(bEnabled ? EMouseCursor::Hand : EMouseCursor::Default);
}

int32 SNVButton::OnPaint(const FPaintArgs& Args, const FGeometry& G, const FSlateRect& Culling, FSlateWindowElementList& Out,
                         int32 LayerId, const FWidgetStyle& Style, bool bParentEnabled) const
{
	const float A = StepAnim(SelAnim, LastPaint, IsSel() && bEnabled ? 1.f : 0.f, 9.f);
	const FVector2f S(G.GetLocalSize());
	NVUI::FPainter P(G, Style.GetColorAndOpacityTint());
	P.Rect(FVector2f(0.f, S.Y - 1.f), FVector2f(S.X, 1.f), NVUI::WithAlpha(NVUI::Accent, 0.07f));
	if (A > 0.f)
	{
		const float W = S.X * (0.35f + 0.65f * EaseOut(A));
		P.RectH(FVector2f(0.f, 0.f), FVector2f(W, S.Y), NVUI::WithAlpha(NVUI::Accent, 0.24f * A), NVUI::WithAlpha(NVUI::Accent, 0.f));
		P.Rect(FVector2f(0.f, 0.f), FVector2f(3.f, S.Y), NVUI::WithAlpha(NVUI::Accent, A));
		P.Diamond(FVector2f(S.X - 9.f, S.Y * 0.5f), 3.5f * A, NVUI::WithAlpha(NVUI::Accent, A));
	}
	P.Flush(Out, LayerId);
	return SCompoundWidget::OnPaint(Args, G, Culling, Out, LayerId + 1, Style, bParentEnabled);
}

// ================================================================ SNVTab

void SNVTab::Construct(const FArguments& InArgs)
{
	Active = InArgs._Active;
	OnClicked = InArgs._OnClicked;
	auto Col = TAttribute<FSlateColor>::CreateLambda([this]()
	{
		return FSlateColor(Active.Get(false) ? NVUI::Text : (IsHovered() ? NVUI::Accent : NVUI::TextDim));
	});
	ChildSlot.Padding(FMargin(18.f, 10.f, 18.f, 12.f))
	[
		NVUI::MakeText(InArgs._Text.ToUpper(), NVUI::EFont::Display, 12.f, Col, 220)
	];
}

FReply SNVTab::OnMouseButtonDown(const FGeometry& MyGeometry, const FPointerEvent& MouseEvent)
{
	if (MouseEvent.GetEffectingButton() == EKeys::LeftMouseButton)
	{
		OnClicked.ExecuteIfBound();
		return FReply::Handled();
	}
	return FReply::Unhandled();
}

FCursorReply SNVTab::OnCursorQuery(const FGeometry& MyGeometry, const FPointerEvent& CursorEvent) const
{
	return FCursorReply::Cursor(EMouseCursor::Hand);
}

int32 SNVTab::OnPaint(const FPaintArgs& Args, const FGeometry& G, const FSlateRect& Culling, FSlateWindowElementList& Out,
                      int32 LayerId, const FWidgetStyle& Style, bool bParentEnabled) const
{
	const FVector2f S(G.GetLocalSize());
	NVUI::FPainter P(G, Style.GetColorAndOpacityTint());
	if (Active.Get(false))
	{
		P.RectV(FVector2f(0.f, 0.f), FVector2f(S.X, S.Y), NVUI::WithAlpha(NVUI::Accent, 0.f), NVUI::WithAlpha(NVUI::Accent, 0.16f));
		P.Rect(FVector2f(0.f, S.Y - 2.f), FVector2f(S.X, 2.f), NVUI::Accent);
		P.Diamond(FVector2f(S.X * 0.5f, S.Y - 1.f), 4.f, NVUI::Accent);
	}
	else if (IsHovered())
	{
		P.Rect(FVector2f(0.f, S.Y - 1.f), FVector2f(S.X, 1.f), NVUI::WithAlpha(NVUI::Accent, 0.5f));
	}
	P.Flush(Out, LayerId);
	return SCompoundWidget::OnPaint(Args, G, Culling, Out, LayerId + 1, Style, bParentEnabled);
}
