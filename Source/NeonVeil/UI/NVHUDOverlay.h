#pragma once

#include "CoreMinimal.h"
#include "Widgets/SCompoundWidget.h"
#include "Widgets/DeclarativeSyntaxSupport.h"
#include "UI/NVCommsMessage.h"

class ANVHUD;
class ANVPlayerCharacter;
class SBox;
class SVerticalBox;
class SNVFrame;
class SNVTypeText;
class SNVMenuShell;

/**
 * GHOST-OS heads-up layer, added to the game viewport by ANVHUD. Owns the comms feed, subtitles, notices, title cards,
 * objectives, interaction prompt, vitals, cyberware slots, weapon readout, threat text and the menu shell.
 * World-space and reticle drawing stay on the HUD canvas underneath.
 */
class NEONVEIL_API SNVHUDOverlay : public SCompoundWidget
{
public:
	SLATE_BEGIN_ARGS(SNVHUDOverlay) {}
		SLATE_ARGUMENT(TWeakObjectPtr<ANVHUD>, HUD)
	SLATE_END_ARGS()

	void Construct(const FArguments& InArgs);
	virtual void Tick(const FGeometry& AllottedGeometry, const double InCurrentTime, const float InDeltaTime) override;

	void PushMessage(const FNVCommsMessage& Message);
	void ShowNotice(const FText& Text, float Duration, bool bWarning = false);
	void ShowSubtitle(const FText& Speaker, const FText& Line, float Duration);
	void ShowTitleCard(const FText& Title, const FText& Subtitle, float Duration);

private:
	ANVPlayerCharacter* Pawn() const;
	bool HudOn() const;
	EVisibility VisIf(bool b) const { return b ? EVisibility::HitTestInvisible : EVisibility::Collapsed; }

	TSharedRef<SWidget> BuildVitals();
	TSharedRef<SWidget> BuildCyberSlots();
	TSharedRef<SWidget> BuildWeapon();
	TSharedRef<SWidget> BuildPrompt();
	TSharedRef<SWidget> BuildThreat();
	void OpenCard(const FNVCommsMessage& Message);
	void RefreshObjectives();
	void RefreshMenu();

	TWeakObjectPtr<ANVHUD> HUD;
	float Clock = 0.f; // game-time clock (stops while paused)

	struct FCard
	{
		TSharedPtr<SWidget> Holder;
		TSharedPtr<SNVFrame> Frame;
		float ExpireAt = 0.f;
	};
	TSharedPtr<SVerticalBox> CommsBox;
	TArray<FCard> Cards;
	TArray<FNVCommsMessage> PendingCards;

	TSharedPtr<SBox> NoticeHolder;
	float NoticeUntil = -1.f;

	TSharedPtr<SBox> SubtitleHolder;
	TSharedPtr<SNVFrame> SubtitleFrame;
	TSharedPtr<SNVTypeText> SubtitleText;
	FText SubtitleSpeaker;
	float SubtitleUntil = -1.f;

	TSharedPtr<SBox> TitleHolder;
	float TitleUntil = -1.f;

	TSharedPtr<SBox> ObjectivesHolder;
	FString ObjectiveSig;

	TSharedPtr<SBox> MenuHolder;
	bool bMenuShown = false;
};
