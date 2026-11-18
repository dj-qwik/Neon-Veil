#pragma once

#include "CoreMinimal.h"

class UWorld;
class ANVPlayerCharacter;
class ANVHUD;

/**
 * Player options (controls, audio, gameplay). Display options live in UGameUserSettings; everything else is kept in
 * GameUserSettings.ini under [NeonVeil.Options] so it survives restarts and applies to every map.
 */
struct NEONVEIL_API FNVOptions
{
	// controls
	float LookSensitivity = 1.f;   // 0.2 .. 3
	bool bInvertY = false;
	float FieldOfView = 95.f;      // 80 .. 110 (horizontal)
	bool bToggleSprint = false;
	bool bToggleCrouch = true;
	bool bToggleAim = false;
	// audio (0 .. 1)
	float MasterVolume = 1.f;
	float MusicVolume = 0.8f;
	float VoiceVolume = 1.f;
	float EffectsVolume = 1.f;
	// gameplay / accessibility
	bool bSubtitles = true;
	float TextScale = 1.f;         // 0.8 .. 1.4 of the design size
	bool bMotionBlur = true;

	/** The live options (loaded from disk on first use). */
	static FNVOptions& Get();
	void Load();
	void Save() const;

	/** Pushes the options into the player, HUD and audio of World. Safe to call any time. */
	void Apply(UWorld* World) const;
	void ApplyToPlayer(ANVPlayerCharacter* Player) const;
	void ApplyAudio(UWorld* World) const;
	void ApplyToHUD(ANVHUD* HUD) const;
};

/** Display settings helpers over UGameUserSettings (applied and saved at once). */
namespace NVDisplay
{
	NEONVEIL_API int32 GetQuality();                    // 0 low .. 3 epic, -1 custom
	NEONVEIL_API void SetQuality(int32 Level);
	NEONVEIL_API int32 GetWindowMode();                 // 0 fullscreen, 1 borderless, 2 windowed
	NEONVEIL_API void SetWindowMode(int32 Mode);
	NEONVEIL_API TArray<FIntPoint> GetResolutions();
	NEONVEIL_API FIntPoint GetResolution();
	NEONVEIL_API void SetResolution(FIntPoint Res);
	NEONVEIL_API bool GetVSync();
	NEONVEIL_API void SetVSync(bool bOn);
	NEONVEIL_API float GetFrameLimit();                 // 0 = unlimited
	NEONVEIL_API void SetFrameLimit(float Fps);
	NEONVEIL_API float GetResolutionScale();            // normalized 0 .. 1
	NEONVEIL_API float GetResolutionScalePercent();     // the actual screen percentage
	NEONVEIL_API void SetResolutionScale(float Scale);
}
