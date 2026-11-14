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
		SLATE_END_ARGS()

		void Construct(const FArguments&) { Start = NVUI::Now(); }
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

			auto Poly = [&](std::initializer_list<FVector2f> Pts, const FLinearColor& C, float Th)
			{
				NVUI::Lines(Out, LayerId + 1, G, TArray<FVector2f>(Pts), C, Th);
			};
			// head (octagon), neck, torso, pelvis
			Poly({ Pt(-14, 0), Pt(14, 0), Pt(24, 14), Pt(24, 44), Pt(12, 62), Pt(-12, 62), Pt(-24, 44), Pt(-24, 14), Pt(-14, 0) }, Wire, 1.5f);
			Poly({ Pt(-10, 62), Pt(-10, 76), Pt(10, 76), Pt(10, 62) }, Wire, 1.2f);
			Poly({ Pt(-62, 86), Pt(62, 86), Pt(48, 200), Pt(30, 236), Pt(-30, 236), Pt(-48, 200), Pt(-62, 86) }, Wire, 1.5f);
			Poly({ Pt(-30, 236), Pt(-36, 262), Pt(36, 262), Pt(30, 236) }, Wire, 1.2f);
			Poly({ Pt(0, 92), Pt(0, 232) }, WireDim, 1.f);
			Poly({ Pt(-40, 120), Pt(40, 120) }, WireDim, 1.f);
			Poly({ Pt(-36, 160), Pt(36, 160) }, WireDim, 1.f);
			// arms
			Poly({ Pt(-62, 86), Pt(-84, 96), Pt(-98, 178), Pt(-110, 250), Pt(-104, 276) }, Wire, 1.5f);
			Poly({ Pt(62, 86), Pt(84, 96), Pt(98, 178), Pt(110, 250), Pt(104, 276) }, Wire, 1.5f);
			// legs
			Poly({ Pt(-34, 262), Pt(-46, 370), Pt(-44, 470), Pt(-60, 486) }, Wire, 1.5f);
			Poly({ Pt(-8, 262), Pt(-16, 370), Pt(-22, 470), Pt(-30, 486) }, WireDim, 1.f);
			Poly({ Pt(34, 262), Pt(46, 370), Pt(44, 470), Pt(60, 486) }, Wire, 1.5f);
			Poly({ Pt(8, 262), Pt(16, 370), Pt(22, 470), Pt(30, 486) }, WireDim, 1.f);

			// callouts: slot marker on the body, leader line, label at the side
			struct FCallout { const TCHAR* Name; float X, Y; bool bLeft; };
			static const FCallout Calls[] = {
				{ TEXT("NEURAL"), 0.f, 24.f, true },
				{ TEXT("OCULAR"), 10.f, 30.f, false },
				{ TEXT("DERMAL"), -30.f, 140.f, true },
				{ TEXT("SKELETAL"), 0.f, 200.f, false },
				{ TEXT("ARMS"), -104.f, 220.f, true },
				{ TEXT("LEGS"), 45.f, 400.f, false },
			};
			const FSlateFontInfo LabelFont = NVUI::Font(NVUI::EFont::Mono, 11.f, 120);
			const FSlateFontInfo SubFont = NVUI::Font(NVUI::EFont::Mono, 9.f, 60);
			NVUI::FPainter M(G, Tint);
			const float Pulse = 0.6f + 0.4f * FMath::Sin(static_cast<float>(NVUI::Now()) * 3.f);
			for (const FCallout& C : Calls)
			{
				const FVector2f A = Pt(C.X, C.Y);
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
