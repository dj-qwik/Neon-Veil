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
#include "Core/NVPlayerController.h"
#include "HAL/PlatformTime.h"

#include "Camera/CameraComponent.h"
#include "Engine/Canvas.h"
#include "CanvasItem.h"
#include "Engine/Texture2D.h"
#include "TextureResource.h"
#include "Engine/Engine.h"
#include "Engine/Font.h"
#include "Engine/World.h"
#include "CanvasItem.h"
#include "Engine/Texture2D.h"
#include "TextureResource.h"
#include "Kismet/GameplayStatics.h"
#include "Sound/SoundBase.h"
#include "Fonts/FontMeasure.h"
#include "Fonts/SlateFontInfo.h"
#include "Framework/Application/SlateApplication.h"
#include "Rendering/SlateRenderer.h"
#include "UI/NVHUDOverlay.h"
#include "UI/NVUIStyle.h"
#include "Widgets/SWeakWidget.h"
#include "Engine/GameViewportClient.h"

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
	// TextScale 1.4 is the canvas-era default; GHOST-OS sizes are designed at 1.0.
	NVUI::SetTextScale(TextScale / 1.4f);
	CreateOverlay();
}

void ANVHUD::CreateOverlay()
{
	const APlayerController* PC = GetOwningPlayerController();
	UGameViewportClient* Viewport = GetWorld() ? GetWorld()->GetGameViewport() : nullptr;
	if (!PC || !PC->IsLocalController() || !Viewport || Overlay.IsValid())
	{
		return;
	}
	Overlay = SNew(SNVHUDOverlay).HUD(this);
	OverlayHost = SNew(SWeakWidget).PossiblyNullContent(Overlay);
	Viewport->AddViewportWidgetContent(OverlayHost.ToSharedRef(), 10);
}

void ANVHUD::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	if (OverlayHost.IsValid())
	{
		if (UGameViewportClient* Viewport = GetWorld() ? GetWorld()->GetGameViewport() : nullptr)
		{
			Viewport->RemoveViewportWidgetContent(OverlayHost.ToSharedRef());
		}
	}
	OverlayHost.Reset();
	Overlay.Reset();
	Super::EndPlay(EndPlayReason);
}

void ANVHUD::PushMessage(const FNVCommsMessage& Message)
{
	FNVCommsLogEntry& E = CommsLog.AddDefaulted_GetRef();
	E.Message = Message;
	E.Time = GetWorld() ? GetWorld()->GetTimeSeconds() : 0.f;
	if (Overlay.IsValid())
	{
		Overlay->PushMessage(Message);
	}
	if (Message.Voice)
	{
		UGameplayStatics::PlaySound2D(this, Message.Voice, VoiceVolume);
	}
}

void ANVHUD::ShowMessage(const FText& Sender, const FText& Body, const FText& Channel, bool bPriority)
{
	FNVCommsMessage M;
	M.Sender = Sender;
	M.Body = Body;
	M.Channel = Channel;
	M.bPriority = bPriority;
	PushMessage(M);
}

FText ANVHUD::GetInstructionDisplay() const
{
	if (InstructionText.IsEmpty())
	{
		return FText::GetEmpty();
	}
	FString T = InstructionText.ToString();
	// Device-aware button tokens, e.g. "{Ability2}" -> "[G]" or "[D-pad Right]".
	static const TCHAR* Tokens[] = { TEXT("Interact"), TEXT("Melee"), TEXT("Ability1"), TEXT("Ability2"), TEXT("Ability3"), TEXT("Crouch"), TEXT("Aim"),
		TEXT("NextWeapon"), TEXT("Jump"), TEXT("Sprint"), TEXT("Holster"), TEXT("NavGuide"), TEXT("Fire") };
	for (const TCHAR* Tok : Tokens)
	{
		T.ReplaceInline(*FString::Printf(TEXT("{%s}"), Tok), *KeyLabel(Tok), ESearchCase::CaseSensitive);
	}
	return FText::FromString(T);
}

bool ANVHUD::GetThreat(FText& OutText) const
{
	if (GetWorld() && GetWorld()->GetTimeSeconds() < ThreatUntil && !ThreatText.IsEmpty())
	{
		OutText = ThreatText;
		return true;
	}
	return false;
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
		{ TEXT("Jump"), TEXT("Space"), TEXT("Cross"), TEXT("A") },
		{ TEXT("Sprint"), TEXT("Shift"), TEXT("L3"), TEXT("LS") },
		{ TEXT("Aim"), TEXT("RMB"), TEXT("L2"), TEXT("LT") },
		{ TEXT("NextWeapon"), TEXT("Mouse wheel"), TEXT("R1"), TEXT("RB") },
		{ TEXT("Holster"), TEXT("H"), TEXT("Hold D-pad Down"), TEXT("Hold D-pad Down") },
		{ TEXT("NavGuide"), TEXT("N"), TEXT("D-pad Down"), TEXT("D-pad Down") },
		{ TEXT("Fire"), TEXT("LMB"), TEXT("R2"), TEXT("RT") },
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

FText ANVHUD::KeyCap(FName Action) const
{
	FString L = KeyLabel(Action);
	L.RemoveFromStart(TEXT("["));
	L.RemoveFromEnd(TEXT("]"));
	return FText::FromString(L.ToUpper());
}

void ANVHUD::HandleObjectiveCompleted(FName ObjectiveID)
{
	ShowNotice(NSLOCTEXT("NeonVeil", "ObjectiveComplete", "Objective complete"));
}

void ANVHUD::ShowNotice(const FText& Text, float Duration)
{
	if (Overlay.IsValid())
	{
		Overlay->ShowNotice(Text, Duration);
	}
}
void ANVHUD::ShowSubtitle(const FText& Speaker, const FText& Line, float Duration)
{
	SubtitleUntil = GetWorld()->GetTimeSeconds() + Duration;
	if (Overlay.IsValid())
	{
		Overlay->ShowSubtitle(Speaker, Line, Duration);
	}
}
void ANVHUD::QueueSubtitles(const TArray<FNVSubtitleLine>& Lines)
{
	SubtitleQueue.Append(Lines);
}

void ANVHUD::ShowTitleCard(const FText& Title, const FText& Subtitle, float Duration)
{
	if (Overlay.IsValid())
	{
		Overlay->ShowTitleCard(Title, Subtitle, Duration);
	}
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
	if (!Overlay.IsValid())
	{
		CreateOverlay();
	}
	if (const ANVPlayerCharacter* P = BoundPawn.Get())
	{
		DrawAbilityOverlays(*P); // full-screen tints go under everything else
	}
	UpdateSubtitleQueue();
	if (bHUDVisible)
	{
		if (const ANVPlayerCharacter* Player = BoundPawn.Get())
		{
			if (Player->IsScopedIn())
			{
				DrawScope(*Player);
			}
			else
			{
				DrawReticle(*Player);
			}
			DrawMarks(*Player);
		}
		DrawDetection();
	}
	DrawFadeIn();
}
void ANVHUD::DrawFadeIn()
{
	const double Now = FPlatformTime::Seconds();
	if (FadeStartTime < 0.0)
	{
		const double Step = FadeLastTime > 0.0 ? Now - FadeLastTime : 1.0;
		FadeLastTime = Now;
		FadeSteadyFrames = (Step < 0.1) ? FadeSteadyFrames + 1 : 0;
		if (FadeSteadyFrames >= 15)
		{
			FadeStartTime = Now;
		}
	}
	const float Alpha = FadeStartTime < 0.0 ? 1.f : 1.f - FMath::Clamp(static_cast<float>((Now - FadeStartTime) / 1.6), 0.f, 1.f);
	FadeAlpha = Alpha;
	if (Alpha <= 0.f)
	{
		return;
	}
	FCanvasTileItem Black(FVector2D::ZeroVector, FVector2D(Canvas->ClipX, Canvas->ClipY), FLinearColor(0.f, 0.f, 0.f, Alpha * Alpha * (3.f - 2.f * Alpha)));
	Black.BlendMode = SE_BLEND_Translucent;
	Canvas->DrawItem(Black);
}

void ANVHUD::DrawScope(const ANVPlayerCharacter& Player)
{
	// Sniper scope: black mask outside a round eyepiece, soft dark rim, fine reticle with mil ticks.
	// Vertex-coloured triangles still need a texture to sample: the engine's white square.
	static TWeakObjectPtr<UTexture2D> WhiteTex;
	if (!WhiteTex.IsValid())
	{
		WhiteTex = LoadObject<UTexture2D>(nullptr, TEXT("/Engine/EngineResources/WhiteSquareTexture.WhiteSquareTexture"));
	}
	const FTexture* White = WhiteTex.IsValid() ? WhiteTex->GetResource() : nullptr;
	if (!White)
	{
		return;
	}
	const float W = Canvas->ClipX, H = Canvas->ClipY;
	const float CX = W * 0.5f, CY = H * 0.5f;
	const float R = H * 0.46f;
	const float Far = FMath::Sqrt(W * W + H * H);
	const int32 N = 96;
	TArray<FCanvasUVTri> Mask, Rim;
	Mask.Reserve(N * 2);
	Rim.Reserve(N * 2);
	const FLinearColor Black(0.f, 0.f, 0.f, 1.f);
	const FLinearColor Clear(0.f, 0.f, 0.f, 0.f);
	auto Tri = [](TArray<FCanvasUVTri>& Out, const FVector2D& A, const FVector2D& B, const FVector2D& C,
	              const FLinearColor& CA, const FLinearColor& CB, const FLinearColor& CC)
	{
		FCanvasUVTri T;
		T.V0_Pos = A; T.V1_Pos = B; T.V2_Pos = C;
		T.V0_Color = CA; T.V1_Color = CB; T.V2_Color = CC;
		Out.Add(T);
	};
	for (int32 i = 0; i < N; ++i)
	{
		const float A0 = 2.f * PI * i / N, A1 = 2.f * PI * (i + 1) / N;
		const FVector2D D0(FMath::Cos(A0), FMath::Sin(A0)), D1(FMath::Cos(A1), FMath::Sin(A1));
		const FVector2D C(CX, CY);
		// opaque mask from the eyepiece edge out past the screen corners
		Tri(Mask, C + D0 * R, C + D0 * Far, C + D1 * Far, Black, Black, Black);
		Tri(Mask, C + D0 * R, C + D1 * Far, C + D1 * R, Black, Black, Black);
		// rim shading: fades from clear (inside) to black at the edge
		const float Ri = R * 0.86f;
		Tri(Rim, C + D0 * Ri, C + D0 * R, C + D1 * R, Clear, Black, Black);
		Tri(Rim, C + D0 * Ri, C + D1 * R, C + D1 * Ri, Clear, Black, Clear);
	}
	FCanvasTriangleItem MaskItem(Mask, White);
	MaskItem.BlendMode = SE_BLEND_Translucent;
	Canvas->DrawItem(MaskItem);
	FCanvasTriangleItem RimItem(Rim, White);
	RimItem.BlendMode = SE_BLEND_Translucent;
	Canvas->DrawItem(RimItem);

	// Thin lines in a light grey so they read against a night city; heavy outer posts in black.
	const FLinearColor Ret(0.85f, 0.9f, 0.95f, 0.75f);
	const FLinearColor Post(0.01f, 0.01f, 0.01f, 0.95f);
	const FLinearColor Glow(1.f, 0.25f, 0.2f, 0.95f);
	const float Gap = R * 0.04f;
	// thick outer posts, thin centre lines
	DrawLine(CX - R, CY, CX - R * 0.45f, CY, Post, 5.f);
	DrawLine(CX + R * 0.45f, CY, CX + R, CY, Post, 5.f);
	DrawLine(CX, CY + R * 0.45f, CX, CY + R, Post, 5.f);
	DrawLine(CX - R * 0.45f, CY, CX - Gap, CY, Ret, 1.2f);
	DrawLine(CX + Gap, CY, CX + R * 0.45f, CY, Ret, 1.2f);
	DrawLine(CX, CY - R, CX, CY - Gap, Ret, 1.2f);
	DrawLine(CX, CY + Gap, CX, CY + R * 0.45f, Ret, 1.2f);
	for (int32 k = 1; k <= 4; ++k)
	{
		const float O = R * 0.09f * k;
		const float T = (k % 2 == 0) ? R * 0.025f : R * 0.015f;
		DrawLine(CX - O, CY - T, CX - O, CY + T, Ret, 1.2f);
		DrawLine(CX + O, CY - T, CX + O, CY + T, Ret, 1.2f);
		DrawLine(CX - T, CY + O, CX + T, CY + O, Ret, 1.2f);
	}
	// illuminated centre dot: this is exactly where the round goes
	DrawRect(Glow, CX - 1.5f, CY - 1.5f, 3.f, 3.f);
	(void)Player;
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

void ANVHUD::UpdateSubtitleQueue()
{
	// Advance the subtitle queue when the current line has finished. Comms-flagged lines open a comms card instead.
	const float Now = GetWorld()->GetTimeSeconds();
	while (Now >= SubtitleUntil && SubtitleQueue.Num() > 0)
	{
		const FNVSubtitleLine Line = SubtitleQueue[0];
		SubtitleQueue.RemoveAt(0);
		if (Line.bAsComms)
		{
			FNVCommsMessage M;
			M.Sender = Line.Speaker;
			M.Channel = Line.Channel;
			M.Body = Line.Text;
			M.Duration = FMath::Max(Line.Duration + 2.f, 5.f);
			M.Voice = Line.Voice;
			PushMessage(M);
			SubtitleUntil = Now + Line.Duration;
			continue;
		}
		ShowSubtitle(Line.Speaker, Line.Text, Line.Duration);
		if (Line.Voice)
		{
			UGameplayStatics::PlaySound2D(this, Line.Voice, VoiceVolume);
		}
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

void ANVHUD::DrawDetection()
{
	// Threat text is drawn by GHOST-OS; the detection meter stays here, tight to the reticle.
	const float Now = GetWorld()->GetTimeSeconds();
	const float S = Canvas->ClipY / 1080.f;
	const float CX = Canvas->ClipX * 0.5f, CY = Canvas->ClipY * 0.5f;
	if (Now - DetectionSetAt < 0.25f && Detection > 0.01f)
	{
		const float BW = 90.f * S, BH = 4.f * S;
		DrawRect(FLinearColor(0.f, 0.f, 0.f, 0.5f), CX - BW * 0.5f, CY - 48.f * S, BW, BH);
		DrawRect(Detection >= 1.f ? FLinearColor(1.f, 0.25f, 0.2f, 1.f) : WarningColor, CX - BW * 0.5f, CY - 48.f * S, BW * Detection, BH);
	}
}