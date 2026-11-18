#include "UI/NVOptionsPage.h"
#include "UI/NVUIWidgets.h"
#include "UI/NVUIStyle.h"
#include "UI/NVHUD.h"
#include "Core/NVOptions.h"
#include "Core/NVPlayerController.h"

#include "Engine/World.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Text/STextBlock.h"

#define LOCTEXT_NAMESPACE "NeonVeilOptions"

namespace
{
	/** "<" or ">" stepper: mono glyph, accent on hover, hand cursor. */
	class SNVStep : public SCompoundWidget
	{
	public:
		SLATE_BEGIN_ARGS(SNVStep) {}
			SLATE_ARGUMENT(FText, Glyph)
			SLATE_EVENT(FSimpleDelegate, OnClicked)
		SLATE_END_ARGS()

		void Construct(const FArguments& InArgs)
		{
			OnClicked = InArgs._OnClicked;
			ChildSlot.Padding(FMargin(8.f, 2.f))
			[
				NVUI::MakeText(InArgs._Glyph, NVUI::EFont::Mono, 17.f,
					TAttribute<FSlateColor>::CreateLambda([this]() { return FSlateColor(IsHovered() ? NVUI::Accent : NVUI::TextDim); }))
			];
		}
		virtual FReply OnMouseButtonDown(const FGeometry&, const FPointerEvent& E) override
		{
			if (E.GetEffectingButton() == EKeys::LeftMouseButton)
			{
				OnClicked.ExecuteIfBound();
				return FReply::Handled();
			}
			return FReply::Unhandled();
		}
		virtual FCursorReply OnCursorQuery(const FGeometry&, const FPointerEvent&) const override
		{
			return FCursorReply::Cursor(EMouseCursor::Hand);
		}

	private:
		FSimpleDelegate OnClicked;
	};

	using FGetText = TFunction<FText()>;
	using FGetFloat = TFunction<float()>;
	using FStep = TFunction<void(int32)>;

	/** Label on the left; "<  value  >" (and an optional meter) on the right. Dir is -1 or +1. */
	TSharedRef<SWidget> Row(const FText& Label, FGetText Value, FStep Step, FGetFloat Meter = nullptr)
	{
		TSharedRef<SHorizontalBox> Right = SNew(SHorizontalBox)
			+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center)
			[
				SNew(SNVStep).Glyph(FText::FromString(TEXT("<"))).OnClicked_Lambda([Step]() { Step(-1); })
			]
			+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center)
			[
				SNew(SBox).WidthOverride(150.f).HAlign(HAlign_Center)
				[
					NVUI::MakeText(TAttribute<FText>::CreateLambda([Value]() { return Value(); }), NVUI::EFont::BodySemi, 17.f, FSlateColor(NVUI::Text), 60)
				]
			]
			+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center)
			[
				SNew(SNVStep).Glyph(FText::FromString(TEXT(">"))).OnClicked_Lambda([Step]() { Step(1); })
			];
		TSharedRef<SVerticalBox> RightCol = SNew(SVerticalBox)
			+ SVerticalBox::Slot().AutoHeight().HAlign(HAlign_Right)
			[
				Right
			];
		if (Meter)
		{
			RightCol->AddSlot().AutoHeight().HAlign(HAlign_Right).Padding(0.f, 2.f, 30.f, 0.f)
			[
				SNew(SNVMeter).Value_Lambda([Meter]() { return Meter(); }).Segments(20).Width(160.f).Height(4.f).Trail(false)
			];
		}
		return SNew(SBox).HeightOverride(Meter ? 46.f : 36.f)
			[
				SNew(SHorizontalBox)
				+ SHorizontalBox::Slot().FillWidth(1.f).VAlign(VAlign_Center)
				[
					NVUI::MakeText(Label.ToUpper(), NVUI::EFont::Mono, 13.f, FSlateColor(NVUI::TextDim), 120)
				]
				+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center)
				[
					RightCol
				]
			];
	}

	FText OnOff(bool b) { return b ? LOCTEXT("On", "ON") : LOCTEXT("Off", "OFF"); }
	FText Percent(float V) { return FText::AsPercent(V); }
	FText Number(float V, int32 Frac = 1)
	{
		FNumberFormattingOptions O;
		O.MinimumFractionalDigits = Frac;
		O.MaximumFractionalDigits = Frac;
		return FText::AsNumber(V, &O);
	}

	TSharedRef<SWidget> Column(const FText& Header, const TArray<TSharedRef<SWidget>>& Rows, float Width = 430.f)
	{
		TSharedRef<SVerticalBox> Box = SNew(SVerticalBox)
			+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 0.f, 0.f, 12.f)
			[
				NVUI::MakeHeader(Header)
			];
		for (const TSharedRef<SWidget>& R : Rows)
		{
			Box->AddSlot().AutoHeight().Padding(0.f, 0.f, 0.f, 4.f)[R];
		}
		return SNew(SBox).WidthOverride(Width)[Box];
	}
}

TSharedRef<SWidget> NVUI::BuildOptionsPage(const FNVMenuContext& Ctx)
{
	const TWeakObjectPtr<ANVPlayerController> PC = Ctx.PC;
	// every change: clamp, save, push into the running game
	auto Commit = [PC]()
	{
		FNVOptions& O = FNVOptions::Get();
		O.Save();
		if (PC.IsValid())
		{
			O.Apply(PC->GetWorld());
		}
	};
	auto StepF = [Commit](float FNVOptions::* Field, float Step, float Min, float Max)
	{
		return [Commit, Field, Step, Min, Max](int32 Dir)
		{
			FNVOptions& O = FNVOptions::Get();
			O.*Field = FMath::Clamp(FMath::RoundToFloat((O.*Field + Dir * Step) / Step) * Step, Min, Max);
			Commit();
		};
	};
	auto Toggle = [Commit](bool FNVOptions::* Field)
	{
		return [Commit, Field](int32)
		{
			FNVOptions& O = FNVOptions::Get();
			O.*Field = !(O.*Field);
			Commit();
		};
	};
	auto Bool = [](bool FNVOptions::* Field) { return [Field]() { return OnOff(FNVOptions::Get().*Field); }; };
	auto Vol = [](float FNVOptions::* Field) { return [Field]() { return Percent(FNVOptions::Get().*Field); }; };
	auto VolMeter = [](float FNVOptions::* Field) { return [Field]() { return FNVOptions::Get().*Field; }; };

	// ---------------- controls + gameplay
	TArray<TSharedRef<SWidget>> Controls = {
		Row(LOCTEXT("Sens", "Look sensitivity"), []() { return Number(FNVOptions::Get().LookSensitivity); },
			StepF(&FNVOptions::LookSensitivity, 0.1f, 0.2f, 3.f), []() { return (FNVOptions::Get().LookSensitivity - 0.2f) / 2.8f; }),
		Row(LOCTEXT("Invert", "Invert look"), Bool(&FNVOptions::bInvertY), Toggle(&FNVOptions::bInvertY)),
		Row(LOCTEXT("Fov", "Field of view"), []() { return Number(FNVOptions::Get().FieldOfView, 0); },
			StepF(&FNVOptions::FieldOfView, 1.f, 80.f, 110.f), []() { return (FNVOptions::Get().FieldOfView - 80.f) / 30.f; }),
		Row(LOCTEXT("TSprint", "Toggle sprint"), Bool(&FNVOptions::bToggleSprint), Toggle(&FNVOptions::bToggleSprint)),
		Row(LOCTEXT("TCrouch", "Toggle crouch"), Bool(&FNVOptions::bToggleCrouch), Toggle(&FNVOptions::bToggleCrouch)),
		Row(LOCTEXT("TAim", "Toggle aim"), Bool(&FNVOptions::bToggleAim), Toggle(&FNVOptions::bToggleAim)),
	};
	TArray<TSharedRef<SWidget>> Gameplay = {
		Row(LOCTEXT("Subs", "Subtitles"), Bool(&FNVOptions::bSubtitles), Toggle(&FNVOptions::bSubtitles)),
		Row(LOCTEXT("TextSize", "Text size"), []() { return Percent(FNVOptions::Get().TextScale); },
			StepF(&FNVOptions::TextScale, 0.1f, 0.8f, 1.4f)),
		Row(LOCTEXT("Blur", "Motion blur"), Bool(&FNVOptions::bMotionBlur), Toggle(&FNVOptions::bMotionBlur)),
	};

	// ---------------- audio
	TArray<TSharedRef<SWidget>> AudioRows = {
		Row(LOCTEXT("Master", "Master volume"), Vol(&FNVOptions::MasterVolume), StepF(&FNVOptions::MasterVolume, 0.05f, 0.f, 1.f), VolMeter(&FNVOptions::MasterVolume)),
		Row(LOCTEXT("Music", "Music"), Vol(&FNVOptions::MusicVolume), StepF(&FNVOptions::MusicVolume, 0.05f, 0.f, 1.f), VolMeter(&FNVOptions::MusicVolume)),
		Row(LOCTEXT("Voice", "Dialogue"), Vol(&FNVOptions::VoiceVolume), StepF(&FNVOptions::VoiceVolume, 0.05f, 0.f, 1.f), VolMeter(&FNVOptions::VoiceVolume)),
		Row(LOCTEXT("Fx", "Effects"), Vol(&FNVOptions::EffectsVolume), StepF(&FNVOptions::EffectsVolume, 0.05f, 0.f, 1.f), VolMeter(&FNVOptions::EffectsVolume)),
	};

	// ---------------- display (UGameUserSettings)
	static const FText Qualities[] = { LOCTEXT("QLow", "LOW"), LOCTEXT("QMed", "MEDIUM"), LOCTEXT("QHigh", "HIGH"), LOCTEXT("QEpic", "EPIC") };
	static const FText Modes[] = { LOCTEXT("MFull", "FULLSCREEN"), LOCTEXT("MBorder", "BORDERLESS"), LOCTEXT("MWin", "WINDOWED") };
	static const float Limits[] = { 30.f, 60.f, 90.f, 120.f, 144.f, 0.f };
	TArray<TSharedRef<SWidget>> DisplayRows = {
		Row(LOCTEXT("Quality", "Graphics quality"),
			[]() { const int32 Q = NVDisplay::GetQuality(); return Q >= 0 && Q <= 3 ? Qualities[Q] : LOCTEXT("QCustom", "CUSTOM"); },
			[](int32 Dir) { NVDisplay::SetQuality(FMath::Clamp(FMath::Max(0, NVDisplay::GetQuality()) + Dir, 0, 3)); }),
		Row(LOCTEXT("Window", "Window mode"), []() { return Modes[FMath::Clamp(NVDisplay::GetWindowMode(), 0, 2)]; },
			[](int32 Dir) { NVDisplay::SetWindowMode((NVDisplay::GetWindowMode() + Dir + 3) % 3); }),
		Row(LOCTEXT("Res", "Resolution"),
			[]() { const FIntPoint R = NVDisplay::GetResolution(); return FText::FromString(FString::Printf(TEXT("%d x %d"), R.X, R.Y)); },
			[](int32 Dir)
			{
				const TArray<FIntPoint> All = NVDisplay::GetResolutions();
				int32 I = All.IndexOfByKey(NVDisplay::GetResolution());
				I = I == INDEX_NONE ? All.Num() - 1 : FMath::Clamp(I + Dir, 0, All.Num() - 1);
				NVDisplay::SetResolution(All[I]);
			}),
		Row(LOCTEXT("ResScale", "Render scale"), []() { return Percent(NVDisplay::GetResolutionScalePercent() / 100.f); },
			[](int32 Dir) { NVDisplay::SetResolutionScale(FMath::RoundToFloat((NVDisplay::GetResolutionScale() + Dir * 0.1f) * 10.f) / 10.f); },
			[]() { return NVDisplay::GetResolutionScale(); }),
		Row(LOCTEXT("VSync", "V-sync"), []() { return OnOff(NVDisplay::GetVSync()); }, [](int32) { NVDisplay::SetVSync(!NVDisplay::GetVSync()); }),
		Row(LOCTEXT("Fps", "Frame limit"),
			[]() { const float L = NVDisplay::GetFrameLimit(); return L <= 0.f ? LOCTEXT("Unlimited", "UNLIMITED") : FText::AsNumber(FMath::RoundToInt(L)); },
			[](int32 Dir)
			{
				const float Cur = NVDisplay::GetFrameLimit();
				int32 I = 5;
				for (int32 k = 0; k < 6; ++k)
				{
					if (FMath::IsNearlyEqual(Limits[k], Cur, 0.5f))
					{
						I = k;
					}
				}
				NVDisplay::SetFrameLimit(Limits[FMath::Clamp(I + Dir, 0, 5)]);
			}),
	};

	TArray<TSharedRef<SWidget>> LeftRows = Controls;
	LeftRows.Add(SNew(SBox).HeightOverride(18.f));
	LeftRows.Add(NVUI::MakeHeader(LOCTEXT("GameplayHdr", "Gameplay")));
	LeftRows.Add(SNew(SBox).HeightOverride(8.f));
	LeftRows.Append(Gameplay);

	return SNew(SVerticalBox)
		+ SVerticalBox::Slot().AutoHeight()
		[
			SNew(SHorizontalBox)
			+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Top).Padding(0.f, 0.f, 56.f, 0.f)
			[
				Column(LOCTEXT("ControlsHdr", "Controls"), LeftRows)
			]
			+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Top).Padding(0.f, 0.f, 56.f, 0.f)
			[
				Column(LOCTEXT("AudioHdr", "Audio"), AudioRows)
			]
			+ SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Top)
			[
				Column(LOCTEXT("DisplayHdr", "Display"), DisplayRows, 460.f)
			]
		]
		+ SVerticalBox::Slot().AutoHeight().Padding(0.f, 28.f, 0.f, 0.f)
		[
			NVUI::MakeText(LOCTEXT("OptHint", "CLICK  <  >  TO CHANGE A SETTING. CHANGES APPLY AND SAVE AT ONCE."), NVUI::EFont::Mono, 11.f,
				FSlateColor(NVUI::WithAlpha(NVUI::TextDim, 0.7f)), 140)
		];
}

#undef LOCTEXT_NAMESPACE
