#include "UI/NVMenuShell.h"
#include "UI/NVUIWidgets.h"
#include "UI/NVHUD.h"
#include "Core/NVPlayerController.h"
#include "Character/NVPlayerCharacter.h"
#include "Combat/NVHealthComponent.h"
#include "Combat/NVWeaponComponent.h"
#include "Combat/NVWeaponData.h"
#include "Abilities/NVAbilityComponent.h"
#include "Abilities/NVAbilityData.h"
#include "Objectives/NVObjectiveSubsystem.h"
#include "Objectives/NVObjectiveData.h"
#include "UI/NVHoloRig.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/SkeletalMesh.h"

#include "Framework/Application/SlateApplication.h"
#include "Fonts/FontMeasure.h"
#include "Rendering/DrawElements.h"
#include "Rendering/SlateRenderer.h"
#include "Widgets/SOverlay.h"
#include "Widgets/SNullWidget.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Layout/SScrollBox.h"
#include "Widgets/Layout/SSpacer.h"
#include "Widgets/Layout/SUniformGridPanel.h"
#include "Widgets/Layout/SWidgetSwitcher.h"
#include "Widgets/Text/STextBlock.h"

#define LOCTEXT_NAMESPACE "NeonVeilUI"


namespace
{
	/** Small painted diamond. */
	class SNVDot : public SLeafWidget
	{
	public:
		SLATE_BEGIN_ARGS(SNVDot) : _Color(NVUI::Accent), _Radius(4.f) {}
			SLATE_ATTRIBUTE(FLinearColor, Color)
			SLATE_ARGUMENT(float, Radius)
		SLATE_END_ARGS()

		void Construct(const FArguments& InArgs) { Color = InArgs._Color; Radius = InArgs._Radius; }
		virtual FVector2D ComputeDesiredSize(float) const override { return FVector2D(Radius * 2.f + 2.f, Radius * 2.f + 2.f); }
		virtual int32 OnPaint(const FPaintArgs&, const FGeometry& G, const FSlateRect&, FSlateWindowElementList& Out, int32 LayerId,
		                      const FWidgetStyle& Style, bool) const override
		{
			NVUI::FPainter P(G, Style.GetColorAndOpacityTint());
			const FVector2f S(G.GetLocalSize());
			P.Diamond(S * 0.5f, Radius, Color.Get());
			P.Diamond(S * 0.5f, Radius * 0.45f, FLinearColor(0.f, 0.f, 0.f, 0.6f));
			return P.Flush(Out, LayerId);
		}

	private:
		TAttribute<FLinearColor> Color;
		float Radius = 4.f;
	};

	/** Vertical connector between skill nodes. */
	class SNVConnector : public SLeafWidget
	{
	public:
		SLATE_BEGIN_ARGS(SNVConnector) {}
		SLATE_END_ARGS()

		void Construct(const FArguments&) {}
		virtual FVector2D ComputeDesiredSize(float) const override { return FVector2D(20.f, 26.f); }
		virtual int32 OnPaint(const FPaintArgs&, const FGeometry& G, const FSlateRect&, FSlateWindowElementList& Out, int32 LayerId,
		                      const FWidgetStyle& Style, bool) const override
		{
			NVUI::FPainter P(G, Style.GetColorAndOpacityTint());
			const FVector2f S(G.GetLocalSize());
			const float X = FMath::FloorToFloat(S.X * 0.5f);
			for (float Y = 0.f; Y < S.Y; Y += 5.f)
			{
				P.Rect(FVector2f(X, Y), FVector2f(1.f, 3.f), NVUI::WithAlpha(NVUI::Accent, 0.35f));
			}
			return P.Flush(Out, LayerId);
		}
	};

	/** Wireframe operative with implant slot callouts (cyberware page). */
	class SNVBodyScan : public SLeafWidget
	{
	public:
		SLATE_BEGIN_ARGS(SNVBodyScan) {}
			SLATE_ARGUMENT(TWeakObjectPtr<ANVHoloRig>, Rig)
		SLATE_END_ARGS()

		void Construct(const FArguments& InArgs)
		{
			Start = NVUI::Now();
			Rig = InArgs._Rig;
			if (Rig.IsValid() && Rig->GetPresenter())
			{
				HoloBrush.SetResourceObject(Rig->GetPresenter());
				HoloBrush.ImageSize = FVector2D(ANVHoloRig::BoxW, ANVHoloRig::BoxH);
				HoloBrush.DrawAs = ESlateBrushDrawType::Image;
				bHolo = true;
			}
		}
		virtual FVector2D ComputeDesiredSize(float) const override { return FVector2D(460.f, 540.f); }
		virtual int32 OnPaint(const FPaintArgs&, const FGeometry& G, const FSlateRect&, FSlateWindowElementList& Out, int32 LayerId,
		                      const FWidgetStyle& Style, bool) const override
		{
			const FVector2f S(G.GetLocalSize());
			const FLinearColor Tint = Style.GetColorAndOpacityTint();
			const float CX = S.X * 0.5f;
			const float K = FMath::Min(S.Y / 540.f, S.X / 460.f);
			auto Pt = [&](float X, float Y) { return FVector2f(CX + X * K, (20.f + Y) * K); };
			const FLinearColor Wire = NVUI::WithAlpha(NVUI::Accent, 0.55f) * Tint;
			const FLinearColor WireDim = NVUI::WithAlpha(NVUI::Accent, 0.2f) * Tint;

			// ground grid
			NVUI::FPainter P(G, Tint);
			for (int32 i = -5; i <= 5; ++i)
			{
				P.Rect(Pt(i * 26.f, 486.f), FVector2f(1.f, 8.f * K), NVUI::WithAlpha(NVUI::Accent, 0.18f));
			}
			P.Rect(Pt(-140.f, 494.f), FVector2f(280.f * K, 1.f), NVUI::WithAlpha(NVUI::Accent, 0.25f));
			// scan band
			const float T = FMath::Frac(static_cast<float>(NVUI::Now() - Start) * 0.25f);
			const float BandY = (20.f + T * 480.f) * K;
			P.RectV(FVector2f(CX - 150.f * K, BandY - 30.f * K), FVector2f(300.f * K, 30.f * K), NVUI::WithAlpha(NVUI::Accent, 0.f), NVUI::WithAlpha(NVUI::Accent, 0.12f));
			P.Rect(FVector2f(CX - 150.f * K, BandY), FVector2f(300.f * K, 1.f), NVUI::WithAlpha(NVUI::Accent, 0.6f));
			P.Flush(Out, LayerId);

			if (bHolo && Rig.IsValid())
			{
				// --- Holographic body: live capture of the operative (ANVHoloRig), platform rings, height ruler.
				Rig->Touch();
				FSlateDrawElement::MakeBox(Out, LayerId + 1,
					G.ToPaintGeometry(FVector2f(ANVHoloRig::BoxW * K, ANVHoloRig::BoxH * K), FSlateLayoutTransform(FVector2f(CX - ANVHoloRig::BoxW * 0.5f * K, 0.f))),
					&HoloBrush, ESlateDrawEffect::None, Tint);
				// projector platform: concentric ellipses under the feet, a slow rotating tick ring
				const float Now = static_cast<float>(NVUI::Now() - Start);
				auto Ellipse = [&](float RX, float RY, float CYu, const FLinearColor& Col, float Th, float Gap = 0.f, float Phase = 0.f)
				{
					TArray<FVector2f> Pts;
					for (int32 i = 0; i <= 64; ++i)
					{
						const float A = Phase + i / 64.f * 2.f * PI;
						if (Gap > 0.f && FMath::Fmod(static_cast<float>(i), 8.f) < Gap) { if (Pts.Num() > 1) { NVUI::Lines(Out, LayerId + 1, G, Pts, Col, Th); } Pts.Reset(); continue; }
						Pts.Add(Pt(FMath::Cos(A) * RX, CYu + FMath::Sin(A) * RY));
					}
					if (Pts.Num() > 1) { NVUI::Lines(Out, LayerId + 1, G, Pts, Col, Th); }
				};
				Ellipse(120.f, 18.f, 470.f, NVUI::WithAlpha(NVUI::Accent, 0.55f) * Tint, 1.2f);
				Ellipse(150.f, 23.f, 470.f, NVUI::WithAlpha(NVUI::Accent, 0.25f) * Tint, 1.f, 3.f, Now * 0.4f);
				Ellipse(185.f, 28.f, 470.f, NVUI::WithAlpha(NVUI::Accent, 0.12f) * Tint, 1.f, 5.f, -Now * 0.25f);
				Ellipse(70.f, 10.f, 470.f, NVUI::WithAlpha(NVUI::Accent, 0.8f) * Tint, 1.6f);
				// height ruler on the right edge
				NVUI::FPainter R(G, Tint);
				for (int32 i = 0; i <= 18; ++i)
				{
					const float Yu = 5.f + i * (465.f / 18.f);
					const float Len = (i % 3 == 0) ? 14.f : 7.f;
					R.Rect(Pt(208.f - Len, Yu), FVector2f(Len * K, 1.f), NVUI::WithAlpha(NVUI::Accent, i % 3 == 0 ? 0.5f : 0.25f));
				}
				R.Rect(Pt(208.f, 5.f), FVector2f(1.f, 465.f * K), NVUI::WithAlpha(NVUI::Accent, 0.25f));
				// corner brackets framing the scan volume
				const float BL = 22.f;
				for (int32 cx = -1; cx <= 1; cx += 2)
				{
					for (int32 cy = 0; cy <= 1; ++cy)
					{
						const FVector2f C0 = Pt(cx * 196.f, cy ? 505.f : -10.f);
						R.Rect(FVector2f(cx < 0 ? C0.X : C0.X - BL * K, C0.Y), FVector2f(BL * K, 1.5f), NVUI::WithAlpha(NVUI::Accent, 0.6f));
						R.Rect(FVector2f(C0.X, cy ? C0.Y - BL * K : C0.Y), FVector2f(1.5f, BL * K), NVUI::WithAlpha(NVUI::Accent, 0.6f));
					}
				}
				R.Flush(Out, LayerId + 1);
				const FSlateFontInfo Tiny = NVUI::Font(NVUI::EFont::Mono, 9.f, 80);
				const FString Sync = FString::Printf(TEXT("NEURAL SYNC %.1f%%   //   BIOMON NOMINAL   //   SCAN %03d"), 97.8f + 0.6f * FMath::Sin(Now * 0.7f), static_cast<int32>(FMath::Frac(Now * 0.25f) * 1000.f));
				FSlateDrawElement::MakeText(Out, LayerId + 3, G.ToPaintGeometry(FVector2f(S.X, 14.f), FSlateLayoutTransform(Pt(-196.f, 512.f))),
					Sync, Tiny, ESlateDrawEffect::None, NVUI::WithAlpha(NVUI::Accent, 0.6f) * Tint);
			}
			else
			{
				// --- Holographic body: filled anatomical silhouette, x-ray skeleton inside, glowing contour.
				using FPtList = TArray<FVector2f>;
				auto Mirror = [](const TArray<FVector2D>& Right, bool bClose)
				{
					// Right half (x >= 0, top to bottom) + mirrored left half back up = closed outline in local units.
					TArray<FVector2D> All = Right;
					for (int32 i = Right.Num() - 1; i >= 0; --i)
					{
						if (!FMath::IsNearlyZero(Right[i].X))
						{
							All.Add(FVector2D(-Right[i].X, Right[i].Y));
						}
					}
					if (bClose) { const FVector2D First = All[0]; All.Add(First); }
					return All;
				};
				auto ToPts = [&](const TArray<FVector2D>& L, float Flip = 1.f)
				{
					FPtList R;
					for (const FVector2D& V : L) { R.Add(Pt(static_cast<float>(V.X) * Flip, static_cast<float>(V.Y))); }
					return R;
				};
				auto Fan = [&](NVUI::FPainter& Painter, const FPtList& Outline, const FLinearColor& Top, const FLinearColor& Bottom)
				{
					// Star-shaped fill: fan from the centroid (the pieces are not convex).
					FVector2f C(0.f, 0.f);
					for (const FVector2f& V : Outline) { C += V; }
					C /= static_cast<float>(FMath::Max(1, Outline.Num()));
					FPtList F;
					F.Add(C);
					F.Append(Outline);
					F.Add(Outline[0]);
					Painter.PolyV(F, Top, Bottom);
				};

				// Pieces (right side; arms/legs mirrored). Local units: 0..490 tall, centre x = 0.
				const TArray<FVector2D> HeadR = { {0,0},{14,2},{23,10},{27,24},{27,40},{24,52},{17,62},{8,70},{0,73} };
				const TArray<FVector2D> NeckR = { {0,66},{10,67},{12,88},{0,88} };
				const TArray<FVector2D> TorsoR = { {0,84},{12,86},{30,90},{52,96},{60,105},{56,122},{50,128},{48,150},{42,200},{48,236},{52,262},{26,272},{0,280} };
				const TArray<FVector2D> ArmR = { {60,105},{70,120},{74,150},{78,190},{84,230},{88,262},{93,280},{89,299},{80,302},{76,284},{74,262},{66,226},{60,192},{56,150},{50,128},{56,122} };
				const TArray<FVector2D> LegR = { {52,262},{54,300},{50,360},{46,378},{48,410},{42,456},{36,470},{45,483},{39,491},{18,491},{20,476},{20,460},{18,410},{14,378},{12,330},{4,282},{26,272} };
				const TArray<FVector2D> OutlineR = { {0,0},{14,2},{23,10},{27,24},{27,40},{24,52},{17,62},{10,70},{11,84},{30,90},{52,96},{60,105},{70,120},{74,150},{78,190},{84,230},{88,262},{93,280},{89,299},{80,302},{76,284},{74,262},{66,226},{60,192},{56,150},{50,128},{48,150},{42,200},{48,236},{52,262},{54,300},{50,360},{46,378},{48,410},{42,456},{36,470},{45,483},{39,491},{18,491},{20,476},{20,460},{18,410},{14,378},{12,330},{4,282},{0,280} };

				const FLinearColor FillTop = NVUI::WithAlpha(NVUI::Accent, 0.20f);
				const FLinearColor FillBot = NVUI::WithAlpha(NVUI::Accent, 0.05f);
				NVUI::FPainter Body(G, Tint);
				Fan(Body, ToPts(Mirror(HeadR, false)), FillTop, FillBot);
				Fan(Body, ToPts(Mirror(NeckR, false)), FillTop, FillBot);
				Fan(Body, ToPts(Mirror(TorsoR, false)), FillTop, FillBot);
				for (float Side : { 1.f, -1.f })
				{
					Fan(Body, ToPts(ArmR, Side), FillTop, FillBot);
					Fan(Body, ToPts(LegR, Side), FillTop, FillBot);
				}
				// horizontal hologram lines across the silhouette
				for (float Y = 4.f; Y < 490.f; Y += 7.f)
				{
					Body.Rect(Pt(-96.f, Y), FVector2f(192.f * K, 1.f), NVUI::WithAlpha(NVUI::Accent, 0.025f));
				}
				Body.Flush(Out, LayerId + 1);

				auto Line = [&](const FPtList& P2, const FLinearColor& C, float Th) { NVUI::Lines(Out, LayerId + 1, G, P2, C, Th); };
				auto L2 = [&](std::initializer_list<FVector2D> Pts, float Side, const FLinearColor& C, float Th)
				{
					Line(ToPts(TArray<FVector2D>(Pts), Side), C, Th);
				};
				const FLinearColor Bone = NVUI::WithAlpha(NVUI::Accent, 0.42f) * Tint;
				const FLinearColor Faint = NVUI::WithAlpha(NVUI::Accent, 0.16f) * Tint;

				// x-ray skeleton
				for (float Y = 92.f; Y <= 268.f; Y += 8.f)          // vertebrae
				{
					L2({ { -3.0, Y }, { 3.0, Y } }, 1.f, Bone, 1.2f);
				}
				L2({ { 0, 88 }, { 0, 272 } }, 1.f, Faint, 1.f);
				for (int32 i = 0; i < 6; ++i)                      // ribs
				{
					const double Y = 108.0 + i * 13.0;
					const double W = 40.0 - FMath::Abs(i - 2) * 3.0;
					for (float Side : { 1.f, -1.f })
					{
						L2({ { 3, Y }, { W * 0.55, Y - 3 }, { W, Y + 6 }, { W - 2, Y + 15 } }, Side, Bone, 1.f);
					}
				}
				for (float Side : { 1.f, -1.f })
				{
					L2({ { 6, 93 }, { 30, 92 }, { 52, 100 } }, Side, Bone, 1.2f);              // clavicle
					L2({ { 8, 236 }, { 30, 230 }, { 42, 240 }, { 36, 258 }, { 14, 268 } }, Side, Bone, 1.2f); // pelvis
					L2({ { 62, 112 }, { 67, 190 } }, Side, Bone, 1.5f);                         // humerus
					L2({ { 68, 196 }, { 79, 262 } }, Side, Bone, 1.2f);                         // forearm
					L2({ { 71, 196 }, { 83, 260 } }, Side, Faint, 1.f);
					L2({ { 35, 266 }, { 32, 374 } }, Side, Bone, 1.6f);                         // femur
					L2({ { 30, 384 }, { 29, 462 } }, Side, Bone, 1.4f);                         // tibia
					L2({ { 34, 386 }, { 34, 458 } }, Side, Faint, 1.f);
					L2({ { 4, 104 }, { 28, 102 }, { 46, 114 }, { 40, 132 }, { 12, 136 } }, Side, Faint, 1.f); // chest plate
					L2({ { 8, 150 }, { 34, 156 }, { 38, 200 }, { 10, 214 } }, Side, Faint, 1.f);  // abdomen panel
					L2({ { 20, 300 }, { 44, 304 } }, Side, Faint, 1.f);                         // thigh band
					L2({ { 22, 420 }, { 44, 424 } }, Side, Faint, 1.f);                         // shin band
				}
				// skull + visor
				L2({ { -18, 6 }, { 18, 6 } }, 1.f, Faint, 1.f);
				L2({ { -22, 46 }, { -14, 60 }, { 0, 66 }, { 14, 60 }, { 22, 46 } }, 1.f, Bone, 1.f);
				NVUI::FPainter Joints(G, Tint);
				Joints.Rect(Pt(-20.f, 29.f), FVector2f(40.f * K, 4.f * K), NVUI::WithAlpha(NVUI::Accent, 0.85f));   // visor
				Joints.Rect(Pt(-20.f, 29.f), FVector2f(40.f * K, 1.f), NVUI::WithAlpha(FLinearColor::White, 0.6f));
				for (float Side : { 1.f, -1.f })
				{
					for (const FVector2D& J : { FVector2D(62, 108), FVector2D(67, 193), FVector2D(80, 264), FVector2D(35, 264), FVector2D(31, 379), FVector2D(29, 465) })
					{
						Joints.Diamond(Pt(static_cast<float>(J.X) * Side, static_cast<float>(J.Y)), 3.f, NVUI::WithAlpha(NVUI::Accent, 0.55f));
					}
				}
				Joints.Flush(Out, LayerId + 1);

				// contour: soft glow + crisp edge
				const FPtList Contour = ToPts(Mirror(OutlineR, true));
				Line(Contour, NVUI::WithAlpha(NVUI::Accent, 0.10f) * Tint, 5.f);
				Line(Contour, NVUI::WithAlpha(NVUI::Accent, 0.85f) * Tint, 1.4f);

			}

			// callouts: slot marker on the body, leader line, label at the side
			struct FCallout { const TCHAR* Name; float X, Y; bool bLeft; const TCHAR* Bone; FVector Offset; };
			// screen-left is the operative's right side (the hologram faces the viewer)
			static const FCallout Calls[] = {
				{ TEXT("NEURAL"), 0.f, 16.f, true, TEXT("head"), FVector(0.f, 0.f, 16.f) },
				{ TEXT("OCULAR"), 12.f, 31.f, false, TEXT("head"), FVector(10.f, -4.f, 8.f) },
				{ TEXT("DERMAL"), -28.f, 140.f, true, TEXT("clavicle_r"), FVector(6.f, 0.f, -12.f) },
				{ TEXT("SKELETAL"), 0.f, 196.f, false, TEXT("spine_02"), FVector(10.f, 0.f, 0.f) },
				{ TEXT("ARMS"), -72.f, 214.f, true, TEXT("lowerarm_r"), FVector::ZeroVector },
				{ TEXT("LEGS"), 32.f, 410.f, false, TEXT("calf_l"), FVector::ZeroVector },
			};
			const FSlateFontInfo LabelFont = NVUI::Font(NVUI::EFont::Mono, 11.f, 120);
			const FSlateFontInfo SubFont = NVUI::Font(NVUI::EFont::Mono, 9.f, 60);
			NVUI::FPainter M(G, Tint);
			const float Pulse = 0.6f + 0.4f * FMath::Sin(static_cast<float>(NVUI::Now()) * 3.f);
			for (const FCallout& C : Calls)
			{
				FVector2f Units(C.X, C.Y);
				if (bHolo && Rig.IsValid())
				{
					Rig->ProjectBone(C.Bone, C.Offset, Units);
				}
				const FVector2f A = Pt(Units.X, Units.Y);
				const float EdgeX = C.bLeft ? 18.f : S.X - 18.f;
				const FVector2f Knee(C.bLeft ? EdgeX + 70.f : EdgeX - 70.f, A.Y);
				NVUI::Lines(Out, LayerId + 2, G, { A, Knee, FVector2f(EdgeX, A.Y) }, NVUI::WithAlpha(NVUI::Accent, 0.35f) * Tint, 1.f);
				M.Diamond(A, 5.f, NVUI::WithAlpha(NVUI::Accent, Pulse));
				M.Diamond(A, 2.f, FLinearColor(0.f, 0.f, 0.f, 0.8f));
				const FString L = C.Name;
				const FString Sub = TEXT("SLOT OPEN");
				FVector2D LS(60.f, 14.f);
				if (FSlateApplication::IsInitialized() && FSlateApplication::Get().GetRenderer())
				{
					LS = FSlateApplication::Get().GetRenderer()->GetFontMeasureService()->Measure(L, LabelFont);
				}
				const float LX = C.bLeft ? EdgeX : EdgeX - static_cast<float>(LS.X);
				FSlateDrawElement::MakeText(Out, LayerId + 3, G.ToPaintGeometry(FVector2f(LS), FSlateLayoutTransform(FVector2f(LX, A.Y - static_cast<float>(LS.Y) - 2.f))),
					L, LabelFont, ESlateDrawEffect::None, NVUI::Accent * Tint);
				FSlateDrawElement::MakeText(Out, LayerId + 3, G.ToPaintGeometry(FVector2f(80.f, 14.f), FSlateLayoutTransform(FVector2f(C.bLeft ? EdgeX : EdgeX - 62.f, A.Y + 3.f))),
					Sub, SubFont, ESlateDrawEffect::None, NVUI::WithAlpha(NVUI::TextDim, 0.8f) * Tint);
			}
			M.Flush(Out, LayerId + 2);
			return LayerId + 3;
		}

	private:
		double Start = 0.0;
		TWeakObjectPtr<ANVHoloRig> Rig;
		FSlateBrush HoloBrush;
		bool bHolo = false;
	};

	ANVPlayerCharacter* PawnOf(const FNVMenuContext& Ctx)
	{
		return Ctx.HUD.IsValid() ? Ctx.HUD->GetHUDPawn() : nullptr;
	}

	TSharedRef<SWidget> ObjectiveRows(const FNVMenuContext& Ctx)
	{
		TSharedRef<SVerticalBox> Box = SNew(SVerticalBox);
		const UNVObjectiveSubsystem* Obj = Ctx.HUD.IsValid() ? UNVObjectiveSubsystem::Get(Ctx.HUD.Get()) : nullptr;
		if (!Obj || !Obj->GetCurrentMission())
		{
			Box->AddSlot().AutoHeight()[ NVUI::MakeText(LOCTEXT("NoOp", "No active operation."), NVUI::EFont::Body, 17.f, FSlateColor(NVUI::TextDim)) ];
			return Box;
		}
		Box->AddSlot().AutoHeight().Padding(0.f, 0.f, 0.f, 10.f)
		[
			NVUI::MakeText(Obj->GetCurrentMission()->MissionTitle.ToUpper(), NVUI::EFont::BodyBold, 26.f, FSlateColor(NVUI::Text), 40, true)
		];
		for (const FNVObjectiveDef& Def : Obj->GetActiveObjectives())
		{
			Box->AddSlot().AutoHeight().Padding(0.f, 3.f)
			[
				SNew(SHorizontalBox)
				+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Top).Padding(0.f, 5.f, 10.f, 0.f)
				[
					SNew(SNVDot).Color(Def.bOptional ? NVUI::TextDim : NVUI::Accent)
				]
				+ SHorizontalBox::Slot().FillWidth(1.f)
				[
					NVUI::MakeText(Def.DisplayText, NVUI::EFont::BodySemi, 18.f, FSlateColor(Def.bOptional ? NVUI::TextDim : NVUI::Text), 0, true)
				]
			];
		}
		return Box;
	}

	// ------------------------------------------------------------ SYSTEM

	TSharedRef<SWidget> BuildSystemPage(const FNVMenuContext& Ctx)
	{
		TSharedRef<SVerticalBox> Items = SNew(SVerticalBox);
		const TArray<FText>& PItems = ANVPlayerController::GetPauseItems();
		const TWeakObjectPtr<ANVPlayerController> PC = Ctx.PC;
		for (int32 i = 0; i < PItems.Num(); ++i)
		{
			Items->AddSlot().AutoHeight().Padding(0.f, 0.f, 0.f, 6.f)
			[
				SNew(SNVButton)
				.Index(FText::FromString(FString::Printf(TEXT("%02d"), i + 1)))
				.Text(PItems[i].ToUpper())
				.Size(22.f)
				.Selected_Lambda([PC, i]() { return PC.IsValid() && PC->GetPauseSelection() == i; })
				.OnHovered_Lambda([PC, i]() { if (PC.IsValid()) { PC->SetPauseSelection(i); } })
				.OnClicked_Lambda([PC, i]() { if (PC.IsValid()) { PC->ActivatePauseItem(i); } })
			];
		}

		const TWeakObjectPtr<ANVHUD> HUD = Ctx.HUD;
		auto Integrity = [HUD]()
		{
			const ANVPlayerCharacter* P = HUD.IsValid() ? HUD->GetHUDPawn() : nullptr;
			return P ? P->GetHealth()->GetHealthPercent() : 1.f;
		};

		return SNew(SHorizontalBox)
			+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Top).Padding(0.f, 0.f, 60.f, 0.f)
			[
				SNew(SBox).WidthOverride(440.f)
				[
					SNew(SVerticalBox)
					+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 0.f, 0.f, 16.f)
					[
						NVUI::MakeHeader(LOCTEXT("SysHdr", "Session"))
					]
					+ SVerticalBox::Slot().AutoHeight()
					[
						Items
					]
				]
			]
			+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Top)
			[
				SNew(SBox).WidthOverride(560.f)
				[
					SNew(SNVFrame).Header(LOCTEXT("OpHdr", "Current operation")).Padding(FMargin(24.f, 18.f))
					[
						SNew(SVerticalBox)
						+ SVerticalBox::Slot().AutoHeight()
						[
							ObjectiveRows(Ctx)
						]
						+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 24.f, 0.f, 8.f)
						[
							NVUI::MakeHeader(LOCTEXT("OperativeHdr", "Operative // Ghost"))
						]
						+ SVerticalBox::Slot().AutoHeight()
						[
							SNew(SHorizontalBox)
							+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(0.f, 0.f, 14.f, 0.f)
							[
								NVUI::MakeText(LOCTEXT("Integrity", "INTEGRITY"), NVUI::EFont::Mono, 12.f, FSlateColor(NVUI::TextDim), 100)
							]
							+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center)
							[
								SNew(SNVMeter).Value_Lambda(Integrity).Segments(24).Width(300.f).Height(8.f)
							]
							+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(14.f, 0.f, 0.f, 0.f)
							[
								NVUI::MakeText(TAttribute<FText>::CreateLambda([Integrity]() { return FText::AsPercent(Integrity()); }), NVUI::EFont::Mono, 13.f, FSlateColor(NVUI::Text))
							]
						]
					]
				]
			];
	}

	// ------------------------------------------------------------ CYBERWARE

	TSharedRef<SWidget> BuildCyberwarePage(const FNVMenuContext& Ctx)
	{
		TSharedRef<SVerticalBox> List = SNew(SVerticalBox);
		const TWeakObjectPtr<ANVHUD> HUD = Ctx.HUD;
		const ANVPlayerCharacter* Pawn = PawnOf(Ctx);
		const UNVAbilityComponent* AC = Pawn ? Pawn->GetAbilities() : nullptr;
		static const FName Actions[] = { TEXT("Ability1"), TEXT("Ability2"), TEXT("Ability3") };
		int32 Installed = 0;
		if (AC)
		{
			for (int32 i = 0; i < AC->Abilities.Num() && i < 3; ++i)
			{
				const UNVAbilityData* D = AC->Abilities[i];
				if (!D)
				{
					continue;
				}
				++Installed;
				auto Status = [HUD, i]()
				{
					const ANVPlayerCharacter* P = HUD.IsValid() ? HUD->GetHUDPawn() : nullptr;
					const FNVAbilityRuntime* R = P ? P->GetAbilities()->GetRuntime(i) : nullptr;
					if (!R)
					{
						return LOCTEXT("StNoSig", "NO SIGNAL");
					}
					if (R->bDisabled)
					{
						return LOCTEXT("StOffline", "OFFLINE // FAULT");
					}
					if (R->ActiveTimeLeft > 0.f)
					{
						return FText::Format(LOCTEXT("StActive", "ACTIVE // {0}s"), FText::AsNumber(FMath::CeilToInt(R->ActiveTimeLeft)));
					}
					if (R->CooldownLeft > 0.f)
					{
						return FText::Format(LOCTEXT("StCool", "RECHARGING // {0}s"), FText::AsNumber(FMath::CeilToInt(R->CooldownLeft)));
					}
					return LOCTEXT("StOnline", "ONLINE");
				};
				auto StatusColor = [HUD, i]()
				{
					const ANVPlayerCharacter* P = HUD.IsValid() ? HUD->GetHUDPawn() : nullptr;
					const FNVAbilityRuntime* R = P ? P->GetAbilities()->GetRuntime(i) : nullptr;
					return FSlateColor(!R || R->bDisabled ? NVUI::Warning : (R->CooldownLeft > 0.f ? NVUI::TextDim : NVUI::Accent));
				};
				const FName Action = Actions[i];
				List->AddSlot().AutoHeight().Padding(0.f, 0.f, 0.f, 8.f)
				[
					SNew(SNVFrame).Cut(10.f).Padding(FMargin(14.f, 10.f)).Delay(0.05f * i).Trims(false)
					[
						SNew(SHorizontalBox)
						+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(0.f, 0.f, 16.f, 0.f)
						[
							SNew(SNVIcon).Size(38.f).Icon(NVUI::IconForAbility(D->AbilityTag))
						]
						+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(0.f, 0.f, 16.f, 0.f)
						[
							SNew(SNVKeyCap).Key_Lambda([HUD, Action]() { return HUD.IsValid() ? HUD->KeyCap(Action) : FText::GetEmpty(); })
						]
						+ SHorizontalBox::Slot().FillWidth(1.f).VAlign(VAlign_Center)
						[
							SNew(SVerticalBox)
							+ SVerticalBox::Slot().AutoHeight()
							[
								NVUI::MakeText(D->DisplayName.ToUpper(), NVUI::EFont::BodyBold, 20.f, FSlateColor(NVUI::Text), 40)
							]
							+ SVerticalBox::Slot().AutoHeight()
							[
								NVUI::MakeText(TAttribute<FText>::CreateLambda(Status), NVUI::EFont::Mono, 11.f, TAttribute<FSlateColor>::CreateLambda(StatusColor), 100)
							]
						]
						+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center)
						[
							NVUI::MakeText(FText::Format(LOCTEXT("SlotN", "SLOT {0}"), FText::AsNumber(i + 1)), NVUI::EFont::Mono, 11.f, FSlateColor(NVUI::TextDim), 100)
						]
					]
				];
			}
		}
		if (Installed == 0)
		{
			List->AddSlot().AutoHeight()[ NVUI::MakeText(LOCTEXT("NoImpl", "No implants detected."), NVUI::EFont::Body, 17.f, FSlateColor(NVUI::TextDim)) ];
		}

		TSharedRef<SVerticalBox> Slots = SNew(SVerticalBox);
		static const TCHAR* BodySlots[] = { TEXT("NEURAL"), TEXT("OCULAR"), TEXT("DERMAL"), TEXT("SKELETAL"), TEXT("ARMS"), TEXT("LEGS") };
		for (int32 i = 0; i < static_cast<int32>(UE_ARRAY_COUNT(BodySlots)); ++i)
		{
			Slots->AddSlot().AutoHeight()
			[
				SNew(SNVButton)
				.Index(FText::FromString(FString::Printf(TEXT("%02d"), i + 1)))
				.Text(FText::FromString(BodySlots[i]))
				.Detail(LOCTEXT("SlotOpen", "SLOT OPEN // NO IMPLANT"))
				.Size(17.f)
			];
		}

		return SNew(SHorizontalBox)
			+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Top).Padding(0.f, 0.f, 48.f, 0.f)
			[
				SNew(SBox).WidthOverride(560.f)
				[
					SNew(SVerticalBox)
					+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 0.f, 0.f, 12.f)
					[
						NVUI::MakeHeader(FText::Format(LOCTEXT("ActiveImpl", "Active implants // {0} installed"), FText::AsNumber(Installed)))
					]
					+ SVerticalBox::Slot().AutoHeight()
					[
						List
					]
					+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 22.f, 0.f, 10.f)
					[
						NVUI::MakeHeader(LOCTEXT("BodySlots", "Body slots"))
					]
					+ SVerticalBox::Slot().AutoHeight()
					[
						Slots
					]
				]
			]
			+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Top)
			[
				SNew(SNVFrame).Header(LOCTEXT("Diag", "Implant diagnostics")).Padding(FMargin(20.f, 16.f))
				[
					SNew(SBox).WidthOverride(460.f).HeightOverride(560.f)
					[
						SNew(SNVBodyScan)
						.Rig(TWeakObjectPtr<ANVHoloRig>(ANVHoloRig::Get(Pawn ? Pawn->GetWorld() : nullptr,
							Pawn && Pawn->GetMesh() ? Pawn->GetMesh()->GetSkeletalMeshAsset() : nullptr)))
					]
				]
			];
	}

	// ------------------------------------------------------------ UPGRADES

	TSharedRef<SWidget> BuildUpgradesPage(const FNVMenuContext& Ctx)
	{
		static const TCHAR* LineNames[] = { TEXT("BALLISTICS"), TEXT("OPTICS"), TEXT("CHASSIS"), TEXT("MOBILITY") };
		static const TCHAR* Tiers[] = { TEXT("I"), TEXT("II"), TEXT("III") };
		TSharedRef<SUniformGridPanel> Grid = SNew(SUniformGridPanel).SlotPadding(FMargin(6.f));
		for (int32 Col = 0; Col < 4; ++Col)
		{
			for (int32 Row = 0; Row < 3; ++Row)
			{
				Grid->AddSlot(Col, Row)
				[
					SNew(SNVFrame).Cut(10.f).Padding(FMargin(16.f, 12.f)).Delay(0.03f * (Col + Row * 4)).FillAlpha(0.8f)
					.Accent(NVUI::WithAlpha(NVUI::Accent, Row == 0 ? 1.f : 0.5f))
					[
						SNew(SVerticalBox)
						+ SVerticalBox::Slot().AutoHeight()
						[
							NVUI::MakeText(FText::FromString(FString::Printf(TEXT("%s // TIER %s"), LineNames[Col], Tiers[Row])), NVUI::EFont::Mono, 11.f, FSlateColor(Row == 0 ? NVUI::Accent : NVUI::TextDim), 100)
						]
						+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 8.f, 0.f, 2.f)
						[
							NVUI::MakeText(LOCTEXT("Locked", "LOCKED"), NVUI::EFont::BodyBold, 20.f, FSlateColor(NVUI::WithAlpha(NVUI::Text, 0.55f)), 160)
						]
						+ SVerticalBox::Slot().AutoHeight()
						[
							NVUI::MakeText(LOCTEXT("ReqShards", "REQUIRES DATA SHARDS"), NVUI::EFont::Mono, 10.f, FSlateColor(NVUI::WithAlpha(NVUI::TextDim, 0.8f)), 60)
						]
					]
				];
			}
		}
		return SNew(SBox).WidthOverride(1100.f)
			[
				SNew(SVerticalBox)
				+ SVerticalBox::Slot().AutoHeight().Padding(6.f, 0.f, 6.f, 14.f)
				[
					SNew(SHorizontalBox)
					+ SHorizontalBox::Slot().FillWidth(1.f).VAlign(VAlign_Center)
					[
						NVUI::MakeHeader(LOCTEXT("UpgHdr", "Upgrade matrix"))
					]
					+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(20.f, 0.f, 0.f, 0.f)
					[
						NVUI::MakeText(LOCTEXT("Shards", "DATA SHARDS  000"), NVUI::EFont::Mono, 13.f, FSlateColor(NVUI::Warning), 120)
					]
				]
				+ SVerticalBox::Slot().AutoHeight()
				[
					Grid
				]
			];
	}

	// ------------------------------------------------------------ SKILLS

	TSharedRef<SWidget> BuildSkillsPage(const FNVMenuContext& Ctx)
	{
		static const TCHAR* Trees[] = { TEXT("COMBAT"), TEXT("INFILTRATION"), TEXT("NETRUNNING") };
		TSharedRef<SHorizontalBox> Cols = SNew(SHorizontalBox);
		for (int32 t = 0; t < 3; ++t)
		{
			TSharedRef<SVerticalBox> Col = SNew(SVerticalBox);
			Col->AddSlot().AutoHeight().Padding(0.f, 0.f, 0.f, 14.f)
			[
				NVUI::MakeHeader(FText::FromString(Trees[t]))
			];
			for (int32 n = 0; n < 4; ++n)
			{
				if (n > 0)
				{
					Col->AddSlot().AutoHeight().HAlign(HAlign_Center)[ SNew(SNVConnector) ];
				}
				Col->AddSlot().AutoHeight()
				[
					SNew(SNVFrame).Cut(9.f).Padding(FMargin(16.f, 10.f)).Delay(0.04f * (n + t)).FillAlpha(0.8f).Trims(n == 0)
					.Accent(NVUI::WithAlpha(NVUI::Accent, n == 0 ? 1.f : 0.45f))
					[
						SNew(SHorizontalBox)
						+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(0.f, 0.f, 12.f, 0.f)
						[
							SNew(SNVDot).Color(n == 0 ? NVUI::Accent : NVUI::WithAlpha(NVUI::TextDim, 0.6f)).Radius(5.f)
						]
						+ SHorizontalBox::Slot().FillWidth(1.f).VAlign(VAlign_Center)
						[
							SNew(SVerticalBox)
							+ SVerticalBox::Slot().AutoHeight()
							[
								NVUI::MakeText(FText::FromString(FString::Printf(TEXT("NODE %d.%d"), t + 1, n + 1)), NVUI::EFont::Mono, 10.f, FSlateColor(NVUI::TextDim), 100)
							]
							+ SVerticalBox::Slot().AutoHeight()
							[
								NVUI::MakeText(n == 0 ? LOCTEXT("Uncal", "UNCALIBRATED") : LOCTEXT("Sealed", "SEALED"), NVUI::EFont::BodySemi, 18.f,
									FSlateColor(n == 0 ? NVUI::Text : NVUI::WithAlpha(NVUI::Text, 0.45f)), 80)
							]
						]
					]
				];
			}
			Cols->AddSlot().FillWidth(1.f).Padding(t == 0 ? 0.f : 28.f, 0.f, 0.f, 0.f)[ Col ];
		}
		return SNew(SBox).WidthOverride(1100.f)
			[
				SNew(SVerticalBox)
				+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 0.f, 0.f, 22.f)
				[
					SNew(SHorizontalBox)
					+ SHorizontalBox::Slot().FillWidth(1.f).VAlign(VAlign_Center)
					[
						NVUI::MakeText(LOCTEXT("NeuralMap", "NEURAL MAP INCOMPLETE // AWAITING CALIBRATION"), NVUI::EFont::Mono, 13.f, FSlateColor(NVUI::Warning), 120)
					]
					+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center)
					[
						NVUI::MakeText(LOCTEXT("SkillPts", "SKILL POINTS  00"), NVUI::EFont::Mono, 13.f, FSlateColor(NVUI::Accent), 120)
					]
				]
				+ SVerticalBox::Slot().AutoHeight()
				[
					Cols
				]
			];
	}

	// ------------------------------------------------------------ COMMS LOG

	TSharedRef<SWidget> BuildCommsPage(const FNVMenuContext& Ctx)
	{
		TSharedRef<SScrollBox> Scroll = SNew(SScrollBox);
		const TArray<FNVCommsLogEntry>* Log = Ctx.HUD.IsValid() ? &Ctx.HUD->GetCommsLog() : nullptr;
		if (!Log || Log->Num() == 0)
		{
			Scroll->AddSlot()[ NVUI::MakeText(LOCTEXT("NoComms", "NO TRANSMISSIONS LOGGED."), NVUI::EFont::Mono, 13.f, FSlateColor(NVUI::TextDim), 100) ];
		}
		else
		{
			for (int32 i = Log->Num() - 1; i >= 0; --i)
			{
				const FNVCommsLogEntry& E = (*Log)[i];
				const int32 Secs = FMath::FloorToInt(E.Time);
				const FText Stamp = FText::FromString(FString::Printf(TEXT("T+%02d:%02d"), Secs / 60, Secs % 60));
				const FText Channel = E.Message.Channel.IsEmpty() ? LOCTEXT("Direct", "DIRECT") : E.Message.Channel.ToUpper();
				const FLinearColor Acc = E.Message.bPriority ? NVUI::Warning : NVUI::Accent;
				Scroll->AddSlot().Padding(0.f, 0.f, 12.f, 10.f)
				[
					SNew(SNVFrame).Spine(true).Accent(Acc).Cut(10.f).Padding(FMargin(16.f, 10.f)).AnimateIn(false).Trims(false)
					[
						SNew(SVerticalBox)
						+ SVerticalBox::Slot().AutoHeight()
						[
							SNew(SHorizontalBox)
							+ SHorizontalBox::Slot().AutoWidth().Padding(0.f, 0.f, 14.f, 0.f)
							[
								NVUI::MakeText(Stamp, NVUI::EFont::Mono, 11.f, FSlateColor(NVUI::TextDim), 80)
							]
							+ SHorizontalBox::Slot().AutoWidth().Padding(0.f, 0.f, 14.f, 0.f)
							[
								NVUI::MakeText(Channel, NVUI::EFont::Mono, 11.f, FSlateColor(Acc), 120)
							]
							+ SHorizontalBox::Slot().AutoWidth()
							[
								NVUI::MakeText(E.Message.Sender.ToUpper(), NVUI::EFont::BodyBold, 16.f, FSlateColor(NVUI::Text), 40)
							]
						]
						+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 4.f, 0.f, 0.f)
						[
							NVUI::MakeText(E.Message.Body, NVUI::EFont::Body, 17.f, FSlateColor(NVUI::WithAlpha(NVUI::Text, 0.9f)), 0, true)
						]
					]
				];
			}
		}
		return SNew(SBox).WidthOverride(900.f)
			[
				SNew(SVerticalBox)
				+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 0.f, 0.f, 14.f)
				[
					NVUI::MakeHeader(FText::Format(LOCTEXT("CommsHdr", "Comms log // {0} transmissions"), FText::AsNumber(Log ? Log->Num() : 0)))
				]
				+ SVerticalBox::Slot().FillHeight(1.f)
				[
					Scroll
				]
			];
	}
}

TArray<FNVMenuPage>& NVUI::MenuPages()
{
	static TArray<FNVMenuPage> Pages;
	static bool bInit = false;
	if (!bInit)
	{
		bInit = true;
		Pages.Add({ TEXT("System"), LOCTEXT("TabSystem", "System"), &BuildSystemPage });
		Pages.Add({ TEXT("Cyberware"), LOCTEXT("TabCyber", "Cyberware"), &BuildCyberwarePage });
		Pages.Add({ TEXT("Upgrades"), LOCTEXT("TabUpg", "Upgrades"), &BuildUpgradesPage });
		Pages.Add({ TEXT("Skills"), LOCTEXT("TabSkills", "Skills"), &BuildSkillsPage });
		Pages.Add({ TEXT("Comms"), LOCTEXT("TabComms", "Comms"), &BuildCommsPage });
	}
	return Pages;
}

void NVUI::RegisterMenuPage(const FNVMenuPage& Page, int32 InsertAt)
{
	TArray<FNVMenuPage>& Pages = MenuPages();
	for (FNVMenuPage& P : Pages)
	{
		if (P.Id == Page.Id)
		{
			P = Page;
			return;
		}
	}
	if (InsertAt >= 0 && InsertAt <= Pages.Num())
	{
		Pages.Insert(Page, InsertAt);
	}
	else
	{
		Pages.Add(Page);
	}
}

// ================================================================ shell

void SNVMenuShell::Construct(const FArguments& InArgs)
{
	Ctx = InArgs._Context;
	OpenTime = NVUI::Now();
	const TWeakObjectPtr<ANVPlayerController> PC = Ctx.PC;
	const TWeakObjectPtr<ANVHUD> HUD = Ctx.HUD;

	TSharedRef<SHorizontalBox> Tabs = SNew(SHorizontalBox);
	TSharedRef<SWidgetSwitcher> Switcher = SNew(SWidgetSwitcher)
		.WidgetIndex_Lambda([PC]() { return PC.IsValid() ? PC->GetMenuTab() : 0; });
	const TArray<FNVMenuPage>& Pages = NVUI::MenuPages();
	for (int32 i = 0; i < Pages.Num(); ++i)
	{
		Tabs->AddSlot().AutoWidth().Padding(4.f, 0.f)
		[
			SNew(SNVTab)
			.Text(Pages[i].Label)
			.Active_Lambda([PC, i]() { return PC.IsValid() && PC->GetMenuTab() == i; })
			.OnClicked_Lambda([PC, i]() { if (PC.IsValid()) { PC->SetMenuTab(i); } })
		];
		Switcher->AddSlot()
		[
			Pages[i].Build ? Pages[i].Build(Ctx) : SNullWidget::NullWidget
		];
	}

	auto Pad = [HUD]() { return HUD.IsValid() && HUD->IsUsingGamepad(); };
	auto PS = [HUD]() { return HUD.IsValid() && HUD->bPlayStationGlyphs; };
	auto Hint = [](TAttribute<FText> Key, const FText& Caption)
	{
		return SNew(SHorizontalBox)
			+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(0.f, 0.f, 8.f, 0.f)
			[
				SNew(SNVKeyCap).Key(Key).Size(11.f)
			]
			+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(0.f, 0.f, 26.f, 0.f)
			[
				NVUI::MakeText(Caption, NVUI::EFont::Mono, 11.f, FSlateColor(NVUI::TextDim), 120)
			];
	};
	const TAttribute<FText> TabKeys = TAttribute<FText>::CreateLambda([Pad, PS]() { return FText::FromString(Pad() ? (PS() ? TEXT("L1 / R1") : TEXT("LB / RB")) : TEXT("Q / E")); });
	const TAttribute<FText> SelKeys = TAttribute<FText>::CreateLambda([Pad, PS]() { return FText::FromString(Pad() ? (PS() ? TEXT("CROSS") : TEXT("A")) : TEXT("ENTER")); });
	const TAttribute<FText> BackKeys = TAttribute<FText>::CreateLambda([Pad, PS]() { return FText::FromString(Pad() ? (PS() ? TEXT("OPTIONS") : TEXT("MENU")) : TEXT("ESC")); });

	ChildSlot
	[
		SNew(SVerticalBox)
		+ SVerticalBox::Slot().AutoHeight().Padding(80.f, 46.f, 80.f, 0.f)
		[
			SNew(SHorizontalBox)
			+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Bottom)
			[
				SNew(SVerticalBox)
				+ SVerticalBox::Slot().AutoHeight()
				[
					NVUI::MakeText(LOCTEXT("OSName", "GHOST-OS"), NVUI::EFont::Display, 24.f, FSlateColor(NVUI::Text), 420)
				]
				+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 4.f, 0.f, 0.f)
				[
					NVUI::MakeText(LOCTEXT("OSSub", "NEURAL INTERFACE  //  BUILD 0.9.4  //  LINK STABLE"), NVUI::EFont::Mono, 11.f, FSlateColor(NVUI::TextDim), 100)
				]
			]
			+ SHorizontalBox::Slot().FillWidth(1.f).HAlign(HAlign_Center).VAlign(VAlign_Bottom)
			[
				Tabs
			]
			+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Bottom)
			[
				SNew(SVerticalBox)
				+ SVerticalBox::Slot().AutoHeight().HAlign(HAlign_Right)
				[
					NVUI::MakeText(LOCTEXT("Paused", "SIMULATION PAUSED"), NVUI::EFont::Mono, 12.f, FSlateColor(NVUI::Warning), 160)
				]
				+ SVerticalBox::Slot().AutoHeight().HAlign(HAlign_Right).Padding(0.f, 4.f, 0.f, 0.f)
				[
					NVUI::MakeText(TAttribute<FText>::CreateLambda([]()
					{
						const FDateTime T = FDateTime::Now();
						return FText::FromString(FString::Printf(TEXT("%02d:%02d:%02d  //  SYNC 98.2%%"), T.GetHour(), T.GetMinute(), T.GetSecond()));
					}), NVUI::EFont::Mono, 11.f, FSlateColor(NVUI::TextDim), 100)
				]
			]
		]
		+ SVerticalBox::Slot().AutoHeight().Padding(80.f, 10.f, 80.f, 0.f)
		[
			SNew(SNVRule).Color(NVUI::WithAlpha(NVUI::Accent, 0.35f))
		]
		+ SVerticalBox::Slot().FillHeight(1.f).Padding(80.f, 36.f, 80.f, 20.f)
		[
			Switcher
		]
		+ SVerticalBox::Slot().AutoHeight().Padding(80.f, 0.f, 80.f, 40.f)
		[
			SNew(SHorizontalBox)
			+ SHorizontalBox::Slot().AutoWidth()[ Hint(TabKeys, LOCTEXT("HintTabs", "SWITCH TAB")) ]
			+ SHorizontalBox::Slot().AutoWidth()[ Hint(SelKeys, LOCTEXT("HintSel", "SELECT")) ]
			+ SHorizontalBox::Slot().AutoWidth()[ Hint(BackKeys, LOCTEXT("HintBack", "RESUME")) ]
			+ SHorizontalBox::Slot().FillWidth(1.f).HAlign(HAlign_Right).VAlign(VAlign_Center)
			[
				NVUI::MakeText(LOCTEXT("Footer", "NEON VEIL  //  ETHERION SYSTEMS INTERNAL"), NVUI::EFont::Mono, 10.f, FSlateColor(NVUI::WithAlpha(NVUI::TextDim, 0.6f)), 160)
			]
		]
	];
}

int32 SNVMenuShell::OnPaint(const FPaintArgs& Args, const FGeometry& G, const FSlateRect& Culling, FSlateWindowElementList& Out,
                            int32 LayerId, const FWidgetStyle& Style, bool bParentEnabled) const
{
	const float Open = FMath::Clamp(static_cast<float>((NVUI::Now() - OpenTime) / 0.22), 0.f, 1.f);
	const FLinearColor Tint = Style.GetColorAndOpacityTint() * FLinearColor(1.f, 1.f, 1.f, Open);
	const FVector2f S(G.GetLocalSize());
	NVUI::FPainter P(G, Tint);
	P.Rect(FVector2f::ZeroVector, S, FLinearColor(0.004f, 0.008f, 0.012f, 0.84f));
	// faint grid
	for (float X = 0.f; X < S.X; X += 80.f)
	{
		P.Rect(FVector2f(X, 0.f), FVector2f(1.f, S.Y), NVUI::WithAlpha(NVUI::Accent, 0.022f));
	}
	for (float Y = 0.f; Y < S.Y; Y += 80.f)
	{
		P.Rect(FVector2f(0.f, Y), FVector2f(S.X, 1.f), NVUI::WithAlpha(NVUI::Accent, 0.022f));
	}
	// scanlines + vignette
	P.Scanlines(FVector2f::ZeroVector, S, 3.f, FLinearColor(0.f, 0.f, 0.f, 0.18f));
	P.RectV(FVector2f::ZeroVector, FVector2f(S.X, S.Y * 0.25f), FLinearColor(0.f, 0.f, 0.f, 0.5f), FLinearColor(0.f, 0.f, 0.f, 0.f));
	P.RectV(FVector2f(0.f, S.Y * 0.75f), FVector2f(S.X, S.Y * 0.25f), FLinearColor(0.f, 0.f, 0.f, 0.f), FLinearColor(0.f, 0.f, 0.f, 0.55f));
	P.RectH(FVector2f::ZeroVector, FVector2f(S.X * 0.2f, S.Y), FLinearColor(0.f, 0.f, 0.f, 0.4f), FLinearColor(0.f, 0.f, 0.f, 0.f));
	P.RectH(FVector2f(S.X * 0.8f, 0.f), FVector2f(S.X * 0.2f, S.Y), FLinearColor(0.f, 0.f, 0.f, 0.f), FLinearColor(0.f, 0.f, 0.f, 0.4f));
	// corner brackets
	const float In = 26.f, L = 46.f;
	const FLinearColor B = NVUI::WithAlpha(NVUI::Accent, 0.65f);
	P.Rect(FVector2f(In, In), FVector2f(L, 2.f), B);
	P.Rect(FVector2f(In, In), FVector2f(2.f, L), B);
	P.Rect(FVector2f(S.X - In - L, In), FVector2f(L, 2.f), B);
	P.Rect(FVector2f(S.X - In - 2.f, In), FVector2f(2.f, L), B);
	P.Rect(FVector2f(In, S.Y - In - 2.f), FVector2f(L, 2.f), B);
	P.Rect(FVector2f(In, S.Y - In - L), FVector2f(2.f, L), B);
	P.Rect(FVector2f(S.X - In - L, S.Y - In - 2.f), FVector2f(L, 2.f), B);
	P.Rect(FVector2f(S.X - In - 2.f, S.Y - In - L), FVector2f(2.f, L), B);
	P.Flush(Out, LayerId);

	FWidgetStyle CS(Style);
	CS.BlendColorAndOpacityTint(FLinearColor(1.f, 1.f, 1.f, Open));
	return SCompoundWidget::OnPaint(Args, G, Culling, Out, LayerId + 1, CS, bParentEnabled);
}

#undef LOCTEXT_NAMESPACE
