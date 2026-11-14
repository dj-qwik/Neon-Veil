#pragma once

#include "CoreMinimal.h"
#include "Fonts/SlateFontInfo.h"
#include "Rendering/RenderingCommon.h"
#include "Layout/Geometry.h"

class FSlateWindowElementList;
struct FSlateBrush;

/**
 * GHOST-OS: the shared look of every NEON VEIL screen (HUD, comms, menus, future cyberware / upgrade / skill pages).
 * Palette follows Bible §14 (pale white text, smoked glass, controlled cyan, emergency amber).
 * Fonts are OFL files in Content/UI/Fonts, loaded straight from disk (staged as non-UFS when packaging).
 */
namespace NVUI
{
	// ---- palette (linear) ----
	inline const FLinearColor Accent(0.35f, 0.9f, 1.f, 1.f);         // controlled cyan
	inline const FLinearColor AccentDeep(0.04f, 0.28f, 0.36f, 1.f);
	inline const FLinearColor Warning(1.f, 0.62f, 0.15f, 1.f);        // emergency amber
	inline const FLinearColor Danger(1.f, 0.22f, 0.2f, 1.f);
	inline const FLinearColor Signal(1.f, 0.18f, 0.55f, 1.f);         // glitch / encrypted, use sparingly
	inline const FLinearColor Text(0.92f, 0.95f, 0.97f, 1.f);
	inline const FLinearColor TextDim(0.55f, 0.64f, 0.69f, 1.f);
	inline const FLinearColor Glass(0.012f, 0.022f, 0.03f, 0.78f);   // smoked glass
	inline const FLinearColor GlassLight(0.03f, 0.06f, 0.075f, 0.7f);

	inline FLinearColor WithAlpha(const FLinearColor& C, float A) { return FLinearColor(C.R, C.G, C.B, C.A * A); }

	// ---- type ----
	enum class EFont : uint8
	{
		Display,   // Orbitron: titles, tab names, big numbers
		Body,      // Rajdhani Medium: reading text
		BodySemi,  // Rajdhani SemiBold: labels, objectives
		BodyBold,  // Rajdhani Bold: names, ammo
		Mono,      // Share Tech Mono: tags, data, terminal text
	};

	/** Font at Size (Slate points, 1080p design units) times the accessibility text scale. */
	NEONVEIL_API FSlateFontInfo Font(EFont Face, float Size, int32 LetterSpacing = 0);

	/** Accessibility multiplier (1 = design size). The HUD sets it from its TextScale setting. */
	NEONVEIL_API void SetTextScale(float Scale);
	NEONVEIL_API float GetTextScale();

	/** Seconds on the UI clock (real time, keeps running while paused). */
	NEONVEIL_API double Now();

	/** Uppercase with thin spacing, the way GHOST-OS prints labels. */
	NEONVEIL_API FText Label(const FText& In);

	/**
	 * Batches solid shapes into one custom-vertex draw call. Coordinates are local to the widget's geometry.
	 * Every colour is multiplied by Tint (pass the widget style's colour-and-opacity so fades work).
	 */
	struct NEONVEIL_API FPainter
	{
		FPainter(const FGeometry& InGeometry, const FLinearColor& InTint);

		void Tri(const FVector2f& A, const FVector2f& B, const FVector2f& C, const FLinearColor& CA, const FLinearColor& CB, const FLinearColor& CC);
		void Quad(const FVector2f& A, const FVector2f& B, const FVector2f& C, const FVector2f& D,
		          const FLinearColor& CA, const FLinearColor& CB, const FLinearColor& CC, const FLinearColor& CD);
		void Rect(const FVector2f& Pos, const FVector2f& Size, const FLinearColor& C);
		/** Vertical gradient. */
		void RectV(const FVector2f& Pos, const FVector2f& Size, const FLinearColor& Top, const FLinearColor& Bottom);
		/** Horizontal gradient. */
		void RectH(const FVector2f& Pos, const FVector2f& Size, const FLinearColor& Left, const FLinearColor& Right);
		/** Convex polygon fill (fan). */
		void Poly(const TArray<FVector2f>& Points, const FLinearColor& C);
		/** Convex polygon with a vertical gradient between its top and bottom. */
		void PolyV(const TArray<FVector2f>& Points, const FLinearColor& Top, const FLinearColor& Bottom);
		/** Thick segment as a quad (crisp for horizontal / vertical, use Lines() for diagonals). */
		void Seg(const FVector2f& A, const FVector2f& B, float Thickness, const FLinearColor& C);
		/** Horizontal scanlines over a rect. */
		void Scanlines(const FVector2f& Pos, const FVector2f& Size, float Pitch, const FLinearColor& C);
		/** Small diamond centred on P. */
		void Diamond(const FVector2f& P, float R, const FLinearColor& C);

		/** Submits the batch at Layer. Returns Layer. */
		int32 Flush(FSlateWindowElementList& Out, int32 Layer);

	private:
		FColor Pack(const FLinearColor& C) const;
		FSlateRenderTransform Transform;
		FLinearColor Tint;
		TArray<FSlateVertex> Verts;
		TArray<SlateIndex> Indices;
	};

	/** Antialiased polyline (outlines, chamfers, connectors). */
	NEONVEIL_API void Lines(FSlateWindowElementList& Out, int32 Layer, const FGeometry& G, const TArray<FVector2f>& Points,
	                        const FLinearColor& C, float Thickness = 1.f);

	/** Line-art icons drawn in code (cyberware, statuses). */
	enum class EIcon : uint8
	{
		None,
		Cloak,   // optical disruption: eye, struck through with a broken line
		Shield,  // kinetic shield: shield with an inner layer
		Drone,   // drone uplink: quadcopter with signal arcs
		Implant, // generic cyberware chip
	};

	/** Draws Icon centred on Center within a Size x Size square. Colour already includes any tint. */
	NEONVEIL_API void PaintIcon(FSlateWindowElementList& Out, int32 Layer, const FGeometry& G, const FVector2f& Center, float Size,
	                            EIcon Icon, const FLinearColor& Color);

	/** Chamfered rectangle outline points (top-left and bottom-right corners cut by Cut). Closed. */
	NEONVEIL_API TArray<FVector2f> ChamferPoints(const FVector2f& Pos, const FVector2f& Size, float Cut, bool bClosed = true);
}
