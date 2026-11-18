#include "Core/NVOptions.h"
#include "Character/NVPlayerCharacter.h"
#include "UI/NVHUD.h"
#include "UI/NVUIStyle.h"
#include "NeonVeil.h"

#include "AudioDevice.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "GameFramework/GameUserSettings.h"
#include "GameFramework/PlayerController.h"
#include "HAL/IConsoleManager.h"
#include "Kismet/KismetSystemLibrary.h"
#include "Misc/ConfigCacheIni.h"
#include "Sound/AudioSettings.h"
#include "Sound/SoundClass.h"

namespace
{
	const TCHAR* Section = TEXT("NeonVeil.Options");

	// Music and dialogue assets carry these classes (see Scripts/Python/nv_audio_classes.py); everything else plays
	// through the engine's default class, which is the "effects" slider.
	USoundClass* MusicClass()
	{
		static TWeakObjectPtr<USoundClass> C;
		if (!C.IsValid())
		{
			C = LoadObject<USoundClass>(nullptr, TEXT("/Game/NeonVeil/Audio/Mix/SC_NV_Music.SC_NV_Music"));
		}
		return C.Get();
	}
	USoundClass* VoiceClass()
	{
		static TWeakObjectPtr<USoundClass> C;
		if (!C.IsValid())
		{
			C = LoadObject<USoundClass>(nullptr, TEXT("/Game/NeonVeil/Audio/Mix/SC_NV_Voice.SC_NV_Voice"));
		}
		return C.Get();
	}
	USoundClass* EffectsClass()
	{
		static TWeakObjectPtr<USoundClass> C;
		if (!C.IsValid())
		{
			C = Cast<USoundClass>(GetDefault<UAudioSettings>()->DefaultSoundClassName.TryLoad());
		}
		return C.Get();
	}

	void ReadF(const TCHAR* Key, float& V)
	{
		GConfig->GetFloat(Section, Key, V, GGameUserSettingsIni);
	}
	void ReadB(const TCHAR* Key, bool& V)
	{
		GConfig->GetBool(Section, Key, V, GGameUserSettingsIni);
	}

	UGameUserSettings* GUS()
	{
		return GEngine ? GEngine->GetGameUserSettings() : nullptr;
	}
	void Commit()
	{
		if (UGameUserSettings* S = GUS())
		{
			S->ApplySettings(false);
			S->SaveSettings();
		}
	}
}

FNVOptions& FNVOptions::Get()
{
	static FNVOptions O;
	static bool bLoaded = false;
	if (!bLoaded)
	{
		bLoaded = true;
		O.Load();
	}
	return O;
}

void FNVOptions::Load()
{
	if (!GConfig)
	{
		return;
	}
	ReadF(TEXT("LookSensitivity"), LookSensitivity);
	ReadB(TEXT("InvertY"), bInvertY);
	ReadF(TEXT("FieldOfView"), FieldOfView);
	ReadB(TEXT("ToggleSprint"), bToggleSprint);
	ReadB(TEXT("ToggleCrouch"), bToggleCrouch);
	ReadB(TEXT("ToggleAim"), bToggleAim);
	ReadF(TEXT("MasterVolume"), MasterVolume);
	ReadF(TEXT("MusicVolume"), MusicVolume);
	ReadF(TEXT("VoiceVolume"), VoiceVolume);
	ReadF(TEXT("EffectsVolume"), EffectsVolume);
	ReadB(TEXT("Subtitles"), bSubtitles);
	ReadF(TEXT("TextScale"), TextScale);
	ReadB(TEXT("MotionBlur"), bMotionBlur);
	LookSensitivity = FMath::Clamp(LookSensitivity, 0.2f, 3.f);
	FieldOfView = FMath::Clamp(FieldOfView, 80.f, 110.f);
	TextScale = FMath::Clamp(TextScale, 0.8f, 1.4f);
}

void FNVOptions::Save() const
{
	if (!GConfig)
	{
		return;
	}
	GConfig->SetFloat(Section, TEXT("LookSensitivity"), LookSensitivity, GGameUserSettingsIni);
	GConfig->SetBool(Section, TEXT("InvertY"), bInvertY, GGameUserSettingsIni);
	GConfig->SetFloat(Section, TEXT("FieldOfView"), FieldOfView, GGameUserSettingsIni);
	GConfig->SetBool(Section, TEXT("ToggleSprint"), bToggleSprint, GGameUserSettingsIni);
	GConfig->SetBool(Section, TEXT("ToggleCrouch"), bToggleCrouch, GGameUserSettingsIni);
	GConfig->SetBool(Section, TEXT("ToggleAim"), bToggleAim, GGameUserSettingsIni);
	GConfig->SetFloat(Section, TEXT("MasterVolume"), MasterVolume, GGameUserSettingsIni);
	GConfig->SetFloat(Section, TEXT("MusicVolume"), MusicVolume, GGameUserSettingsIni);
	GConfig->SetFloat(Section, TEXT("VoiceVolume"), VoiceVolume, GGameUserSettingsIni);
	GConfig->SetFloat(Section, TEXT("EffectsVolume"), EffectsVolume, GGameUserSettingsIni);
	GConfig->SetBool(Section, TEXT("Subtitles"), bSubtitles, GGameUserSettingsIni);
	GConfig->SetFloat(Section, TEXT("TextScale"), TextScale, GGameUserSettingsIni);
	GConfig->SetBool(Section, TEXT("MotionBlur"), bMotionBlur, GGameUserSettingsIni);
	GConfig->Flush(false, GGameUserSettingsIni);
}

void FNVOptions::Apply(UWorld* World) const
{
	if (!World)
	{
		return;
	}
	ApplyAudio(World);
	if (APlayerController* PC = World->GetFirstPlayerController())
	{
		ApplyToPlayer(Cast<ANVPlayerCharacter>(PC->GetPawn()));
		ApplyToHUD(Cast<ANVHUD>(PC->GetHUD()));
	}
}

void FNVOptions::ApplyToPlayer(ANVPlayerCharacter* Player) const
{
	if (!Player)
	{
		return;
	}
	Player->SetLookSensitivity(LookSensitivity);
	Player->SetInvertY(bInvertY);
	Player->SetBaseFOV(FieldOfView);
	Player->SetToggleSettings(bToggleSprint, bToggleCrouch, bToggleAim);
}

void FNVOptions::ApplyAudio(UWorld* World) const
{
	if (World)
	{
		FAudioDeviceHandle Device = World->GetAudioDevice();
		if (Device.IsValid())
		{
			Device->SetTransientPrimaryVolume(MasterVolume);
		}
	}
	if (USoundClass* C = MusicClass())
	{
		C->Properties.Volume = MusicVolume;
	}
	if (USoundClass* C = VoiceClass())
	{
		C->Properties.Volume = VoiceVolume;
	}
	if (USoundClass* C = EffectsClass())
	{
		C->Properties.Volume = EffectsVolume;
	}
}

void FNVOptions::ApplyToHUD(ANVHUD* HUD) const
{
	NVUI::SetTextScale(TextScale);
	if (IConsoleVariable* MB = IConsoleManager::Get().FindConsoleVariable(TEXT("r.MotionBlurQuality")))
	{
		MB->Set(bMotionBlur ? 4 : 0, ECVF_SetByGameSetting);
	}
	if (HUD)
	{
		HUD->bSubtitlesEnabled = bSubtitles;
	}
}

// ---------------------------------------------------------------- display

int32 NVDisplay::GetQuality()
{
	UGameUserSettings* S = GUS();
	return S ? S->GetOverallScalabilityLevel() : 3;
}

void NVDisplay::SetQuality(int32 Level)
{
	if (UGameUserSettings* S = GUS())
	{
		S->SetOverallScalabilityLevel(FMath::Clamp(Level, 0, 3));
		Commit();
	}
}

int32 NVDisplay::GetWindowMode()
{
	UGameUserSettings* S = GUS();
	if (!S)
	{
		return 1;
	}
	switch (S->GetFullscreenMode())
	{
	case EWindowMode::Fullscreen: return 0;
	case EWindowMode::WindowedFullscreen: return 1;
	default: return 2;
	}
}

void NVDisplay::SetWindowMode(int32 Mode)
{
	if (UGameUserSettings* S = GUS())
	{
		S->SetFullscreenMode(Mode == 0 ? EWindowMode::Fullscreen : (Mode == 1 ? EWindowMode::WindowedFullscreen : EWindowMode::Windowed));
		if (Mode == 1)
		{
			S->SetScreenResolution(S->GetDesktopResolution());
		}
		Commit();
	}
}

TArray<FIntPoint> NVDisplay::GetResolutions()
{
	TArray<FIntPoint> Out;
	TArray<FIntPoint> Supported;
	if (UKismetSystemLibrary::GetSupportedFullscreenResolutions(Supported))
	{
		for (const FIntPoint& R : Supported)
		{
			if (R.X >= 1280 && R.Y >= 720)
			{
				Out.AddUnique(R);
			}
		}
	}
	if (Out.Num() == 0)
	{
		Out = { FIntPoint(1280, 720), FIntPoint(1600, 900), FIntPoint(1920, 1080), FIntPoint(2560, 1440) };
	}
	Out.Sort([](const FIntPoint& A, const FIntPoint& B) { return A.X * A.Y < B.X * B.Y; });
	return Out;
}

FIntPoint NVDisplay::GetResolution()
{
	UGameUserSettings* S = GUS();
	return S ? S->GetScreenResolution() : FIntPoint(1920, 1080);
}

void NVDisplay::SetResolution(FIntPoint Res)
{
	if (UGameUserSettings* S = GUS())
	{
		S->SetScreenResolution(Res);
		Commit();
	}
}

bool NVDisplay::GetVSync()
{
	UGameUserSettings* S = GUS();
	return S && S->IsVSyncEnabled();
}

void NVDisplay::SetVSync(bool bOn)
{
	if (UGameUserSettings* S = GUS())
	{
		S->SetVSyncEnabled(bOn);
		Commit();
	}
}

float NVDisplay::GetFrameLimit()
{
	UGameUserSettings* S = GUS();
	return S ? S->GetFrameRateLimit() : 0.f;
}

void NVDisplay::SetFrameLimit(float Fps)
{
	if (UGameUserSettings* S = GUS())
	{
		S->SetFrameRateLimit(Fps);
		Commit();
	}
}

float NVDisplay::GetResolutionScale()
{
	UGameUserSettings* S = GUS();
	return S ? S->GetResolutionScaleNormalized() : 1.f;
}

float NVDisplay::GetResolutionScalePercent()
{
	UGameUserSettings* S = GUS();
	if (!S)
	{
		return 100.f;
	}
	float Norm = 1.f, Value = 100.f, Min = 50.f, Max = 100.f;
	S->GetResolutionScaleInformationEx(Norm, Value, Min, Max);
	return Value;
}

void NVDisplay::SetResolutionScale(float Scale)
{
	if (UGameUserSettings* S = GUS())
	{
		S->SetResolutionScaleNormalized(FMath::Clamp(Scale, 0.f, 1.f));
		Commit();
	}
}
