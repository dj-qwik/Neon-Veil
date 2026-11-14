#include "UI/NVUIStyle.h"
#include "NeonVeil.h"

#include "Engine/Texture2D.h"
#include "Fonts/CompositeFont.h"
#include "Framework/Application/SlateApplication.h"
#include "HAL/PlatformTime.h"
#include "Misc/Paths.h"
#include "Rendering/DrawElements.h"
#include "Rendering/SlateRenderer.h"
#include "Styling/CoreStyle.h"
#include "Styling/SlateBrush.h"

namespace NVUI
{
namespace
{
	float GTextScale = 1.f;

	TSharedPtr<const FCompositeFont> LoadFace(const TCHAR* File)
	{
		const FString Path = FPaths::ConvertRelativePathToFull(FPaths::ProjectContentDir() / TEXT("UI/Fonts") / File);
		if (!FPaths::FileExists(Path))
		{
			UE_LOG(LogNeonVeil, Warning, TEXT("GHOST-OS font missing: %s (falling back to Roboto)"), *Path);
			return nullptr;
		}
		return MakeShared<FCompositeFont>(FName(TEXT("Regular")), Path, EFontHinting::Default, EFontLoadingPolicy::LazyLoad);
	}

	const TSharedPtr<const FCompositeFont>& Face(EFont F)
	{
		static TSharedPtr<const FCompositeFont> Faces[5];
		static bool bLoaded = false;
		if (!bLoaded)
		{
			bLoaded = true;
			Faces[static_cast<int32>(EFont::Display)] = LoadFace(TEXT("Orbitron.ttf"));
			Faces[static_cast<int32>(EFont::Body)] = LoadFace(TEXT("Rajdhani-Medium.ttf"));
			Faces[static_cast<int32>(EFont::BodySemi)] = LoadFace(TEXT("Rajdhani-SemiBold.ttf"));
			Faces[static_cast<int32>(EFont::BodyBold)] = LoadFace(TEXT("Rajdhani-Bold.ttf"));
			Faces[static_cast<int32>(EFont::Mono)] = LoadFace(TEXT("ShareTechMono-Regular.ttf"));
		}
		return Faces[static_cast<int32>(F)];
	}

	const FSlateBrush* WhiteBrush()
	{
		static FSlateBrush* Brush = nullptr;
		if (!Brush)
		{
			Brush = new FSlateBrush();
			if (UTexture2D* Tex = LoadObject<UTexture2D>(nullptr, TEXT("/Engine/EngineResources/WhiteSquareTexture.WhiteSquareTexture")))
			{
				Tex->AddToRoot();
				Brush->SetResourceObject(Tex);
				Brush->ImageSize = FVector2D(4.f, 4.f);
			}
		}
		return Brush;
	}
}

FSlateFontInfo Font(EFont FaceId, float Size, int32 LetterSpacing)
{
	const float S = FMath::Max(6.f, Size * GTextScale);
	const TSharedPtr<const FCompositeFont>& F = Face(FaceId);
	FSlateFontInfo Info = F.IsValid()
		? FSlateFontInfo(F, S, FName(TEXT("Regular")))
		: FCoreStyle::GetDefaultFontStyle(FaceId == EFont::Body ? FName(TEXT("Regular")) : FName(TEXT("Bold")), S);
	Info.LetterSpacing = LetterSpacing;
	return Info;
}

void SetTextScale(float Scale)
{
	GTextScale = FMath::Clamp(Scale, 0.6f, 2.f);
}

float GetTextScale()
{
	return GTextScale;
}

double Now()
{
	return FSlateApplication::IsInitialized() ? FSlateApplication::Get().GetCurrentTime() : FPlatformTime::Seconds();
}

FText Label(const FText& In)
{
	return In.ToUpper();
}

// ---------------------------------------------------------------- painter

FPainter::FPainter(const FGeometry& InGeometry, const FLinearColor& InTint)
	: Transform(InGeometry.GetAccumulatedRenderTransform())
	, Tint(InTint)
{
	Verts.Reserve(256);
	Indices.Reserve(384);
}

FColor FPainter::Pack(const FLinearColor& C) const
{
	return (C * Tint).ToFColor(true);
}

void FPainter::Tri(const FVector2f& A, const FVector2f& B, const FVector2f& C, const FLinearColor& CA, const FLinearColor& CB, const FLinearColor& CC)
{
	const SlateIndex Base = static_cast<SlateIndex>(Verts.Num());
	const FVector2f UV(0.5f, 0.5f);
	Verts.Add(FSlateVertex::Make(Transform, A, UV, UV, Pack(CA), FColor(), ESlateVertexRounding::Disabled));
	Verts.Add(FSlateVertex::Make(Transform, B, UV, UV, Pack(CB), FColor(), ESlateVertexRounding::Disabled));
	Verts.Add(FSlateVertex::Make(Transform, C, UV, UV, Pack(CC), FColor(), ESlateVertexRounding::Disabled));
	Indices.Add(Base);
	Indices.Add(Base + 1);
	Indices.Add(Base + 2);
}

void FPainter::Quad(const FVector2f& A, const FVector2f& B, const FVector2f& C, const FVector2f& D,
                    const FLinearColor& CA, const FLinearColor& CB, const FLinearColor& CC, const FLinearColor& CD)
{
	const SlateIndex Base = static_cast<SlateIndex>(Verts.Num());
	const FVector2f UV(0.5f, 0.5f);
	Verts.Add(FSlateVertex::Make(Transform, A, UV, UV, Pack(CA), FColor(), ESlateVertexRounding::Disabled));
	Verts.Add(FSlateVertex::Make(Transform, B, UV, UV, Pack(CB), FColor(), ESlateVertexRounding::Disabled));
	Verts.Add(FSlateVertex::Make(Transform, C, UV, UV, Pack(CC), FColor(), ESlateVertexRounding::Disabled));
	Verts.Add(FSlateVertex::Make(Transform, D, UV, UV, Pack(CD), FColor(), ESlateVertexRounding::Disabled));
	Indices.Add(Base);
	Indices.Add(Base + 1);
	Indices.Add(Base + 2);
	Indices.Add(Base);
	Indices.Add(Base + 2);
	Indices.Add(Base + 3);
}

void FPainter::Rect(const FVector2f& P, const FVector2f& S, const FLinearColor& C)
{
	Quad(P, P + FVector2f(S.X, 0.f), P + S, P + FVector2f(0.f, S.Y), C, C, C, C);
}

void FPainter::RectV(const FVector2f& P, const FVector2f& S, const FLinearColor& Top, const FLinearColor& Bottom)
{
	Quad(P, P + FVector2f(S.X, 0.f), P + S, P + FVector2f(0.f, S.Y), Top, Top, Bottom, Bottom);
}

void FPainter::RectH(const FVector2f& P, const FVector2f& S, const FLinearColor& Left, const FLinearColor& Right)
{
	Quad(P, P + FVector2f(S.X, 0.f), P + S, P + FVector2f(0.f, S.Y), Left, Right, Right, Left);
}

void FPainter::Poly(const TArray<FVector2f>& Points, const FLinearColor& C)
{
	for (int32 i = 1; i + 1 < Points.Num(); ++i)
	{
		Tri(Points[0], Points[i], Points[i + 1], C, C, C);
	}
}

void FPainter::PolyV(const TArray<FVector2f>& Points, const FLinearColor& Top, const FLinearColor& Bottom)
{
	if (Points.Num() < 3)
	{
		return;
	}
	float Y0 = Points[0].Y, Y1 = Points[0].Y;
	for (const FVector2f& Pt : Points)
	{
		Y0 = FMath::Min(Y0, Pt.Y);
		Y1 = FMath::Max(Y1, Pt.Y);
	}
	const float H = FMath::Max(1.f, Y1 - Y0);
	auto Col = [&](const FVector2f& Pt) { return FMath::Lerp(Top, Bottom, (Pt.Y - Y0) / H); };
	for (int32 i = 1; i + 1 < Points.Num(); ++i)
	{
		Tri(Points[0], Points[i], Points[i + 1], Col(Points[0]), Col(Points[i]), Col(Points[i + 1]));
	}
}

void FPainter::Seg(const FVector2f& A, const FVector2f& B, float Thickness, const FLinearColor& C)
{
	FVector2f D = B - A;
	const float Len = D.Size();
	if (Len < KINDA_SMALL_NUMBER)
	{
		return;
	}
	const FVector2f N = FVector2f(-D.Y, D.X) / Len * (Thickness * 0.5f);
	Quad(A + N, B + N, B - N, A - N, C, C, C, C);
}

void FPainter::Scanlines(const FVector2f& P, const FVector2f& S, float Pitch, const FLinearColor& C)
{
	for (float Y = P.Y + 1.f; Y < P.Y + S.Y; Y += Pitch)
	{
		Rect(FVector2f(P.X, Y), FVector2f(S.X, 1.f), C);
	}
}

void FPainter::Diamond(const FVector2f& P, float R, const FLinearColor& C)
{
	Quad(P + FVector2f(0.f, -R), P + FVector2f(R, 0.f), P + FVector2f(0.f, R), P + FVector2f(-R, 0.f), C, C, C, C);
}

int32 FPainter::Flush(FSlateWindowElementList& Out, int32 Layer)
{
	if (Verts.Num() > 0 && FSlateApplication::IsInitialized() && FSlateApplication::Get().GetRenderer())
	{
		const FSlateResourceHandle Handle = FSlateApplication::Get().GetRenderer()->GetResourceHandle(*WhiteBrush(), FVector2f(4.f, 4.f), 1.f);
		FSlateDrawElement::MakeCustomVerts(Out, Layer, Handle, Verts, Indices, nullptr, 0, 0);
	}
	Verts.Reset();
	Indices.Reset();
	return Layer;
}

void Lines(FSlateWindowElementList& Out, int32 Layer, const FGeometry& G, const TArray<FVector2f>& Points, const FLinearColor& C, float Thickness)
{
	if (Points.Num() < 2)
	{
		return;
	}
	FSlateDrawElement::MakeLines(Out, Layer, G.ToPaintGeometry(), Points, ESlateDrawEffect::None, C, true, Thickness);
}

TArray<FVector2f> ChamferPoints(const FVector2f& P, const FVector2f& S, float Cut, bool bClosed)
{
	const float C = FMath::Min(Cut, FMath::Min(S.X, S.Y) * 0.5f);
	TArray<FVector2f> Pts = {
		P + FVector2f(C, 0.f),
		P + FVector2f(S.X, 0.f),
		P + FVector2f(S.X, S.Y - C),
		P + FVector2f(S.X - C, S.Y),
		P + FVector2f(0.f, S.Y),
		P + FVector2f(0.f, C),
	};
	if (bClosed)
	{
		const FVector2f First = Pts[0]; // copy: Add() may reallocate
		Pts.Add(First);
	}
	return Pts;
}

void PaintIcon(FSlateWindowElementList& Out, int32 Layer, const FGeometry& G, const FVector2f& C, float Size, EIcon Icon, const FLinearColor& Col)
{
	const float R = Size * 0.5f;
	const FLinearColor Fill = WithAlpha(Col, 0.18f);
	FPainter P(G, FLinearColor::White);
	auto Circle = [&](const FVector2f& O, float Rad, int32 N, float A0 = 0.f, float A1 = 2.f * PI)
	{
		TArray<FVector2f> Pts;
		for (int32 i = 0; i <= N; ++i)
		{
			const float A = FMath::Lerp(A0, A1, static_cast<float>(i) / N);
			Pts.Add(O + FVector2f(FMath::Cos(A), FMath::Sin(A)) * Rad);
		}
		return Pts;
	};
	switch (Icon)
	{
	case EIcon::Cloak:
	{
		// eye
		TArray<FVector2f> Eye;
		for (int32 i = 0; i <= 12; ++i)
		{
			const float T = -1.f + 2.f * i / 12.f;
			Eye.Add(C + FVector2f(R * 0.95f * T, -R * 0.55f * (1.f - T * T)));
		}
		for (int32 i = 11; i >= 0; --i)
		{
			const float T = -1.f + 2.f * i / 12.f;
			Eye.Add(C + FVector2f(R * 0.95f * T, R * 0.55f * (1.f - T * T)));
		}
		P.Poly(Circle(C, R * 0.3f, 16), Fill);
		P.Diamond(C, R * 0.16f, Col);
		P.Flush(Out, Layer);
		Lines(Out, Layer + 1, G, Eye, Col, 1.6f);
		Lines(Out, Layer + 1, G, Circle(C, R * 0.3f, 16), Col, 1.4f);
		// broken strike-through: the image is "disrupted"
		const FVector2f A = C + FVector2f(-R * 0.85f, R * 0.85f), B = C + FVector2f(R * 0.85f, -R * 0.85f);
		for (int32 k = 0; k < 4; ++k)
		{
			const float T0 = k / 4.f, T1 = T0 + 0.16f;
			Lines(Out, Layer + 1, G, { FMath::Lerp(A, B, T0), FMath::Lerp(A, B, T1) }, Col, 2.f);
		}
		break;
	}
	case EIcon::Shield:
	{
		TArray<FVector2f> Outer;
		const FVector2f Off[] = { FVector2f(0.f, -R), FVector2f(R * 0.82f, -R * 0.68f), FVector2f(R * 0.82f, R * 0.1f), FVector2f(0.f, R),
			FVector2f(-R * 0.82f, R * 0.1f), FVector2f(-R * 0.82f, -R * 0.68f) };
		TArray<FVector2f> Inner;
		for (const FVector2f& O : Off)
		{
			Outer.Add(C + O);
			Inner.Add(C + O * 0.55f + FVector2f(0.f, R * 0.04f));
		}
		P.Poly(Outer, Fill);
		P.Poly(Inner, WithAlpha(Col, 0.35f));
		P.Flush(Out, Layer);
		const FVector2f O0 = Outer[0];
		Outer.Add(O0);
		const FVector2f I0 = Inner[0];
		Inner.Add(I0);
		Lines(Out, Layer + 1, G, Outer, Col, 1.6f);
		Lines(Out, Layer + 1, G, Inner, Col, 1.2f);
		break;
	}
	case EIcon::Drone:
	{
		const FVector2f Body = C + FVector2f(0.f, R * 0.18f);
		const float Arm = R * 0.62f;
		const FVector2f Dirs[] = { FVector2f(-1.f, -1.f), FVector2f(1.f, -1.f), FVector2f(1.f, 1.f), FVector2f(-1.f, 1.f) };
		P.Diamond(Body, R * 0.2f, Col);
		for (const FVector2f& D : Dirs)
		{
			const FVector2f Rotor = Body + D.GetSafeNormal() * Arm;
			P.Poly(Circle(Rotor, R * 0.24f, 14), Fill);
		}
		P.Flush(Out, Layer);
		for (const FVector2f& D : Dirs)
		{
			const FVector2f Rotor = Body + D.GetSafeNormal() * Arm;
			Lines(Out, Layer + 1, G, { Body + D.GetSafeNormal() * R * 0.2f, Rotor }, Col, 1.6f);
			Lines(Out, Layer + 1, G, Circle(Rotor, R * 0.24f, 14), Col, 1.3f);
		}
		// uplink arcs above
		const FVector2f Top = C + FVector2f(0.f, -R * 0.55f);
		Lines(Out, Layer + 1, G, Circle(Top + FVector2f(0.f, R * 0.35f), R * 0.32f, 8, PI * 1.2f, PI * 1.8f), Col, 1.3f);
		Lines(Out, Layer + 1, G, Circle(Top + FVector2f(0.f, R * 0.35f), R * 0.55f, 10, PI * 1.25f, PI * 1.75f), WithAlpha(Col, 0.7f), 1.3f);
		break;
	}
	case EIcon::Implant:
	{
		const TArray<FVector2f> Chip = ChamferPoints(C - FVector2f(R * 0.55f, R * 0.55f), FVector2f(R * 1.1f, R * 1.1f), R * 0.25f, true);
		P.Poly(ChamferPoints(C - FVector2f(R * 0.55f, R * 0.55f), FVector2f(R * 1.1f, R * 1.1f), R * 0.25f, false), Fill);
		for (int32 i = -1; i <= 1; ++i)
		{
			const float O = i * R * 0.32f;
			P.Rect(C + FVector2f(O - 1.f, -R * 0.9f), FVector2f(2.f, R * 0.3f), Col);
			P.Rect(C + FVector2f(O - 1.f, R * 0.6f), FVector2f(2.f, R * 0.3f), Col);
			P.Rect(C + FVector2f(-R * 0.9f, O - 1.f), FVector2f(R * 0.3f, 2.f), Col);
			P.Rect(C + FVector2f(R * 0.6f, O - 1.f), FVector2f(R * 0.3f, 2.f), Col);
		}
		P.Diamond(C, R * 0.2f, Col);
		P.Flush(Out, Layer);
		Lines(Out, Layer + 1, G, Chip, Col, 1.5f);
		break;
	}
	default:
		break;
	}
}
}
