#include "UI/NVHUD.h"
#include "Character/NVPlayerCharacter.h"
#include "Combat/NVHealthComponent.h"
#include "Combat/NVWeaponComponent.h"
#include "Combat/NVWeaponData.h"
#include "Interaction/NVInteractionComponent.h"
#include "Interaction/NVInteractable.h"
#include "Objectives/NVObjectiveSubsystem.h"
#include "Abilities/NVAbilityComponent.h"
#include "Abilities/NVAbilityData.h"
#include "Combat/NVMeleeComponent.h"
#include "Core/NVGameplayTags.h"
#include "InputCoreTypes.h"
#include "GameFramework/PlayerController.h"

#include "Camera/CameraComponent.h"
#include "Engine/Canvas.h"
#include "Engine/Engine.h"
#include "Engine/Font.h"
#include "Engine/World.h"
#include "CanvasItem.h"
#include "Kismet/GameplayStatics.h"
#include "Sound/SoundBase.h"
#include "Fonts/FontMeasure.h"
#include "Fonts/SlateFontInfo.h"
#include "Framework/Application/SlateApplication.h"
#include "Rendering/SlateRenderer.h"

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
		Old->GetMelee()->OnMeleeHit.RemoveDynamic(this, &ANVHUD::HandleMeleeHit);
		Old->GetAbilities()->OnAbilityFailed.RemoveDynamic(this, &ANVHUD::HandleAbilityFailed);
		Old->GetHealth()->OnDamageBlocked.RemoveDynamic(this, &ANVHUD::HandleDamageBlocked);
	}
	BoundPawn = Player;
	if (Player)
	{
		Player->GetWeapons()->OnHitConfirmed.AddDynamic(this, &ANVHUD::HandleHitConfirmed);
		Player->GetMelee()->OnMeleeHit.AddDynamic(this, &ANVHUD::HandleMeleeHit);
		Player->GetAbilities()->OnAbilityFailed.AddDynamic(this, &ANVHUD::HandleAbilityFailed);
		Player->GetHealth()->OnDamageBlocked.AddDynamic(this, &ANVHUD::HandleDamageBlocked);
	}
}

void ANVHUD::HandleHitConfirmed(AActor* HitActor, bool bWeakPoint)
{
	HitMarkerTime = GetWorld()->GetTimeSeconds();
	bHitMarkerWeak = bWeakPoint;
}

void ANVHUD::HandleMeleeHit(AActor* HitActor, bool bTakedown)
{
	HitMarkerTime = GetWorld()->GetTimeSeconds();
	bHitMarkerWeak = bTakedown;
	if (bTakedown)
	{
		ShowNotice(NSLOCTEXT("NeonVeil", "Takedown", "Takedown"), 1.2f);
	}
}

void ANVHUD::HandleAbilityFailed(FGameplayTag AbilityTag, ENVAbilityFailReason Reason)
{
	if (Reason == ENVAbilityFailReason::OnCooldown)
	{
		ShowThreat(NSLOCTEXT("NeonVeil", "Recharging", "Cyberware recharging"), 1.f);
	}
	else if (Reason == ENVAbilityFailReason::Disabled)
	{
		ShowThreat(NSLOCTEXT("NeonVeil", "Offline", "Cyberware offline"), 1.2f);
	}
}

void ANVHUD::HandleDamageBlocked(UNVHealthComponent* HealthComp, float BlockedAmount)
{
	ShieldFlashTime = GetWorld()->GetTimeSeconds();
}

void ANVHUD::ShowThreat(const FText& Text, float Duration)
{
	ThreatText = Text;
	ThreatUntil = GetWorld()->GetTimeSeconds() + Duration;
}

void ANVHUD::SetDetection(float Amount)
{
	Detection = FMath::Clamp(Amount, 0.f, 1.f);
	DetectionSetAt = GetWorld()->GetTimeSeconds();
}

void ANVHUD::UpdateInputDevice()
{
	const APlayerController* PC = GetOwningPlayerController();
	if (!PC)
	{
		return;
	}
	// Last device wins. Cheap polling keeps this independent of input plugins.
	static const FKey PadKeys[] = { EKeys::Gamepad_FaceButton_Bottom, EKeys::Gamepad_FaceButton_Right, EKeys::Gamepad_FaceButton_Left,
		EKeys::Gamepad_FaceButton_Top, EKeys::Gamepad_LeftShoulder, EKeys::Gamepad_RightShoulder, EKeys::Gamepad_LeftTrigger,
		EKeys::Gamepad_RightTrigger, EKeys::Gamepad_DPad_Up, EKeys::Gamepad_DPad_Down, EKeys::Gamepad_DPad_Left, EKeys::Gamepad_DPad_Right };
	bool bPad = FMath::Abs(PC->GetInputAnalogKeyState(EKeys::Gamepad_LeftX)) > 0.3f || FMath::Abs(PC->GetInputAnalogKeyState(EKeys::Gamepad_LeftY)) > 0.3f
		|| FMath::Abs(PC->GetInputAnalogKeyState(EKeys::Gamepad_RightX)) > 0.3f || FMath::Abs(PC->GetInputAnalogKeyState(EKeys::Gamepad_RightY)) > 0.3f;
	for (const FKey& K : PadKeys)
	{
		bPad |= PC->IsInputKeyDown(K);
	}
	float MX = 0.f, MY = 0.f;
	PC->GetInputMouseDelta(MX, MY);
	const bool bKbm = FMath::Abs(MX) + FMath::Abs(MY) > 0.5f || PC->IsInputKeyDown(EKeys::W) || PC->IsInputKeyDown(EKeys::A)
		|| PC->IsInputKeyDown(EKeys::S) || PC->IsInputKeyDown(EKeys::D) || PC->IsInputKeyDown(EKeys::LeftMouseButton) || PC->IsInputKeyDown(EKeys::E);
	if (bPad)
	{
		bUsingGamepad = true;
	}
	else if (bKbm)
	{
		bUsingGamepad = false;
	}
}

FString ANVHUD::KeyLabel(FName Action) const
{
	struct FRow { const TCHAR* Action; const TCHAR* Kbm; const TCHAR* PS; const TCHAR* Xbox; };
	static const FRow Rows[] = {
		{ TEXT("Interact"), TEXT("E"), TEXT("Triangle"), TEXT("Y") },
		{ TEXT("Melee"), TEXT("V"), TEXT("R3"), TEXT("RS") },
		{ TEXT("Ability1"), TEXT("Q"), TEXT("D-pad Left"), TEXT("D-pad Left") },
		{ TEXT("Ability2"), TEXT("G"), TEXT("D-pad Right"), TEXT("D-pad Right") },
		{ TEXT("Ability3"), TEXT("T"), TEXT("D-pad Up"), TEXT("D-pad Up") },
		{ TEXT("Crouch"), TEXT("Ctrl"), TEXT("Circle"), TEXT("B") },
		{ TEXT("Aim"), TEXT("RMB"), TEXT("L2"), TEXT("LT") },
		{ TEXT("NextWeapon"), TEXT("Mouse wheel"), TEXT("R1"), TEXT("RB") },
	};
	for (const FRow& R : Rows)
	{
		if (Action == FName(R.Action))
		{
			return FString::Printf(TEXT("[%s]"), bUsingGamepad ? (bPlayStationGlyphs ? R.PS : R.Xbox) : R.Kbm);
		}
	}
	return FString::Printf(TEXT("[%s]"), *Action.ToString());
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

FSlateFontInfo ANVHUD::MakeFont(UFont* Font, float Scale) const
{
	// Point sizes at 1080p before the UI scale; Large = headings and numbers.
	const float Base = (Font == LargeFont) ? 20.f : 13.f;
	return FSlateFontInfo(Font, FMath::Max(6.f, Base * Scale * TextScale));
}

void ANVHUD::MeasureText(const FString& Text, UFont* Font, float Scale, float& OutW, float& OutH) const
{
	if (Font && FSlateApplication::IsInitialized() && FSlateApplication::Get().GetRenderer())
	{
		const FVector2D Size = FSlateApplication::Get().GetRenderer()->GetFontMeasureService()->Measure(Text, MakeFont(Font, Scale));
		OutW = Size.X;
		OutH = Size.Y;
		return;
	}
	OutW = OutH = 0.f;
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
		MeasureText(Text, Font, Scale, W, H);
		X -= W;
	}
	FCanvasTextItem Item(FVector2D(X, Y), FText::FromString(Text), MakeFont(Font, Scale), Color);
	Item.EnableShadow(FLinearColor(0.f, 0.f, 0.f, 0.75f), FVector2D(2.f, 2.f));
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
	UpdateInputDevice();
	if (const ANVPlayerCharacter* P = BoundPawn.Get())
	{
		DrawAbilityOverlays(*P); // full-screen tints go under everything else
	}
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
		DrawAbilities(*Player);
		DrawMarks(*Player);
	}
	DrawThreat();
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

	// Weapon safety: friendly in the sights.
	if (W->GetFriendlyInSights() && !Player.IsSprinting())
	{
		const FString F = TEXT("FRIENDLY");
		float FW, FH;
		MeasureText(F, SmallFont, 0.7f * UIScale, FW, FH);
		DrawTextShadowed(F, CX - FW * 0.5f, CY + 26.f * UIScale, AccentColor, SmallFont, 0.7f * UIScale);
	}

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
	const FString HP = FString::Printf(TEXT("%d"), FMath::CeilToInt(H->GetHealth()));
	float TW, TH;
	MeasureText(HP, LargeFont, S, TW, TH);
	HealthTextTop = Y - 8.f * S - TH;
	DrawTextShadowed(HP, X, HealthTextTop, TextColor, LargeFont, S);
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
	const bool bLow = Slot.AmmoInMag <= FMath::Max(1, Data->MagazineSize / 4);
	const FString Mag = FString::Printf(TEXT("%d"), Slot.AmmoInMag);
	const FString Reserve = FString::Printf(TEXT("/ %d"), Slot.ReserveAmmo);
	const FString Name = W->IsReloading() ? TEXT("RELOADING") : Data->DisplayName.ToString().ToUpper();
	float MW, MH, RW, RH, NW, NH;
	MeasureText(Mag, LargeFont, 1.5f * S, MW, MH);
	MeasureText(Reserve, SmallFont, 1.15f * S, RW, RH);
	MeasureText(Name, SmallFont, 0.9f * S, NW, NH);
	// Stack from the bottom: weapon name, then magazine / reserve on one baseline.
	const float NameY = Canvas->ClipY - 58.f * S - NH;
	const float MagY = NameY - 4.f * S - MH;
	DrawTextShadowed(Reserve, RX, MagY + MH - RH - 4.f * S, TextColor * 0.8f, SmallFont, 1.15f * S, true);
	DrawTextShadowed(Mag, RX - RW - 10.f * S, MagY, bLow ? WarningColor : TextColor, LargeFont, 1.5f * S, true);
	DrawTextShadowed(Name, RX, NameY, W->IsReloading() ? WarningColor : AccentColor, SmallFont, 0.9f * S, true);
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
	float Y = 40.f * S;
	float TW, TH;
	const FString Title = Obj->GetCurrentMission()->MissionTitle.ToString().ToUpper();
	MeasureText(Title, SmallFont, 0.85f * S, TW, TH);
	DrawTextShadowed(Title, RX, Y, AccentColor, SmallFont, 0.85f * S, true);
	Y += TH + 6.f * S;
	for (const FNVObjectiveDef& Def : Obj->GetActiveObjectives())
	{
		const FString Line = Def.bOptional ? FString::Printf(TEXT("(Optional) %s"), *Def.DisplayText.ToString()) : Def.DisplayText.ToString();
		MeasureText(Line, SmallFont, 1.05f * S, TW, TH);
		DrawTextShadowed(Line, RX, Y, Def.bOptional ? TextColor * 0.75f : TextColor, SmallFont, 1.05f * S, true);
		Y += TH + 4.f * S;
	}
	DrawInstruction(Y + 14.f * S);
}

void ANVHUD::DrawInstruction(float Y)
{
	if (InstructionText.IsEmpty())
	{
		return;
	}
	const float S = Canvas->ClipY / 1080.f;
	FString T = InstructionText.ToString();
	// Device-aware button tokens, e.g. "{Ability2}" -> "[G]" or "[D-pad Right]".
	static const TCHAR* Tokens[] = { TEXT("Interact"), TEXT("Melee"), TEXT("Ability1"), TEXT("Ability2"), TEXT("Ability3"), TEXT("Crouch"), TEXT("Aim"), TEXT("NextWeapon") };
	for (const TCHAR* Tok : Tokens)
	{
		T.ReplaceInline(*FString::Printf(TEXT("{%s}"), Tok), *KeyLabel(Tok), ESearchCase::CaseSensitive);
	}
	DrawTextShadowed(T, Canvas->ClipX - 48.f * S, Y, AccentColor, SmallFont, 1.05f * S, true);
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
	const FString Key = KeyLabel(TEXT("Interact"));
	const FString Label = Hold > 0.f ? FString::Printf(TEXT("Hold %s"), *Key) : Key;
	const FString PromptText = FString::Printf(TEXT("%s  %s"), *Label, *Prompt.ToString());
	float PW, PH;
	MeasureText(PromptText, SmallFont, 1.05f * S, PW, PH);
	DrawTextShadowed(PromptText, X, Y, TextColor, SmallFont, 1.05f * S);
	if (Hold > 0.f && I->GetHoldProgress() > 0.f)
	{
		const float BarW = FMath::Max(160.f * S, PW);
		DrawRect(FLinearColor(0.f, 0.f, 0.f, 0.45f), X, Y + PH + 6.f * S, BarW, 4.f * S);
		DrawRect(AccentColor, X, Y + PH + 6.f * S, BarW * I->GetHoldProgress(), 4.f * S);
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

	if (Now < TitleUntil)
	{
		const float Fade = FMath::Clamp((Now - TitleStart) / 1.2f, 0.f, 1.f) * FMath::Clamp((TitleUntil - Now) / 1.0f, 0.f, 1.f);
		FLinearColor C = TextColor;
		C.A = Fade;
		FLinearColor A2 = AccentColor;
		A2.A = Fade;
		float W, H;
		const FString T = TitleText.ToString().ToUpper();
		MeasureText(T, LargeFont, 2.2f * S, W, H);
		const float TitleY = Canvas->ClipY * 0.42f;
		DrawTextShadowed(T, (Canvas->ClipX - W) * 0.5f, TitleY, C, LargeFont, 2.2f * S);
		const float SubY = TitleY + H + 16.f * S;
		const FString Sub = TitleSubText.ToString();
		MeasureText(Sub, SmallFont, 1.1f * S, W, H);
		DrawTextShadowed(Sub, (Canvas->ClipX - W) * 0.5f, SubY, A2, SmallFont, 1.1f * S);
	}
	if (Now < NoticeUntil)
	{
		float W, H;
		const FString T = NoticeText.ToString().ToUpper();
		MeasureText(T, SmallFont, 1.1f * S, W, H);
		DrawTextShadowed(T, (Canvas->ClipX - W) * 0.5f, Canvas->ClipY * 0.22f, AccentColor, SmallFont, 1.1f * S);
	}
	if (Now < SubtitleUntil)
	{
		const float Scale = 1.15f * S * SubtitleScale;
		const FString Line = FString::Printf(TEXT("%s:  %s"), *SubtitleSpeaker.ToString().ToUpper(), *SubtitleLine.ToString());
		float W, H;
		MeasureText(Line, SmallFont, Scale, W, H);
		const float X = (Canvas->ClipX - W) * 0.5f;
		const float Y = Canvas->ClipY - 225.f * S - H; // clear of the ability bar and health
		// Readable background box (Bible §10).
		DrawRect(FLinearColor(0.f, 0.f, 0.f, 0.55f), X - 14.f * S, Y - 8.f * S, W + 28.f * S, H + 16.f * S);
		DrawTextShadowed(Line, X, Y, TextColor, SmallFont, Scale);
	}
}

void ANVHUD::DrawAbilities(const ANVPlayerCharacter& Player)
{
	const UNVAbilityComponent* A = Player.GetAbilities();
	if (!A || A->Abilities.Num() == 0)
	{
		return;
	}
	const float S = Canvas->ClipY / 1080.f;
	const float Size = 46.f * S * FMath::Max(1.f, TextScale * 0.85f), Gap = 12.f * S;
	static const FName Actions[] = { TEXT("Ability1"), TEXT("Ability2"), TEXT("Ability3") };
	float LW, LH;
	MeasureText(TEXT("Ag"), SmallFont, 0.62f * S, LW, LH);
	const float Bottom = (HealthTextTop > 0.f ? HealthTextTop : Canvas->ClipY - 120.f * S) - 10.f * S;
	const float Y = Bottom - LH - 4.f * S - Size;
	float X = 48.f * S;
	for (int32 i = 0; i < A->Abilities.Num() && i < 3; ++i)
	{
		const UNVAbilityData* D = A->Abilities[i];
		const FNVAbilityRuntime* R = A->GetRuntime(i);
		if (!D || !R)
		{
			continue;
		}
		DrawRect(FLinearColor(0.f, 0.f, 0.f, 0.5f), X, Y, Size, Size);
		FLinearColor LabelColor = TextColor;
		if (R->bDisabled)
		{
			LabelColor = WarningColor * 0.8f;
		}
		else if (R->ActiveTimeLeft > 0.f)
		{
			// Active: accent fill draining with the remaining time.
			const float F = A->GetActiveFraction(i);
			DrawRect(FLinearColor(AccentColor.R, AccentColor.G, AccentColor.B, 0.45f), X, Y + Size * (1.f - F), Size, Size * F);
			LabelColor = FLinearColor::White;
		}
		else if (R->CooldownLeft > 0.f)
		{
			const float F = A->GetCooldownFraction(i);
			DrawRect(FLinearColor(0.f, 0.f, 0.f, 0.55f), X, Y, Size, Size * F);
			LabelColor = TextColor * 0.55f;
		}
		else
		{
			// Ready: thin accent underline.
			DrawRect(AccentColor, X, Y + Size - 2.f * S, Size, 2.f * S);
		}
		const FString Short = D->ShortLabel.ToString();
		float SW, SH;
		MeasureText(Short, SmallFont, 0.95f * S, SW, SH);
		DrawTextShadowed(Short, X + (Size - SW) * 0.5f, Y + (Size - SH) * 0.5f, LabelColor, SmallFont, 0.95f * S);
		const FString Under = R->bDisabled ? TEXT("OFFLINE") : (R->CooldownLeft > 0.f ? FString::Printf(TEXT("%.0f"), FMath::CeilToFloat(R->CooldownLeft)) : KeyLabel(Actions[i]));
		float UW, UH;
		MeasureText(Under, SmallFont, 0.62f * S, UW, UH);
		DrawTextShadowed(Under, X, Y + Size + 4.f * S, R->bDisabled ? WarningColor : TextColor * 0.8f, SmallFont, 0.62f * S);
		X += FMath::Max(Size, UW) + Gap;
	}
}

void ANVHUD::DrawAbilityOverlays(const ANVPlayerCharacter& Player)
{
	const UNVAbilityComponent* A = Player.GetAbilities();
	if (!A)
	{
		return;
	}
	const float W = Canvas->ClipX, H = Canvas->ClipY;
	const float Now = GetWorld()->GetTimeSeconds();
	if (A->IsAbilityActive(NVTags::Ability_OpticalDisruption))
	{
		// Placeholder for the M6 post-process: cool tint plus a soft edge frame.
		const float Pulse = 0.04f + 0.02f * FMath::Sin(Now * 6.f);
		DrawRect(FLinearColor(0.2f, 0.75f, 1.f, Pulse), 0.f, 0.f, W, H);
		const float E = 18.f * H / 1080.f;
		const FLinearColor Edge(0.35f, 0.9f, 1.f, 0.18f);
		DrawRect(Edge, 0.f, 0.f, W, E);
		DrawRect(Edge, 0.f, H - E, W, E);
		DrawRect(Edge, 0.f, E, E, H - 2.f * E);
		DrawRect(Edge, W - E, E, E, H - 2.f * E);
	}
	if (A->IsAbilityActive(NVTags::Ability_KineticShield))
	{
		const float Flash = FMath::Clamp(1.f - (Now - ShieldFlashTime) / 0.25f, 0.f, 1.f);
		const float E = (10.f + 14.f * Flash) * H / 1080.f;
		const FLinearColor Edge(0.75f, 0.85f, 1.f, 0.22f + 0.4f * Flash);
		DrawRect(Edge, 0.f, 0.f, W, E);
		DrawRect(Edge, 0.f, H - E, W, E);
		DrawRect(Edge, 0.f, E, E, H - 2.f * E);
		DrawRect(Edge, W - E, E, E, H - 2.f * E);
	}
}

void ANVHUD::DrawMarks(const ANVPlayerCharacter& Player)
{
	const UNVAbilityComponent* A = Player.GetAbilities();
	if (!A)
	{
		return;
	}
	const float S = Canvas->ClipY / 1080.f;
	for (AActor* M : A->GetMarkedActors())
	{
		FVector Center, Extent;
		M->GetActorBounds(true, Center, Extent);
		const FVector Top = Center + FVector(0.f, 0.f, Extent.Z + 25.f);
		const FVector Screen = Project(Top, true);
		if (Screen.Z <= 0.f)
		{
			continue; // behind the camera
		}
		// Small diamond (two stacked rects) in emergency amber: marked, not necessarily hostile.
		const float D = 7.f * S;
		DrawRect(WarningColor, Screen.X - D * 0.5f, Screen.Y - D, D, D * 2.f);
		DrawRect(WarningColor, Screen.X - D, Screen.Y - D * 0.5f, D * 2.f, D);
		const float Dist = FVector::Dist(Player.GetActorLocation(), Center) / 100.f;
		DrawTextShadowed(FString::Printf(TEXT("%.0fm"), Dist), Screen.X + 10.f * S, Screen.Y - 9.f * S, WarningColor, SmallFont, 0.65f * S);
	}
}

void ANVHUD::DrawThreat()
{
	const float Now = GetWorld()->GetTimeSeconds();
	const float S = Canvas->ClipY / 1080.f;
	const float CX = Canvas->ClipX * 0.5f, CY = Canvas->ClipY * 0.5f;
	if (Now < ThreatUntil && !ThreatText.IsEmpty())
	{
		float TW = 0.f, TH = 0.f;
		const FString T = ThreatText.ToString().ToUpper();
		MeasureText(T, SmallFont, 0.95f * S, TW, TH);
		const float Blink = FMath::Fmod(Now * 4.f, 1.f) < 0.65f ? 1.f : 0.45f;
		DrawTextShadowed(T, CX - TW * 0.5f, CY + 60.f * S, WarningColor * Blink, SmallFont, 0.95f * S);
	}
	if (Now - DetectionSetAt < 0.25f && Detection > 0.01f)
	{
		// Restrained detection meter just above the reticle.
		const float BW = 90.f * S, BH = 4.f * S;
		DrawRect(FLinearColor(0.f, 0.f, 0.f, 0.5f), CX - BW * 0.5f, CY - 48.f * S, BW, BH);
		DrawRect(Detection >= 1.f ? FLinearColor(1.f, 0.25f, 0.2f, 1.f) : WarningColor, CX - BW * 0.5f, CY - 48.f * S, BW * Detection, BH);
	}
}
