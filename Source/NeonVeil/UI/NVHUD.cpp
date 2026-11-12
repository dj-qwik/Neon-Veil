#include "UI/NVHUD.h"
#include "Character/NVPlayerCharacter.h"
#include "Combat/NVHealthComponent.h"
#include "Combat/NVWeaponComponent.h"
#include "Combat/NVWeaponData.h"
#include "Interaction/NVInteractionComponent.h"
#include "Interaction/NVInteractable.h"
#include "Objectives/NVObjectiveSubsystem.h"

#include "Camera/CameraComponent.h"
#include "Engine/Canvas.h"
#include "Engine/Engine.h"
#include "Engine/Font.h"
#include "Engine/World.h"
#include "CanvasItem.h"
#include "Kismet/GameplayStatics.h"
#include "Sound/SoundBase.h"

ANVHUD::ANVHUD()
{
}

void ANVHUD::BeginPlay()
{
	Super::BeginPlay();
	SmallFont = GEngine ? GEngine->GetMediumFont() : nullptr;
	LargeFont = GEngine ? GEngine->GetLargeFont() : nullptr;
	if (UNVObjectiveSubsystem* Obj = UNVObjectiveSubsystem::Get(this))
	{
		Obj->OnObjectiveCompleted.AddDynamic(this, &ANVHUD::HandleObjectiveCompleted);
	}
}

void ANVHUD::BindToPawn()
{
	ANVPlayerCharacter* Player = Cast<ANVPlayerCharacter>(GetOwningPawn());
	if (Player == BoundPawn.Get())
	{
		return;
	}
	if (ANVPlayerCharacter* Old = BoundPawn.Get())
	{
		Old->GetWeapons()->OnHitConfirmed.RemoveDynamic(this, &ANVHUD::HandleHitConfirmed);
	}
	BoundPawn = Player;
	if (Player)
	{
		Player->GetWeapons()->OnHitConfirmed.AddDynamic(this, &ANVHUD::HandleHitConfirmed);
	}
}

void ANVHUD::HandleHitConfirmed(AActor* HitActor, bool bWeakPoint)
{
	HitMarkerTime = GetWorld()->GetTimeSeconds();
	bHitMarkerWeak = bWeakPoint;
}

void ANVHUD::HandleObjectiveCompleted(FName ObjectiveID)
{
	ShowNotice(NSLOCTEXT("NeonVeil", "ObjectiveComplete", "Objective complete"));
}

void ANVHUD::ShowNotice(const FText& Text, float Duration)
{
	NoticeText = Text;
	NoticeUntil = GetWorld()->GetTimeSeconds() + Duration;
}

void ANVHUD::ShowSubtitle(const FText& Speaker, const FText& Line, float Duration)
{
	SubtitleSpeaker = Speaker;
	SubtitleLine = Line;
	SubtitleUntil = GetWorld()->GetTimeSeconds() + Duration;
}

void ANVHUD::QueueSubtitles(const TArray<FNVSubtitleLine>& Lines)
{
	SubtitleQueue.Append(Lines);
}

void ANVHUD::ShowTitleCard(const FText& Title, const FText& Subtitle, float Duration)
{
	TitleText = Title;
	TitleSubText = Subtitle;
	TitleStart = GetWorld()->GetTimeSeconds();
	TitleUntil = TitleStart + Duration;
}

void ANVHUD::DrawTextShadowed(const FString& Text, float X, float Y, const FLinearColor& Color, UFont* Font, float Scale, bool bRightAlign)
{
	if (!Canvas || !Font)
	{
		return;
	}
	if (bRightAlign)
	{
		float W, H;
		GetTextSize(Text, W, H, Font, Scale);
		X -= W;
	}
	FCanvasTextItem Item(FVector2D(X, Y), FText::FromString(Text), Font, Color);
	Item.Scale = FVector2D(Scale, Scale);
	Item.EnableShadow(FLinearColor(0.f, 0.f, 0.f, 0.7f), FVector2D(1.5f, 1.5f));
	Canvas->DrawItem(Item);
}

void ANVHUD::DrawHUD()
{
	Super::DrawHUD();
	if (!Canvas)
	{
		return;
	}
	BindToPawn();
	DrawMessages();
	if (!bHUDVisible)
	{
		return;
	}
	if (const ANVPlayerCharacter* Player = BoundPawn.Get())
	{
		DrawReticle(*Player);
		DrawHealth(*Player);
		DrawAmmo(*Player);
		DrawPrompt(*Player);
	}
	DrawObjectives();
}

void ANVHUD::DrawReticle(const ANVPlayerCharacter& Player)
{
	const float CX = Canvas->ClipX * 0.5f;
	const float CY = Canvas->ClipY * 0.5f;
	const float UIScale = Canvas->ClipY / 1080.f;
	const UNVWeaponComponent* W = Player.GetWeapons();
	const float Ads = W->GetAdsAlpha();

	// Gap follows the real spread cone, so the reticle never lies about accuracy.
	const float HalfFOV = FMath::DegreesToRadians(Player.GetFirstPersonCamera()->FieldOfView * 0.5f);
	const float SpreadRad = FMath::DegreesToRadians(W->GetCurrentSpreadDeg());
	const float Gap = FMath::Max(3.f, (FMath::Tan(SpreadRad) / FMath::Tan(HalfFOV)) * CX) ;
	const float Len = 7.f * UIScale;
	const float Alpha = 0.85f * (1.f - 0.7f * Ads);
	FLinearColor C = TextColor;
	C.A = Alpha;

	if (Alpha > 0.05f && !Player.IsSprinting())
	{
		DrawLine(CX - Gap - Len, CY, CX - Gap, CY, C, 1.5f);
		DrawLine(CX + Gap, CY, CX + Gap + Len, CY, C, 1.5f);
		DrawLine(CX, CY - Gap - Len, CX, CY - Gap, C, 1.5f);
		DrawLine(CX, CY + Gap, CX, CY + Gap + Len, C, 1.5f);
	}
	// Centre dot always visible (accessibility: crosshair never hidden during combat, Bible §5).
	DrawRect(FLinearColor(C.R, C.G, C.B, 0.9f), CX - 1.f, CY - 1.f, 2.f, 2.f);

	// Hit marker
	const float Since = GetWorld()->GetTimeSeconds() - HitMarkerTime;
	if (Since < 0.15f)
	{
		FLinearColor HM = bHitMarkerWeak ? WarningColor : TextColor;
		HM.A = 1.f - Since / 0.15f;
		const float A = 5.f * UIScale, B = 11.f * UIScale;
		DrawLine(CX - B, CY - B, CX - A, CY - A, HM, 2.f);
		DrawLine(CX + A, CY - A, CX + B, CY - B, HM, 2.f);
		DrawLine(CX - B, CY + B, CX - A, CY + A, HM, 2.f);
		DrawLine(CX + A, CY + A, CX + B, CY + B, HM, 2.f);
	}
}

void ANVHUD::DrawHealth(const ANVPlayerCharacter& Player)
{
	const float S = Canvas->ClipY / 1080.f;
	const UNVHealthComponent* H = Player.GetHealth();
	const float X = 48.f * S, Y = Canvas->ClipY - 70.f * S;
	const float W = 260.f * S, BarH = 6.f * S;
	const float Pct = H->GetHealthPercent();
	const FLinearColor Fill = Pct < 0.3f ? WarningColor : AccentColor;

	DrawRect(FLinearColor(0.f, 0.f, 0.f, 0.45f), X, Y, W, BarH);
	DrawRect(Fill, X, Y, W * Pct, BarH);
	if (H->MaxShield > 0.f)
	{
		DrawRect(FLinearColor(0.75f, 0.85f, 1.f, 0.8f), X, Y - 5.f * S, W * (H->GetShield() / H->MaxShield), 3.f * S);
	}
	DrawTextShadowed(FString::Printf(TEXT("%d"), FMath::CeilToInt(H->GetHealth())), X, Y - 38.f * S, TextColor, LargeFont, S);
}

void ANVHUD::DrawAmmo(const ANVPlayerCharacter& Player)
{
	const float S = Canvas->ClipY / 1080.f;
	const UNVWeaponComponent* W = Player.GetWeapons();
	const UNVWeaponData* Data = W->GetCurrentWeapon();
	if (!Data)
	{
		return;
	}
	const TArray<FNVWeaponSlot>& Slots = W->GetSlots();
	const FNVWeaponSlot& Slot = Slots[W->GetCurrentSlotIndex()];
	const float RX = Canvas->ClipX - 48.f * S;
	const float Y = Canvas->ClipY - 108.f * S;
	const bool bLow = Slot.AmmoInMag <= FMath::Max(1, Data->MagazineSize / 4);
	DrawTextShadowed(FString::Printf(TEXT("%d"), Slot.AmmoInMag), RX - 90.f * S, Y, bLow ? WarningColor : TextColor, LargeFont, 1.6f * S, true);
	DrawTextShadowed(FString::Printf(TEXT("/ %d"), Slot.ReserveAmmo), RX, Y + 14.f * S, TextColor * 0.8f, SmallFont, 1.2f * S, true);
	const FString Name = W->IsReloading() ? TEXT("RELOADING") : Data->DisplayName.ToString().ToUpper();
	DrawTextShadowed(Name, RX, Y + 48.f * S, W->IsReloading() ? WarningColor : AccentColor, SmallFont, 0.9f * S, true);
}

void ANVHUD::DrawObjectives()
{
	const UNVObjectiveSubsystem* Obj = UNVObjectiveSubsystem::Get(this);
	if (!Obj || !Obj->GetCurrentMission())
	{
		return;
	}
	const float S = Canvas->ClipY / 1080.f;
	const float RX = Canvas->ClipX - 48.f * S;
	float Y = 44.f * S;
	DrawTextShadowed(Obj->GetCurrentMission()->MissionTitle.ToString().ToUpper(), RX, Y, AccentColor, SmallFont, 0.85f * S, true);
	Y += 26.f * S;
	for (const FNVObjectiveDef& Def : Obj->GetActiveObjectives())
	{
		const FString Line = Def.bOptional ? FString::Printf(TEXT("(Optional) %s"), *Def.DisplayText.ToString()) : Def.DisplayText.ToString();
		DrawTextShadowed(Line, RX, Y, Def.bOptional ? TextColor * 0.75f : TextColor, SmallFont, 1.05f * S, true);
		Y += 28.f * S;
	}
}

void ANVHUD::DrawPrompt(const ANVPlayerCharacter& Player)
{
	const UNVInteractionComponent* I = Player.GetInteraction();
	AActor* Focus = I->GetFocusedActor();
	if (!Focus || !Focus->Implements<UNVInteractable>())
	{
		return;
	}
	const float S = Canvas->ClipY / 1080.f;
	const float X = Canvas->ClipX * 0.5f + 60.f * S;
	const float Y = Canvas->ClipY * 0.5f + 20.f * S;
	const FText Prompt = INVInteractable::Execute_GetInteractionPrompt(Focus, const_cast<ANVPlayerCharacter*>(&Player));
	const float Hold = INVInteractable::Execute_GetHoldDuration(Focus);
	const FString KeyLabel = Hold > 0.f ? TEXT("Hold [E]") : TEXT("[E]");
	DrawTextShadowed(FString::Printf(TEXT("%s  %s"), *KeyLabel, *Prompt.ToString()), X, Y, TextColor, SmallFont, 1.05f * S);
	if (Hold > 0.f && I->GetHoldProgress() > 0.f)
	{
		DrawRect(FLinearColor(0.f, 0.f, 0.f, 0.45f), X, Y + 30.f * S, 160.f * S, 3.f * S);
		DrawRect(AccentColor, X, Y + 30.f * S, 160.f * S * I->GetHoldProgress(), 3.f * S);
	}
}

void ANVHUD::DrawMessages()
{
	const float Now = GetWorld()->GetTimeSeconds();
	const float S = Canvas->ClipY / 1080.f;

	// Advance the subtitle queue when the current line has finished.
	if (Now >= SubtitleUntil && SubtitleQueue.Num() > 0)
	{
		const FNVSubtitleLine Line = SubtitleQueue[0];
		SubtitleQueue.RemoveAt(0);
		ShowSubtitle(Line.Speaker, Line.Text, Line.Duration);
		if (Line.Voice)
		{
			UGameplayStatics::PlaySound2D(this, Line.Voice);
		}
	}

	if (!InstructionText.IsEmpty() && bHUDVisible)
	{
		const FString T = InstructionText.ToString();
		float W, H;
		GetTextSize(T, W, H, SmallFont, 1.05f * S);
		DrawTextShadowed(T, Canvas->ClipX - 48.f * S - W, 190.f * S, AccentColor, SmallFont, 1.05f * S);
	}

	if (Now < TitleUntil)
	{
		const float Fade = FMath::Clamp((Now - TitleStart) / 1.2f, 0.f, 1.f) * FMath::Clamp((TitleUntil - Now) / 1.0f, 0.f, 1.f);
		FLinearColor C = TextColor;
		C.A = Fade;
		FLinearColor A2 = AccentColor;
		A2.A = Fade;
		float W, H;
		const FString T = TitleText.ToString().ToUpper();
		GetTextSize(T, W, H, LargeFont, 2.2f * S);
		DrawTextShadowed(T, (Canvas->ClipX - W) * 0.5f, Canvas->ClipY * 0.44f, C, LargeFont, 2.2f * S);
		const FString Sub = TitleSubText.ToString();
		GetTextSize(Sub, W, H, SmallFont, 1.1f * S);
		DrawTextShadowed(Sub, (Canvas->ClipX - W) * 0.5f, Canvas->ClipY * 0.44f + 70.f * S, A2, SmallFont, 1.1f * S);
	}
	if (Now < NoticeUntil)
	{
		float W, H;
		const FString T = NoticeText.ToString().ToUpper();
		GetTextSize(T, W, H, SmallFont, 1.1f * S);
		DrawTextShadowed(T, (Canvas->ClipX - W) * 0.5f, Canvas->ClipY * 0.22f, AccentColor, SmallFont, 1.1f * S);
	}
	if (Now < SubtitleUntil)
	{
		const float Scale = 1.15f * S * SubtitleScale;
		const FString Line = FString::Printf(TEXT("%s:  %s"), *SubtitleSpeaker.ToString().ToUpper(), *SubtitleLine.ToString());
		float W, H;
		GetTextSize(Line, W, H, SmallFont, Scale);
		const float X = (Canvas->ClipX - W) * 0.5f;
		const float Y = Canvas->ClipY - 190.f * S;
		// Readable background box (Bible §10).
		DrawRect(FLinearColor(0.f, 0.f, 0.f, 0.55f), X - 14.f * S, Y - 8.f * S, W + 28.f * S, H + 16.f * S);
		DrawTextShadowed(Line, X, Y, TextColor, SmallFont, Scale);
	}
}
