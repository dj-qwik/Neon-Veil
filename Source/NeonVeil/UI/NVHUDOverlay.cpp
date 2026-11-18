#include "UI/NVHUDOverlay.h"
#include "UI/NVHUD.h"
#include "UI/NVMenuShell.h"
#include "UI/NVOpeningTitle.h"
#include "UI/NVUIWidgets.h"
#include "Core/NVPlayerController.h"
#include "Character/NVPlayerCharacter.h"
#include "Combat/NVHealthComponent.h"
#include "Combat/NVWeaponComponent.h"
#include "Combat/NVWeaponData.h"
#include "Abilities/NVAbilityComponent.h"
#include "Abilities/NVAbilityData.h"
#include "Interaction/NVInteractionComponent.h"
#include "Interaction/NVInteractable.h"
#include "Objectives/NVObjectiveSubsystem.h"
#include "Objectives/NVObjectiveData.h"

#include "Engine/World.h"
#include "Widgets/SNullWidget.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/SOverlay.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Layout/SConstraintCanvas.h"
#include "Widgets/Text/STextBlock.h"

#define LOCTEXT_NAMESPACE "NeonVeilUI"


namespace
{
	float Ease(float T) { return 1.f - FMath::Pow(1.f - FMath::Clamp(T, 0.f, 1.f), 3.f); }

	/** Painted diamond marker. */
	class SNVMark : public SLeafWidget
	{
	public:
		SLATE_BEGIN_ARGS(SNVMark) : _Color(NVUI::Accent), _Radius(4.f) {}
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

	/** Centred banner: "OBJECTIVE COMPLETE" between expanding rules. */
	class SNVNoticeBanner : public SCompoundWidget
	{
	public:
		SLATE_BEGIN_ARGS(SNVNoticeBanner) : _Color(NVUI::Accent) {}
			SLATE_ARGUMENT(FText, Text)
			SLATE_ARGUMENT(FLinearColor, Color)
			SLATE_ATTRIBUTE(float, Fade)
		SLATE_END_ARGS()

		void Construct(const FArguments& InArgs)
		{
			Color = InArgs._Color;
			Fade = InArgs._Fade;
			Start = NVUI::Now();
			ChildSlot.Padding(FMargin(30.f, 8.f, 30.f, 9.f))
			[
				SNew(SNVTypeText).Text(InArgs._Text.ToUpper()).Font(NVUI::Font(NVUI::EFont::Display, 17.f, 380)).Color(FSlateColor(Color)).CharsPerSecond(55.f).AutoWrap(false).ShowCursor(false)
			];
		}

		virtual int32 OnPaint(const FPaintArgs& Args, const FGeometry& G, const FSlateRect& Culling, FSlateWindowElementList& Out, int32 LayerId,
		                      const FWidgetStyle& Style, bool bParentEnabled) const override
		{
			const float A = Fade.Get(1.f);
			const float E = Ease(static_cast<float>((NVUI::Now() - Start) / 0.4));
			const FVector2f S(G.GetLocalSize());
			const FLinearColor Tint = Style.GetColorAndOpacityTint() * FLinearColor(1.f, 1.f, 1.f, A);
			NVUI::FPainter P(G, Tint);
			const float Mid = FMath::FloorToFloat(S.Y * 0.5f);
			const float L = 240.f * E;
			P.RectH(FVector2f(-L * 0.6f, 0.f), FVector2f(S.X * 0.5f + L * 0.6f, S.Y), FLinearColor(0.f, 0.f, 0.f, 0.f), FLinearColor(0.005f, 0.012f, 0.018f, 0.82f));
			P.RectH(FVector2f(S.X * 0.5f, 0.f), FVector2f(S.X * 0.5f + L * 0.6f, S.Y), FLinearColor(0.005f, 0.012f, 0.018f, 0.82f), FLinearColor(0.f, 0.f, 0.f, 0.f));
			P.RectH(FVector2f(0.f, 0.f), FVector2f(S.X * 0.5f, S.Y), NVUI::WithAlpha(Color, 0.f), NVUI::WithAlpha(Color, 0.10f));
			P.RectH(FVector2f(S.X * 0.5f, 0.f), FVector2f(S.X * 0.5f, S.Y), NVUI::WithAlpha(Color, 0.10f), NVUI::WithAlpha(Color, 0.f));
			P.RectH(FVector2f(-L, Mid), FVector2f(L - 6.f, 1.f), NVUI::WithAlpha(Color, 0.f), Color);
			P.RectH(FVector2f(S.X + 6.f, Mid), FVector2f(L - 6.f, 1.f), Color, NVUI::WithAlpha(Color, 0.f));
			P.Diamond(FVector2f(-3.f, Mid + 0.5f), 4.f, Color);
			P.Diamond(FVector2f(S.X + 3.f, Mid + 0.5f), 4.f, Color);
			P.Rect(FVector2f(S.X * 0.5f - 40.f * E, 0.f), FVector2f(80.f * E, 1.f), NVUI::WithAlpha(Color, 0.6f));
			P.Rect(FVector2f(S.X * 0.5f - 40.f * E, S.Y - 1.f), FVector2f(80.f * E, 1.f), NVUI::WithAlpha(Color, 0.6f));
			P.Flush(Out, LayerId);
			FWidgetStyle CS(Style);
			CS.BlendColorAndOpacityTint(FLinearColor(1.f, 1.f, 1.f, A));
			return SCompoundWidget::OnPaint(Args, G, Culling, Out, LayerId + 1, CS, bParentEnabled);
		}

	private:
		FLinearColor Color;
		TAttribute<float> Fade;
		double Start = 0.0;
	};

	/** Large centred title card (end of mission, chapter titles). */
	class SNVTitleCard : public SCompoundWidget
	{
	public:
		SLATE_BEGIN_ARGS(SNVTitleCard) {}
			SLATE_ARGUMENT(FText, Title)
			SLATE_ARGUMENT(FText, Subtitle)
			SLATE_ATTRIBUTE(float, Fade)
		SLATE_END_ARGS()

		void Construct(const FArguments& InArgs)
		{
			Fade = InArgs._Fade;
			Start = NVUI::Now();
			ChildSlot.Padding(FMargin(60.f, 22.f))
			[
				SNew(SVerticalBox)
				+ SVerticalBox::Slot().AutoHeight().HAlign(HAlign_Center)
				[
					SNew(SNVTypeText).Text(InArgs._Title.ToUpper()).Font(NVUI::Font(NVUI::EFont::Display, 40.f, 420)).CharsPerSecond(26.f).AutoWrap(false).ShowCursor(false)
					.Justify(ETextJustify::Center)
				]
				+ SVerticalBox::Slot().AutoHeight().HAlign(HAlign_Center).Padding(0.f, 14.f, 0.f, 0.f)
				[
					SNew(SNVTypeText).Text(InArgs._Subtitle.ToUpper()).Font(NVUI::Font(NVUI::EFont::Mono, 14.f, 300)).Color(FSlateColor(NVUI::Accent)).CharsPerSecond(40.f)
					.Delay(0.6f).AutoWrap(false).ShowCursor(false).Justify(ETextJustify::Center)
				]
			];
		}

		virtual int32 OnPaint(const FPaintArgs& Args, const FGeometry& G, const FSlateRect& Culling, FSlateWindowElementList& Out, int32 LayerId,
		                      const FWidgetStyle& Style, bool bParentEnabled) const override
		{
			const float A = Fade.Get(1.f);
			const float E = Ease(static_cast<float>((NVUI::Now() - Start) / 0.7));
			const FVector2f S(G.GetLocalSize());
			const FLinearColor Tint = Style.GetColorAndOpacityTint() * FLinearColor(1.f, 1.f, 1.f, A);
			NVUI::FPainter P(G, Tint);
			const float Ext = 300.f;
			P.RectH(FVector2f(-Ext, 0.f), FVector2f(S.X * 0.5f + Ext, S.Y), FLinearColor(0.f, 0.f, 0.f, 0.f), FLinearColor(0.f, 0.f, 0.f, 0.6f));
			P.RectH(FVector2f(S.X * 0.5f, 0.f), FVector2f(S.X * 0.5f + Ext, S.Y), FLinearColor(0.f, 0.f, 0.f, 0.6f), FLinearColor(0.f, 0.f, 0.f, 0.f));
			const float W = (S.X + Ext) * E;
			P.RectH(FVector2f(S.X * 0.5f - W * 0.5f, 0.f), FVector2f(W * 0.5f, 1.f), NVUI::WithAlpha(NVUI::Accent, 0.f), NVUI::Accent);
			P.RectH(FVector2f(S.X * 0.5f, 0.f), FVector2f(W * 0.5f, 1.f), NVUI::Accent, NVUI::WithAlpha(NVUI::Accent, 0.f));
			P.RectH(FVector2f(S.X * 0.5f - W * 0.5f, S.Y - 1.f), FVector2f(W * 0.5f, 1.f), NVUI::WithAlpha(NVUI::Accent, 0.f), NVUI::WithAlpha(NVUI::Accent, 0.5f));
			P.RectH(FVector2f(S.X * 0.5f, S.Y - 1.f), FVector2f(W * 0.5f, 1.f), NVUI::WithAlpha(NVUI::Accent, 0.5f), NVUI::WithAlpha(NVUI::Accent, 0.f));
			P.Scanlines(FVector2f(-Ext * E, 0.f), FVector2f(S.X + 2.f * Ext * E, S.Y), 3.f, FLinearColor(1.f, 1.f, 1.f, 0.025f));
			P.Flush(Out, LayerId);
			FWidgetStyle CS(Style);
			CS.BlendColorAndOpacityTint(FLinearColor(1.f, 1.f, 1.f, A));
			return SCompoundWidget::OnPaint(Args, G, Culling, Out, LayerId + 1, CS, bParentEnabled);
		}

	private:
		TAttribute<float> Fade;
		double Start = 0.0;
	};

	/** One cyberware slot above the vitals: label, state fill, key or cooldown underneath. */
	class SNVCyberSlot : public SCompoundWidget
	{
	public:
		SLATE_BEGIN_ARGS(SNVCyberSlot) : _Index(0) {}
			SLATE_ARGUMENT(TWeakObjectPtr<ANVHUD>, HUD)
			SLATE_ARGUMENT(int32, Index)
		SLATE_END_ARGS()

		static constexpr float Box = 60.f;
		static constexpr float SlotW = 92.f;

		void Construct(const FArguments& InArgs)
		{
			HUD = InArgs._HUD;
			Index = InArgs._Index;
			ChildSlot
			[
				SNew(SBox).WidthOverride(SlotW)
				[
					SNew(SVerticalBox)
					+ SVerticalBox::Slot().AutoHeight().HAlign(HAlign_Center)
					[
						SNew(SBox).WidthOverride(Box).HeightOverride(Box)
						[
							SNew(SOverlay)
							+ SOverlay::Slot().HAlign(HAlign_Center).VAlign(VAlign_Center)
							[
								SNew(SNVIcon).Size(34.f)
								.Icon_Lambda([this]() { const UNVAbilityData* D = Data(); return D ? NVUI::IconForAbility(D->AbilityTag) : NVUI::EIcon::Implant; })
								.Color_Lambda([this]() { return GetIconColor(); })
							]
							+ SOverlay::Slot().HAlign(HAlign_Center).VAlign(VAlign_Center)
							[
								NVUI::MakeText(TAttribute<FText>::CreateSP(this, &SNVCyberSlot::GetCooldown), NVUI::EFont::BodyBold, 22.f, FSlateColor(NVUI::Text))
							]
						]
					]
					+ SVerticalBox::Slot().AutoHeight().HAlign(HAlign_Center).Padding(0.f, 6.f, 0.f, 0.f)
					[
						SNew(STextBlock)
						.Text_Lambda([this]() { const UNVAbilityData* D = Data(); return D ? D->DisplayName.ToUpper() : FText::GetEmpty(); })
						.Font(NVUI::Font(NVUI::EFont::Mono, 10.f, 40))
						.ColorAndOpacity(TAttribute<FSlateColor>::CreateSP(this, &SNVCyberSlot::GetUnderColor))
						.WrapTextAt(SlotW)
						.Justification(ETextJustify::Center)
						.ShadowOffset(FVector2D(1.f, 1.f))
						.ShadowColorAndOpacity(FLinearColor(0.f, 0.f, 0.f, 0.7f))
					]
					+ SVerticalBox::Slot().AutoHeight().HAlign(HAlign_Center).Padding(0.f, 5.f, 0.f, 0.f)
					[
						SNew(SNVKeyCap).Size(10.f)
						.Key_Lambda([this]() { return GetUnder(); })
						.Color_Lambda([this]() { const FNVAbilityRuntime* R = Runtime(); return R && R->bDisabled ? NVUI::Warning : NVUI::WithAlpha(NVUI::Accent, 0.9f); })
					]
				]
			];
		}

		bool HasAbility() const { return Data() != nullptr; }

		virtual int32 OnPaint(const FPaintArgs& Args, const FGeometry& G, const FSlateRect& Culling, FSlateWindowElementList& Out, int32 LayerId,
		                      const FWidgetStyle& Style, bool bParentEnabled) const override
		{
			const FNVAbilityRuntime* R = Runtime();
			const FLinearColor Tint = Style.GetColorAndOpacityTint();
			const FVector2f B(Box, Box);
			// the box is centred at the top of the (wider) slot
			const FGeometry BoxG = G.MakeChild(FVector2f(Box, Box), FSlateLayoutTransform(FVector2f((G.GetLocalSize().X - Box) * 0.5f, 0.f)));
			NVUI::FPainter P(BoxG, Tint);
			P.PolyV(NVUI::ChamferPoints(FVector2f::ZeroVector, B, 10.f, false), FLinearColor(0.03f, 0.06f, 0.075f, 0.72f), FLinearColor(0.01f, 0.02f, 0.03f, 0.8f));
			FLinearColor Edge = NVUI::WithAlpha(NVUI::Accent, 0.45f);
			if (R && R->bDisabled)
			{
				Edge = NVUI::Warning;
				for (float X = -B.Y; X < B.X; X += 9.f)
				{
					P.Seg(FVector2f(FMath::Max(X, 0.f), FMath::Max(0.f, -X)), FVector2f(FMath::Min(X + B.Y, B.X), FMath::Min(B.Y, B.X - X)), 2.f, NVUI::WithAlpha(NVUI::Warning, 0.12f));
				}
			}
			else if (R && R->ActiveTimeLeft > 0.f)
			{
				const float F = HUD.IsValid() && HUD->GetHUDPawn() ? HUD->GetHUDPawn()->GetAbilities()->GetActiveFraction(Index) : 0.f;
				P.RectV(FVector2f(0.f, B.Y * (1.f - F)), FVector2f(B.X, B.Y * F), NVUI::WithAlpha(NVUI::Accent, 0.5f), NVUI::WithAlpha(NVUI::Accent, 0.2f));
				Edge = NVUI::Accent;
			}
			else if (R && R->CooldownLeft > 0.f)
			{
				const float F = HUD.IsValid() && HUD->GetHUDPawn() ? HUD->GetHUDPawn()->GetAbilities()->GetCooldownFraction(Index) : 0.f;
				P.Rect(FVector2f(0.f, 0.f), FVector2f(B.X, B.Y * F), FLinearColor(0.f, 0.f, 0.f, 0.55f));
				P.Rect(FVector2f(0.f, B.Y * F), FVector2f(B.X, 1.f), NVUI::WithAlpha(NVUI::Accent, 0.5f));
				Edge = NVUI::WithAlpha(NVUI::Accent, 0.25f);
			}
			else
			{
				P.Rect(FVector2f(4.f, B.Y - 4.f), FVector2f(B.X - 14.f, 2.f), NVUI::Accent);
				Edge = NVUI::WithAlpha(NVUI::Accent, 0.75f);
			}
			P.Flush(Out, LayerId);
			NVUI::Lines(Out, LayerId + 1, BoxG, NVUI::ChamferPoints(FVector2f(0.5f, 0.5f), B - FVector2f(1.f, 1.f), 10.f, true), Edge * Tint, 1.f);
			return SCompoundWidget::OnPaint(Args, G, Culling, Out, LayerId + 2, Style, bParentEnabled);
		}

	private:
		const UNVAbilityData* Data() const
		{
			const ANVPlayerCharacter* P = HUD.IsValid() ? HUD->GetHUDPawn() : nullptr;
			const UNVAbilityComponent* A = P ? P->GetAbilities() : nullptr;
			return A && A->Abilities.IsValidIndex(Index) ? A->Abilities[Index].Get() : nullptr;
		}
		const FNVAbilityRuntime* Runtime() const
		{
			const ANVPlayerCharacter* P = HUD.IsValid() ? HUD->GetHUDPawn() : nullptr;
			return P && P->GetAbilities() ? P->GetAbilities()->GetRuntime(Index) : nullptr;
		}
		FLinearColor GetIconColor() const
		{
			const FNVAbilityRuntime* R = Runtime();
			if (!R)
			{
				return NVUI::TextDim;
			}
			if (R->bDisabled)
			{
				return NVUI::WithAlpha(NVUI::Warning, 0.8f);
			}
			if (R->ActiveTimeLeft > 0.f)
			{
				return FLinearColor::White;
			}
			return R->CooldownLeft > 0.f ? NVUI::WithAlpha(NVUI::Accent, 0.3f) : NVUI::Accent;
		}
		FText GetCooldown() const
		{
			const FNVAbilityRuntime* R = Runtime();
			return R && !R->bDisabled && R->CooldownLeft > 0.f ? FText::AsNumber(FMath::CeilToInt(R->CooldownLeft)) : FText::GetEmpty();
		}
		FText GetUnder() const
		{
			static const FName Actions[] = { TEXT("Ability1"), TEXT("Ability2"), TEXT("Ability3") };
			const FNVAbilityRuntime* R = Runtime();
			if (R && R->bDisabled)
			{
				return LOCTEXT("SlotOffline", "OFFLINE");
			}
			return HUD.IsValid() && Index < 3 ? HUD->KeyCap(Actions[Index]) : FText::GetEmpty();
		}
		FSlateColor GetUnderColor() const
		{
			const FNVAbilityRuntime* R = Runtime();
			return FSlateColor(R && R->bDisabled ? NVUI::Warning : NVUI::WithAlpha(NVUI::Text, 0.75f));
		}

		TWeakObjectPtr<ANVHUD> HUD;
		int32 Index = 0;
	};

	/** Magazine as a row of rounds. */
	class SNVAmmoPips : public SLeafWidget
	{
	public:
		SLATE_BEGIN_ARGS(SNVAmmoPips) {}
			SLATE_ARGUMENT(TWeakObjectPtr<ANVHUD>, HUD)
		SLATE_END_ARGS()

		void Construct(const FArguments& InArgs) { HUD = InArgs._HUD; }

		virtual FVector2D ComputeDesiredSize(float) const override
		{
			int32 Mag = 0, Cap = 0;
			Read(Mag, Cap);
			return FVector2D(FMath::Min(Cap, 40) * 5.f, 12.f);
		}

		virtual int32 OnPaint(const FPaintArgs&, const FGeometry& G, const FSlateRect&, FSlateWindowElementList& Out, int32 LayerId,
		                      const FWidgetStyle& Style, bool) const override
		{
			int32 Mag = 0, Cap = 0;
			Read(Mag, Cap);
			if (Cap <= 0)
			{
				return LayerId;
			}
			const int32 N = FMath::Min(Cap, 40);
			const int32 Lit = Cap <= 40 ? Mag : FMath::CeilToInt(static_cast<float>(Mag) / Cap * N);
			const bool bLow = Mag <= FMath::Max(1, Cap / 4);
			const FVector2f S(G.GetLocalSize());
			NVUI::FPainter P(G, Style.GetColorAndOpacityTint());
			for (int32 i = 0; i < N; ++i)
			{
				const float X = S.X - (i + 1) * 5.f + 2.f;
				const bool bOn = i < Lit;
				P.Rect(FVector2f(X, bOn ? 0.f : 6.f), FVector2f(3.f, bOn ? S.Y : S.Y - 6.f), bOn ? (bLow ? NVUI::Warning : NVUI::WithAlpha(NVUI::Text, 0.85f)) : NVUI::WithAlpha(NVUI::Accent, 0.18f));
			}
			return P.Flush(Out, LayerId);
		}

	private:
		void Read(int32& Mag, int32& Cap) const
		{
			const ANVPlayerCharacter* P = HUD.IsValid() ? HUD->GetHUDPawn() : nullptr;
			const UNVWeaponComponent* W = P ? P->GetWeapons() : nullptr;
			const UNVWeaponData* D = W ? W->GetCurrentWeapon() : nullptr;
			if (D && W->GetSlots().IsValidIndex(W->GetCurrentSlotIndex()))
			{
				Mag = W->GetSlots()[W->GetCurrentSlotIndex()].AmmoInMag;
				Cap = D->MagazineSize;
			}
		}

		TWeakObjectPtr<ANVHUD> HUD;
	};
}

// ================================================================ overlay

void SNVHUDOverlay::Construct(const FArguments& InArgs)
{
	HUD = InArgs._HUD;
	const TWeakObjectPtr<ANVHUD> WeakHUD = HUD;
	SetColorAndOpacity(TAttribute<FLinearColor>::CreateLambda([WeakHUD]()
	{
		return FLinearColor(1.f, 1.f, 1.f, WeakHUD.IsValid() ? 1.f - WeakHUD->GetFadeAlpha() : 1.f);
	}));
	SetVisibility(EVisibility::SelfHitTestInvisible);

	ChildSlot
	[
		SNew(SConstraintCanvas)
		.Visibility(EVisibility::SelfHitTestInvisible)

		// comms feed, top left
		+ SConstraintCanvas::Slot().Anchors(FAnchors(0.f, 0.f)).Offset(FMargin(44.f, 40.f, 0.f, 0.f)).AutoSize(true).Alignment(FVector2D(0.f, 0.f))
		[
			SNew(SBox).WidthOverride(470.f).Visibility_Lambda([this]() { return VisIf(!bMenuShown); })
			[
				SAssignNew(CommsBox, SVerticalBox)
			]
		]
		// objectives, top right
		+ SConstraintCanvas::Slot().Anchors(FAnchors(1.f, 0.f)).Offset(FMargin(-44.f, 40.f, 0.f, 0.f)).AutoSize(true).Alignment(FVector2D(1.f, 0.f))
		[
			SAssignNew(ObjectivesHolder, SBox).WidthOverride(410.f)
			.Visibility_Lambda([this]() { return VisIf(HudOn() && !ObjectiveSig.IsEmpty()); })
		]
		// notice banner
		+ SConstraintCanvas::Slot().Anchors(FAnchors(0.5f, 0.2f)).AutoSize(true).Alignment(FVector2D(0.5f, 0.5f))
		[
			SAssignNew(NoticeHolder, SBox).Visibility_Lambda([this]() { return VisIf(!bMenuShown); })
		]
		// title card
		+ SConstraintCanvas::Slot().Anchors(FAnchors(0.5f, 0.42f)).AutoSize(true).Alignment(FVector2D(0.5f, 0.5f))
		[
			SAssignNew(TitleHolder, SBox).Visibility_Lambda([this]() { return VisIf(!bMenuShown); })
		]
		// subtitles, bottom centre (clear of the cyberware bar)
		+ SConstraintCanvas::Slot().Anchors(FAnchors(0.5f, 1.f)).Offset(FMargin(0.f, -200.f, 0.f, 0.f)).AutoSize(true).Alignment(FVector2D(0.5f, 1.f))
		[
			SAssignNew(SubtitleHolder, SBox).MaxDesiredWidth(1150.f).Visibility_Lambda([this]() { return VisIf(!bMenuShown); })
		]
		// cyberware + vitals, bottom left
		+ SConstraintCanvas::Slot().Anchors(FAnchors(0.f, 1.f)).Offset(FMargin(44.f, -44.f, 0.f, 0.f)).AutoSize(true).Alignment(FVector2D(0.f, 1.f))
		[
			SNew(SVerticalBox)
			.Visibility_Lambda([this]() { return VisIf(HudOn()); })
			+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 0.f, 0.f, 12.f)
			[
				BuildCyberSlots()
			]
			+ SVerticalBox::Slot().AutoHeight()
			[
				BuildVitals()
			]
		]
		// weapon, bottom right
		+ SConstraintCanvas::Slot().Anchors(FAnchors(1.f, 1.f)).Offset(FMargin(-48.f, -44.f, 0.f, 0.f)).AutoSize(true).Alignment(FVector2D(1.f, 1.f))
		[
			BuildWeapon()
		]
		// interaction prompt, right of the reticle
		+ SConstraintCanvas::Slot().Anchors(FAnchors(0.5f, 0.5f)).Offset(FMargin(64.f, 16.f, 0.f, 0.f)).AutoSize(true).Alignment(FVector2D(0.f, 0.f))
		[
			BuildPrompt()
		]
		// threat text, under the reticle
		+ SConstraintCanvas::Slot().Anchors(FAnchors(0.5f, 0.5f)).Offset(FMargin(0.f, 64.f, 0.f, 0.f)).AutoSize(true).Alignment(FVector2D(0.5f, 0.f))
		[
			BuildThreat()
		]
		// opening title, full screen under the menu
		+ SConstraintCanvas::Slot().Anchors(FAnchors(0.f, 0.f, 1.f, 1.f)).Offset(FMargin(0.f)).ZOrder(5)
		[
			SAssignNew(OpeningHolder, SBox).Visibility_Lambda([this]() { return VisIf(!bMenuShown && Opening.IsValid()); })
		]
		// menu shell, full screen
		+ SConstraintCanvas::Slot().Anchors(FAnchors(0.f, 0.f, 1.f, 1.f)).Offset(FMargin(0.f)).ZOrder(10)
		[
			SAssignNew(MenuHolder, SBox)
			.Visibility_Lambda([this]() { return bMenuShown ? EVisibility::Visible : EVisibility::Collapsed; })
		]
	];
}

ANVPlayerCharacter* SNVHUDOverlay::Pawn() const
{
	return HUD.IsValid() ? HUD->GetHUDPawn() : nullptr;
}

bool SNVHUDOverlay::HudOn() const
{
	return HUD.IsValid() && HUD->IsHUDVisible() && Pawn() != nullptr;
}

void SNVHUDOverlay::Tick(const FGeometry& AllottedGeometry, const double InCurrentTime, const float InDeltaTime)
{
	SCompoundWidget::Tick(AllottedGeometry, InCurrentTime, InDeltaTime);
	ANVHUD* H = HUD.Get();
	if (!H)
	{
		return;
	}
	// Game clock: world time, so lifetimes pause with the game and match HUD timing.
	if (const UWorld* World = H->GetWorld())
	{
		Clock = World->GetTimeSeconds();
	}

	for (int32 i = Cards.Num() - 1; i >= 0; --i)
	{
		FCard& C = Cards[i];
		if (!C.Frame->IsClosing() && (Clock >= C.ExpireAt || (PendingCards.Num() > 0 && i == 0 && Cards.Num() >= 3)))
		{
			C.Frame->PlayOut();
		}
		if (C.Frame->IsGone())
		{
			CommsBox->RemoveSlot(C.Holder.ToSharedRef());
			Cards.RemoveAt(i);
		}
	}
	while (PendingCards.Num() > 0 && Cards.Num() < 3)
	{
		const FNVCommsMessage M = PendingCards[0];
		PendingCards.RemoveAt(0);
		OpenCard(M);
	}

	if (SubtitleFrame.IsValid())
	{
		if (!SubtitleFrame->IsClosing() && Clock >= SubtitleUntil)
		{
			SubtitleFrame->PlayOut();
		}
		if (SubtitleFrame->IsGone())
		{
			SubtitleHolder->SetContent(SNullWidget::NullWidget);
			SubtitleFrame.Reset();
			SubtitleText.Reset();
		}
	}
	if (NoticeUntil >= 0.f && Clock > NoticeUntil + 0.5f)
	{
		NoticeHolder->SetContent(SNullWidget::NullWidget);
		NoticeUntil = -1.f;
	}
	if (Opening.IsValid() && Opening->IsFinished())
	{
		OpeningHolder->SetContent(SNullWidget::NullWidget);
		Opening.Reset();
	}
	if (TitleUntil >= 0.f && Clock > TitleUntil + 1.1f)
	{
		TitleHolder->SetContent(SNullWidget::NullWidget);
		TitleUntil = -1.f;
	}
	RefreshObjectives();
	RefreshMenu();
}

// ---------------------------------------------------------------- comms

void SNVHUDOverlay::PushMessage(const FNVCommsMessage& Message)
{
	PendingCards.Add(Message);
}

void SNVHUDOverlay::OpenCard(const FNVCommsMessage& M)
{
	if (HUD.IsValid() && HUD->GetWorld())
	{
		Clock = HUD->GetWorld()->GetTimeSeconds();
	}
	const FLinearColor Acc = M.bPriority ? NVUI::Warning : NVUI::Accent;
	const FText Channel = M.Channel.IsEmpty() ? LOCTEXT("Direct", "DIRECT") : M.Channel.ToUpper();
	const int32 Secs = HUD.IsValid() && HUD->GetWorld() ? FMath::FloorToInt(HUD->GetWorld()->GetTimeSeconds()) : 0;
	const FText Stamp = FText::FromString(FString::Printf(TEXT("T+%02d:%02d"), Secs / 60, Secs % 60));
	const int32 Len = M.Body.ToString().Len();

	TSharedPtr<SNVFrame> Frame;
	TSharedRef<SWidget> Holder = SNew(SBox).Padding(FMargin(0.f, 0.f, 0.f, 10.f))
	[
		SAssignNew(Frame, SNVFrame).Spine(true).Accent(Acc).Cut(12.f).Padding(FMargin(16.f, 12.f, 18.f, 14.f))
		[
			SNew(SVerticalBox)
			+ SVerticalBox::Slot().AutoHeight()
			[
				SNew(SHorizontalBox)
				+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(0.f, 0.f, 10.f, 0.f)
				[
					SNew(SNVSignal).Color(Acc)
				]
				+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center)
				[
					NVUI::MakeText(FText::Format(LOCTEXT("IncomingFmt", "INCOMING // {0}"), Channel), NVUI::EFont::Mono, 11.f, FSlateColor(Acc), 120)
				]
				+ SHorizontalBox::Slot().FillWidth(1.f).HAlign(HAlign_Right).VAlign(VAlign_Center)
				[
					NVUI::MakeText(Stamp, NVUI::EFont::Mono, 11.f, FSlateColor(NVUI::TextDim), 80)
				]
			]
			+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 8.f, 0.f, 0.f)
			[
				NVUI::MakeText(M.Sender.ToUpper(), NVUI::EFont::BodyBold, 20.f, FSlateColor(NVUI::Text), 60)
			]
			+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 2.f, 0.f, 0.f)
			[
				SNew(SNVTypeText).Text(M.Body).Font(NVUI::Font(NVUI::EFont::Body, 18.f)).Color(FSlateColor(NVUI::WithAlpha(NVUI::Text, 0.92f))).CharsPerSecond(60.f).Delay(0.35f)
			]
		]
	];
	CommsBox->AddSlot().AutoHeight()[ Holder ];
	const float Life = M.Duration > 0.f ? M.Duration : FMath::Clamp(3.5f + Len / 60.f + Len / 22.f, 5.f, 16.f);
	FCard Card;
	Card.Holder = Holder;
	Card.Frame = Frame;
	Card.ExpireAt = Clock + Life;
	Cards.Add(Card);
}

// ---------------------------------------------------------------- notices / subtitles / title

void SNVHUDOverlay::ShowNotice(const FText& InText, float Duration, bool bWarning)
{
	if (HUD.IsValid() && HUD->GetWorld())
	{
		Clock = HUD->GetWorld()->GetTimeSeconds();
	}
	const float From = Clock;
	NoticeUntil = Clock + Duration;
	const float Until = NoticeUntil;
	NoticeHolder->SetContent(
		SNew(SNVNoticeBanner).Text(InText).Color(bWarning ? NVUI::Warning : NVUI::Accent)
		.Fade_Lambda([this, From, Until]() { return FMath::Clamp((Clock - From) / 0.15f, 0.f, 1.f) * FMath::Clamp((Until - Clock) / 0.45f, 0.f, 1.f); }));
}

void SNVHUDOverlay::ShowSubtitle(const FText& Speaker, const FText& Line, float Duration)
{
	if (HUD.IsValid() && HUD->GetWorld())
	{
		Clock = HUD->GetWorld()->GetTimeSeconds();
	}
	SubtitleSpeaker = Speaker;
	SubtitleUntil = Clock + Duration;
	if (SubtitleFrame.IsValid() && !SubtitleFrame->IsClosing() && SubtitleText.IsValid())
	{
		SubtitleText->SetText(Line);
		return;
	}
	const float Scale = HUD.IsValid() ? HUD->SubtitleScale : 1.f;
	SubtitleHolder->SetContent(
		SAssignNew(SubtitleFrame, SNVFrame).Cut(10.f).FillAlpha(0.9f).Trims(false).Padding(FMargin(20.f, 12.f, 26.f, 13.f))
		[
			SNew(SHorizontalBox)
			+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Top).Padding(0.f, 4.f, 16.f, 0.f)
			[
				SNew(SBox)
				.Visibility_Lambda([this]() { return SubtitleSpeaker.IsEmpty() ? EVisibility::Collapsed : EVisibility::HitTestInvisible; })
				[
					NVUI::MakeText(TAttribute<FText>::CreateLambda([this]() { return SubtitleSpeaker.ToUpper(); }), NVUI::EFont::Mono, 13.f * Scale, FSlateColor(NVUI::Accent), 160)
				]
			]
			+ SHorizontalBox::Slot().FillWidth(1.f).VAlign(VAlign_Center)
			[
				SAssignNew(SubtitleText, SNVTypeText).Text(Line).Font(NVUI::Font(NVUI::EFont::Body, 21.f * Scale)).CharsPerSecond(150.f).ShowCursor(false)
				.WrapAt(960.f)
			]
		]);
}

void SNVHUDOverlay::ShowTitleCard(const FText& Title, const FText& Subtitle, float Duration)
{
	if (HUD.IsValid() && HUD->GetWorld())
	{
		Clock = HUD->GetWorld()->GetTimeSeconds();
	}
	const float From = Clock;
	TitleUntil = Clock + Duration;
	const float Until = TitleUntil;
	TitleHolder->SetContent(
		SNew(SNVTitleCard).Title(Title).Subtitle(Subtitle)
		.Fade_Lambda([this, From, Until]() { return FMath::Clamp((Clock - From) / 0.4f, 0.f, 1.f) * FMath::Clamp((Until - Clock) / 1.f, 0.f, 1.f); }));
}

void SNVHUDOverlay::ShowOpeningTitle(const FText& Title, const FText& Subtitle, const FText& Tagline, float Duration)
{
	OpeningHolder->SetContent(SAssignNew(Opening, SNVOpeningTitle).Title(Title).Subtitle(Subtitle).Tagline(Tagline).Duration(Duration));
}

// ---------------------------------------------------------------- objectives

void SNVHUDOverlay::RefreshObjectives()
{
	const UNVObjectiveSubsystem* Obj = HUD.IsValid() ? UNVObjectiveSubsystem::Get(HUD.Get()) : nullptr;
	FString Sig;
	TArray<FNVObjectiveDef> Active;
	if (Obj && Obj->GetCurrentMission())
	{
		Active = Obj->GetActiveObjectives();
		Sig = Obj->GetCurrentMission()->MissionTitle.ToString();
		for (const FNVObjectiveDef& D : Active)
		{
			Sig += TEXT("|") + D.ObjectiveID.ToString() + D.DisplayText.ToString() + (D.bOptional ? TEXT("?") : TEXT(""));
		}
	}
	if (Sig == ObjectiveSig)
	{
		return;
	}
	ObjectiveSig = Sig;
	if (Sig.IsEmpty())
	{
		ObjectivesHolder->SetContent(SNullWidget::NullWidget);
		return;
	}
	TSharedRef<SVerticalBox> Rows = SNew(SVerticalBox);
	for (const FNVObjectiveDef& D : Active)
	{
		Rows->AddSlot().AutoHeight().Padding(0.f, 2.f, 0.f, 4.f)
		[
			SNew(SHorizontalBox)
			+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Top).Padding(0.f, 5.f, 10.f, 0.f)
			[
				SNew(SNVMark).Color(D.bOptional ? NVUI::TextDim : NVUI::Accent)
			]
			+ SHorizontalBox::Slot().FillWidth(1.f)
			[
				SNew(SVerticalBox)
				+ SVerticalBox::Slot().AutoHeight()
				[
					SNew(SNVTypeText).Text(D.DisplayText).Font(NVUI::Font(NVUI::EFont::BodySemi, 18.f)).Color(FSlateColor(D.bOptional ? NVUI::TextDim : NVUI::Text)).CharsPerSecond(90.f).Delay(0.3f).ShowCursor(false)
				]
				+ SVerticalBox::Slot().AutoHeight()
				[
					SNew(SBox).Visibility(D.bOptional ? EVisibility::HitTestInvisible : EVisibility::Collapsed)
					[
						NVUI::MakeText(LOCTEXT("Optional", "OPTIONAL"), NVUI::EFont::Mono, 10.f, FSlateColor(NVUI::TextDim), 140)
					]
				]
			]
		];
	}
	const TWeakObjectPtr<ANVHUD> WeakHUD = HUD;
	Rows->AddSlot().AutoHeight().Padding(0.f, 8.f, 0.f, 0.f)
	[
		SNew(SBox)
		.Visibility_Lambda([WeakHUD]() { return WeakHUD.IsValid() && !WeakHUD->GetInstructionDisplay().IsEmpty() ? EVisibility::HitTestInvisible : EVisibility::Collapsed; })
		[
			SNew(SHorizontalBox)
			+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Top).Padding(0.f, 1.f, 10.f, 0.f)
			[
				NVUI::MakeText(FText::FromString(TEXT(">")), NVUI::EFont::Mono, 15.f, FSlateColor(NVUI::Accent))
			]
			+ SHorizontalBox::Slot().FillWidth(1.f)
			[
				NVUI::MakeText(TAttribute<FText>::CreateLambda([WeakHUD]() { return WeakHUD.IsValid() ? WeakHUD->GetInstructionDisplay() : FText::GetEmpty(); }),
					NVUI::EFont::BodySemi, 17.f, FSlateColor(NVUI::Accent), 0, true)
			]
		]
	];
	ObjectivesHolder->SetContent(
		SNew(SNVFrame).Header(Obj->GetCurrentMission()->MissionTitle).Padding(FMargin(18.f, 12.f, 18.f, 14.f)).FillAlpha(0.82f)
		[
			Rows
		]);
}

// ---------------------------------------------------------------- menu

void SNVHUDOverlay::RefreshMenu()
{
	ANVHUD* H = HUD.Get();
	ANVPlayerController* PC = H ? Cast<ANVPlayerController>(H->GetOwningPlayerController()) : nullptr;
	const bool bOpen = PC && PC->IsPauseMenuOpen();
	if (bOpen == bMenuShown)
	{
		return;
	}
	bMenuShown = bOpen;
	if (bOpen)
	{
		FNVMenuContext Ctx;
		Ctx.HUD = H;
		Ctx.PC = PC;
		MenuHolder->SetContent(SNew(SNVMenuShell).Context(Ctx));
	}
	else
	{
		MenuHolder->SetContent(SNullWidget::NullWidget);
	}
}

// ---------------------------------------------------------------- vitals / cyberware / weapon / prompt / threat

TSharedRef<SWidget> SNVHUDOverlay::BuildVitals()
{
	auto Health = [this]() { const ANVPlayerCharacter* P = Pawn(); return P ? P->GetHealth()->GetHealthPercent() : 1.f; };
	auto HealthColor = [Health]()
	{
		const float V = Health();
		if (V < 0.15f)
		{
			return FMath::Frac(NVUI::Now() * 2.0) < 0.5 ? NVUI::Danger : NVUI::WithAlpha(NVUI::Danger, 0.55f);
		}
		return V < 0.3f ? NVUI::Warning : NVUI::Accent;
	};
	auto Shield = [this]()
	{
		const ANVPlayerCharacter* P = Pawn();
		const UNVHealthComponent* H = P ? P->GetHealth() : nullptr;
		return H && H->MaxShield > 0.f ? H->GetShield() / H->MaxShield : 0.f;
	};
	auto HasShield = [this]()
	{
		const ANVPlayerCharacter* P = Pawn();
		return P && P->GetHealth()->MaxShield > 0.f;
	};

	return SNew(SNVFrame).AnimateIn(false).Cut(12.f).Padding(FMargin(16.f, 10.f, 20.f, 12.f)).FillAlpha(0.75f).Accent_Lambda(HealthColor)
		[
			SNew(SHorizontalBox)
			+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(0.f, 0.f, 16.f, 0.f)
			[
				SNew(SBox).MinDesiredWidth(64.f).HAlign(HAlign_Right)
				[
					NVUI::MakeText(TAttribute<FText>::CreateLambda([this]()
					{
						const ANVPlayerCharacter* P = Pawn();
						return FText::AsNumber(P ? FMath::CeilToInt(P->GetHealth()->GetHealth()) : 0);
					}), NVUI::EFont::BodyBold, 40.f, FSlateColor(NVUI::Text))
				]
			]
			+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center)
			[
				SNew(SVerticalBox)
				+ SVerticalBox::Slot().AutoHeight()
				[
					SNew(SHorizontalBox)
					+ SHorizontalBox::Slot().AutoWidth()
					[
						NVUI::MakeText(LOCTEXT("Integrity", "INTEGRITY"), NVUI::EFont::Mono, 11.f, FSlateColor(NVUI::TextDim), 140)
					]
					+ SHorizontalBox::Slot().FillWidth(1.f).HAlign(HAlign_Right)
					[
						NVUI::MakeText(TAttribute<FText>::CreateLambda([Health]()
						{
							const float V = Health();
							return V < 0.15f ? LOCTEXT("Critical", "CRITICAL") : (V < 0.3f ? LOCTEXT("Compromised", "COMPROMISED") : LOCTEXT("Nominal", "NOMINAL"));
						}), NVUI::EFont::Mono, 11.f, TAttribute<FSlateColor>::CreateLambda([HealthColor]() { return FSlateColor(HealthColor()); }), 140)
					]
				]
				+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 6.f, 0.f, 0.f)
				[
					SNew(SNVMeter).Value_Lambda(Health).Color_Lambda(HealthColor).Segments(22).Width(250.f).Height(9.f)
				]
				+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 4.f, 0.f, 0.f)
				[
					SNew(SBox).Visibility_Lambda([HasShield]() { return HasShield() ? EVisibility::HitTestInvisible : EVisibility::Collapsed; })
					[
						SNew(SNVMeter).Value_Lambda(Shield).Color(FLinearColor(0.75f, 0.85f, 1.f, 0.9f)).Segments(44).Width(250.f).Height(3.f).Trail(false)
					]
				]
			]
		];
}

TSharedRef<SWidget> SNVHUDOverlay::BuildCyberSlots()
{
	TSharedRef<SHorizontalBox> Row = SNew(SHorizontalBox);
	for (int32 i = 0; i < 3; ++i)
	{
		TSharedPtr<SNVCyberSlot> CSlot;
		Row->AddSlot().AutoWidth().Padding(0.f, 0.f, 12.f, 0.f)
		[
			SAssignNew(CSlot, SNVCyberSlot).HUD(HUD).Index(i)
		];
		TWeakPtr<SNVCyberSlot> WeakSlot = CSlot;
		CSlot->SetVisibility(TAttribute<EVisibility>::CreateLambda([WeakSlot]()
		{
			const TSharedPtr<SNVCyberSlot> S = WeakSlot.Pin();
			return S.IsValid() && S->HasAbility() ? EVisibility::HitTestInvisible : EVisibility::Collapsed;
		}));
	}
	return Row;
}

TSharedRef<SWidget> SNVHUDOverlay::BuildWeapon()
{
	auto Weapons = [this]() -> const UNVWeaponComponent* { const ANVPlayerCharacter* P = Pawn(); return P ? P->GetWeapons() : nullptr; };
	auto Armed = [Weapons]() { const UNVWeaponComponent* W = Weapons(); return W && W->GetCurrentWeapon() != nullptr; };
	auto Ranged = [Weapons]() { const UNVWeaponComponent* W = Weapons(); return W && W->GetCurrentWeapon() && !W->GetCurrentWeapon()->bMelee; };
	auto SlotData = [Weapons]() -> const FNVWeaponSlot*
	{
		const UNVWeaponComponent* W = Weapons();
		return W && W->GetSlots().IsValidIndex(W->GetCurrentSlotIndex()) ? &W->GetSlots()[W->GetCurrentSlotIndex()] : nullptr;
	};
	auto Low = [Weapons, SlotData]()
	{
		const UNVWeaponComponent* W = Weapons();
		const FNVWeaponSlot* S = SlotData();
		return W && S && W->GetCurrentWeapon() && S->AmmoInMag <= FMath::Max(1, W->GetCurrentWeapon()->MagazineSize / 4);
	};
	const TWeakObjectPtr<ANVHUD> WeakHUD = HUD;

	return SNew(SBox).Visibility_Lambda([this]() { return VisIf(HudOn()); })
		[
			SNew(SVerticalBox)
			+ SVerticalBox::Slot().AutoHeight().HAlign(HAlign_Right)
			[
				SNew(SBox).Visibility_Lambda([Armed]() { return Armed() ? EVisibility::HitTestInvisible : EVisibility::Collapsed; })
				[
					SNew(SVerticalBox)
					+ SVerticalBox::Slot().AutoHeight().HAlign(HAlign_Right)
					[
						SNew(SHorizontalBox).Visibility_Lambda([Ranged]() { return Ranged() ? EVisibility::HitTestInvisible : EVisibility::Collapsed; })
						+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Bottom)
						[
							NVUI::MakeText(TAttribute<FText>::CreateLambda([SlotData]() { const FNVWeaponSlot* S = SlotData(); return FText::AsNumber(S ? S->AmmoInMag : 0); }),
								NVUI::EFont::BodyBold, 48.f, TAttribute<FSlateColor>::CreateLambda([Low]() { return FSlateColor(Low() ? NVUI::Warning : NVUI::Text); }))
						]
						+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Bottom).Padding(10.f, 0.f, 0.f, 10.f)
						[
							NVUI::MakeText(TAttribute<FText>::CreateLambda([SlotData]()
							{
								const FNVWeaponSlot* S = SlotData();
								return FText::FromString(FString::Printf(TEXT("/ %03d"), S ? S->ReserveAmmo : 0));
							}), NVUI::EFont::Mono, 18.f, FSlateColor(NVUI::TextDim), 60)
						]
					]
					+ SVerticalBox::Slot().AutoHeight().HAlign(HAlign_Right).Padding(0.f, 0.f, 0.f, 6.f)
					[
						SNew(SNVAmmoPips).HUD(WeakHUD).Visibility_Lambda([Ranged]() { return Ranged() ? EVisibility::HitTestInvisible : EVisibility::Collapsed; })
					]
					+ SVerticalBox::Slot().AutoHeight().HAlign(HAlign_Right)
					[
						SNew(SHorizontalBox)
						+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(0.f, 0.f, 10.f, 0.f)
						[
							SNew(SBox).WidthOverride(56.f)
							[
								SNew(SNVRule)
							]
						]
						+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center)
						[
							NVUI::MakeText(TAttribute<FText>::CreateLambda([Weapons]()
							{
								const UNVWeaponComponent* W = Weapons();
								if (!W || !W->GetCurrentWeapon())
								{
									return FText::GetEmpty();
								}
								return W->IsReloading() ? LOCTEXT("Reloading", "RELOADING") : W->GetCurrentWeapon()->DisplayName.ToUpper();
							}), NVUI::EFont::Mono, 13.f, TAttribute<FSlateColor>::CreateLambda([Weapons]()
							{
								const UNVWeaponComponent* W = Weapons();
								return FSlateColor(W && W->IsReloading() ? NVUI::Warning : NVUI::Accent);
							}), 200)
						]
					]
				]
			]
			+ SVerticalBox::Slot().AutoHeight().HAlign(HAlign_Right)
			[
				SNew(SBox).Visibility_Lambda([Armed]() { return Armed() ? EVisibility::Collapsed : EVisibility::HitTestInvisible; })
				[
					SNew(SHorizontalBox)
					+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(0.f, 0.f, 12.f, 0.f)
					[
						NVUI::MakeText(LOCTEXT("Unarmed", "UNARMED"), NVUI::EFont::Mono, 13.f, FSlateColor(NVUI::TextDim), 220)
					]
					+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(0.f, 0.f, 8.f, 0.f)
					[
						SNew(SNVKeyCap).Key_Lambda([WeakHUD]() { return WeakHUD.IsValid() ? WeakHUD->KeyCap(TEXT("Holster")) : FText::GetEmpty(); }).Size(11.f)
					]
					+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center)
					[
						NVUI::MakeText(LOCTEXT("Draw", "DRAW"), NVUI::EFont::Mono, 11.f, FSlateColor(NVUI::TextDim), 160)
					]
				]
			]
		];
}

TSharedRef<SWidget> SNVHUDOverlay::BuildPrompt()
{
	auto Focus = [this]() -> AActor*
	{
		ANVPlayerCharacter* P = Pawn();
		AActor* F = P && P->GetInteraction() ? P->GetInteraction()->GetFocusedActor() : nullptr;
		return F && F->Implements<UNVInteractable>() ? F : nullptr;
	};
	auto Hold = [Focus]() { AActor* F = Focus(); return F ? INVInteractable::Execute_GetHoldDuration(F) : 0.f; };
	const TWeakObjectPtr<ANVHUD> WeakHUD = HUD;

	return SNew(SBox).Visibility_Lambda([this, Focus]() { return VisIf(HudOn() && Focus() != nullptr); })
		[
			SNew(SHorizontalBox)
			+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Top).Padding(0.f, 1.f, 12.f, 0.f)
			[
				SNew(SNVKeyCap).Key_Lambda([WeakHUD]() { return WeakHUD.IsValid() ? WeakHUD->KeyCap(TEXT("Interact")) : FText::GetEmpty(); }).Size(14.f)
			]
			+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Top)
			[
				SNew(SVerticalBox)
				+ SVerticalBox::Slot().AutoHeight()
				[
					NVUI::MakeText(TAttribute<FText>::CreateLambda([this, Focus, Hold]()
					{
						AActor* F = Focus();
						if (!F)
						{
							return FText::GetEmpty();
						}
						const FText P = INVInteractable::Execute_GetInteractionPrompt(F, Pawn());
						return Hold() > 0.f ? FText::Format(LOCTEXT("HoldFmt", "HOLD  {0}"), P.ToUpper()) : P.ToUpper();
					}), NVUI::EFont::BodySemi, 20.f, FSlateColor(NVUI::Text), 60)
				]
				+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 5.f, 0.f, 0.f)
				[
					SNew(SBox).Visibility_Lambda([Hold]() { return Hold() > 0.f ? EVisibility::HitTestInvisible : EVisibility::Collapsed; })
					[
						SNew(SNVMeter).Value_Lambda([this]()
						{
							const ANVPlayerCharacter* P = Pawn();
							return P && P->GetInteraction() ? P->GetInteraction()->GetHoldProgress() : 0.f;
						}).Segments(16).Width(180.f).Height(4.f).Trail(false)
					]
				]
			]
		];
}

TSharedRef<SWidget> SNVHUDOverlay::BuildThreat()
{
	const TWeakObjectPtr<ANVHUD> WeakHUD = HUD;
	auto Threat = [WeakHUD]()
	{
		FText T;
		return WeakHUD.IsValid() && WeakHUD->GetThreat(T) ? T : FText::GetEmpty();
	};
	auto Blink = []() { return FSlateColor(FMath::Frac(NVUI::Now() * 4.0) < 0.65 ? NVUI::Warning : NVUI::WithAlpha(NVUI::Warning, 0.45f)); };
	return SNew(SBox).Visibility_Lambda([this, Threat]() { return VisIf(HudOn() && !Threat().IsEmpty()); })
		[
			SNew(SHorizontalBox)
			+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(0.f, 0.f, 10.f, 0.f)
			[
				SNew(SNVMark).Color(NVUI::Warning).Radius(4.f)
			]
			+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center)
			[
				NVUI::MakeText(TAttribute<FText>::CreateLambda([Threat]() { return Threat().ToUpper(); }), NVUI::EFont::Mono, 14.f, TAttribute<FSlateColor>::CreateLambda(Blink), 260)
			]
			+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(10.f, 0.f, 0.f, 0.f)
			[
				SNew(SNVMark).Color(NVUI::Warning).Radius(4.f)
			]
		];
}

#undef LOCTEXT_NAMESPACE
