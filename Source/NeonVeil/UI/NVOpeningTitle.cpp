#include "UI/NVOpeningTitle.h"
#include "UI/NVUIStyle.h"

#include "Framework/Application/SlateApplication.h"
#include "Fonts/FontMeasure.h"
#include "Rendering/DrawElements.h"
#include "Rendering/SlateRenderer.h"

namespace
{
	float Ease(float T) { return 1.f - FMath::Pow(1.f - FMath::Clamp(T, 0.f, 1.f), 3.f); }
	float Hash(int32 N) { return FMath::Frac(FMath::Sin(N * 12.9898f) * 43758.5453f); }

	FVector2f Measure(const FString& S, const FSlateFontInfo& F)
	{
		return FVector2f(FSlateApplication::Get().GetRenderer()->GetFontMeasureService()->Measure(S, F));
	}

	void Text(FSlateWindowElementList& Out, int32 Layer, const FGeometry& G, const FString& S, const FSlateFontInfo& F,
	          const FVector2f& Pos, const FLinearColor& C)
	{
		if (S.IsEmpty() || C.A <= 0.002f)
		{
			return;
		}
		const FVector2f Size = Measure(S, F);
		FSlateDrawElement::MakeText(Out, Layer, G.ToPaintGeometry(Size, FSlateLayoutTransform(Pos)), S, F, ESlateDrawEffect::None, C);
	}
}

void SNVOpeningTitle::Construct(const FArguments& InArgs)
{
	Title = InArgs._Title.ToString().ToUpper();
	Subtitle = InArgs._Subtitle.ToString().ToUpper();
	Tagline = InArgs._Tagline.ToString().ToUpper();
	Duration = FMath::Max(3.f, InArgs._Duration);
	Start = NVUI::Now();
	SetVisibility(EVisibility::HitTestInvisible);
}

bool SNVOpeningTitle::IsFinished() const
{
	return NVUI::Now() - Start > Duration + 0.2;
}

int32 SNVOpeningTitle::OnPaint(const FPaintArgs& Args, const FGeometry& G, const FSlateRect& Culling, FSlateWindowElementList& Out, int32 LayerId,
                               const FWidgetStyle& Style, bool bParentEnabled) const
{
	const float T = static_cast<float>(NVUI::Now() - Start);
	const float A = FMath::Clamp(T / 0.5f, 0.f, 1.f) * FMath::Clamp((Duration - T) / 1.4f, 0.f, 1.f);
	if (A <= 0.f)
	{
		return LayerId;
	}
	const FVector2f S(G.GetLocalSize());
	const float K = S.Y / 1080.f;
	const FLinearColor Tint = Style.GetColorAndOpacityTint();

	// ---- backdrop: letterbox bars, a smoked band behind the title, scanlines
	NVUI::FPainter P(G, Tint * FLinearColor(1.f, 1.f, 1.f, A));
	const float Bar = S.Y * 0.105f * Ease(T / 0.9f);
	P.Rect(FVector2f(0.f, 0.f), FVector2f(S.X, Bar), FLinearColor::Black);
	P.Rect(FVector2f(0.f, S.Y - Bar), FVector2f(S.X, Bar), FLinearColor::Black);
	const float BandTop = S.Y * 0.30f, BandH = S.Y * 0.40f;
	P.RectV(FVector2f(0.f, BandTop), FVector2f(S.X, BandH * 0.5f), FLinearColor(0.f, 0.f, 0.f, 0.f), FLinearColor(0.f, 0.005f, 0.01f, 0.72f));
	P.RectV(FVector2f(0.f, BandTop + BandH * 0.5f), FVector2f(S.X, BandH * 0.5f), FLinearColor(0.f, 0.005f, 0.01f, 0.72f), FLinearColor(0.f, 0.f, 0.f, 0.f));
	P.Scanlines(FVector2f(0.f, BandTop), FVector2f(S.X, BandH), 3.f * K, FLinearColor(1.f, 1.f, 1.f, 0.03f));

	// ---- title geometry
	const FSlateFontInfo TitleFont = NVUI::Font(NVUI::EFont::Display, 104.f * K, 900);
	const FVector2f TS = Measure(Title, TitleFont);
	const FVector2f TP((S.X - TS.X) * 0.5f, S.Y * 0.43f - TS.Y * 0.5f);

	// glitch: strong while resolving, then rare short spikes
	const float Resolve = 1.f - FMath::Clamp((T - 0.25f) / 1.3f, 0.f, 1.f);
	const int32 Tick = FMath::FloorToInt(T * 24.f);
	const bool bSpike = T > 2.2f && FMath::Frac(T * 0.37f) < 0.035f;
	const float G0 = FMath::Max(Resolve, bSpike ? 0.55f : 0.f);
	const float Dx = (18.f * G0 + 1.2f) * K;
	const float Jy = (Hash(Tick) - 0.5f) * 6.f * G0 * K;
	const float TitleIn = FMath::Clamp((T - 0.2f) / 0.35f, 0.f, 1.f);
	const bool bBlink = Resolve > 0.15f && Hash(Tick + 7) < 0.22f * Resolve;   // flickers out a few frames early on

	// tear bars across the title while it resolves
	if (G0 > 0.05f)
	{
		for (int32 i = 0; i < 4; ++i)
		{
			const float Y = TP.Y + Hash(Tick * 4 + i) * TS.Y;
			const float H = (2.f + Hash(Tick * 4 + i + 31) * 9.f) * K;
			const float X0 = TP.X - 60.f * K + Hash(Tick * 4 + i + 57) * 120.f * K;
			const FLinearColor C = (i % 2) ? NVUI::WithAlpha(NVUI::Signal, 0.45f * G0) : NVUI::WithAlpha(NVUI::Accent, 0.5f * G0);
			P.Rect(FVector2f(X0, Y), FVector2f(TS.X * (0.3f + Hash(Tick * 4 + i + 91) * 0.7f), H), C);
		}
	}

	// rule under the title, drawn out from the centre, with end diamonds
	const float RuleE = Ease((T - 1.0f) / 0.9f);
	const float RuleW = (TS.X + 120.f * K) * RuleE;
	const float RuleY = TP.Y + TS.Y + 14.f * K;
	if (RuleW > 1.f)
	{
		P.RectH(FVector2f(S.X * 0.5f - RuleW * 0.5f, RuleY), FVector2f(RuleW * 0.5f, 1.5f * K), NVUI::WithAlpha(NVUI::Accent, 0.f), NVUI::Accent);
		P.RectH(FVector2f(S.X * 0.5f, RuleY), FVector2f(RuleW * 0.5f, 1.5f * K), NVUI::Accent, NVUI::WithAlpha(NVUI::Accent, 0.f));
		P.Diamond(FVector2f(S.X * 0.5f, RuleY + 0.75f * K), 4.f * K, NVUI::Accent);
	}
	LayerId = P.Flush(Out, LayerId);

	// ---- text layers
	const FLinearColor Base = Tint * FLinearColor(1.f, 1.f, 1.f, A * TitleIn);
	if (!bBlink)
	{
		Text(Out, LayerId + 1, G, Title, TitleFont, TP + FVector2f(-Dx, Jy), NVUI::WithAlpha(NVUI::Signal, 0.8f) * Base);
		Text(Out, LayerId + 2, G, Title, TitleFont, TP + FVector2f(Dx, -Jy), NVUI::WithAlpha(NVUI::Accent, 0.85f) * Base);
		Text(Out, LayerId + 3, G, Title, TitleFont, TP, NVUI::Text * Base);
	}

	// act line and place line type in
	auto Typed = [T](const FString& Full, float From, float Cps)
	{
		const int32 N = FMath::Clamp(FMath::FloorToInt((T - From) * Cps), 0, Full.Len());
		return Full.Left(N);
	};
	const FSlateFontInfo SubFont = NVUI::Font(NVUI::EFont::Mono, 22.f * K, 650);
	const FString SubShown = Typed(Subtitle, 1.5f, 28.f);
	const FVector2f SubSize = Measure(Subtitle, SubFont);
	Text(Out, LayerId + 3, G, SubShown, SubFont, FVector2f((S.X - SubSize.X) * 0.5f, RuleY + 22.f * K), NVUI::Accent * Tint * FLinearColor(1.f, 1.f, 1.f, A));

	const FSlateFontInfo TagFont = NVUI::Font(NVUI::EFont::Mono, 15.f * K, 450);
	const FString TagShown = Typed(Tagline, 2.6f, 34.f);
	const FVector2f TagSize = Measure(Tagline, TagFont);
	Text(Out, LayerId + 3, G, TagShown, TagFont, FVector2f((S.X - TagSize.X) * 0.5f, RuleY + 22.f * K + SubSize.Y + 12.f * K),
	     NVUI::TextDim * Tint * FLinearColor(1.f, 1.f, 1.f, A * 0.9f));

	return LayerId + 4;
}
