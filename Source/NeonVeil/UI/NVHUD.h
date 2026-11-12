#pragma once

#include "CoreMinimal.h"
#include "GameFramework/HUD.h"
#include "UI/NVSubtitleLine.h"
#include "Abilities/NVAbilityComponent.h"
#include "NVHUD.generated.h"

class ANVPlayerCharacter;
class UNVHealthComponent;
class UFont;

/**
 * Gameplay HUD drawn on the canvas. Layout follows Bible §10:
 * health lower left, ammo lower right, objective top right, prompt center right, restrained reticle.
 * A UMG skin can replace this later without touching gameplay code.
 */
UCLASS()
class NEONVEIL_API ANVHUD : public AHUD
{
	GENERATED_BODY()

public:
	ANVHUD();

	virtual void DrawHUD() override;
	virtual void BeginPlay() override;

	/** Brief on-screen notice ("Objective complete", "Checkpoint saved"). */
	UFUNCTION(BlueprintCallable, Category = "NeonVeil|HUD")
	void ShowNotice(const FText& Text, float Duration = 2.5f);

	/** Subtitle line with speaker label (Bible §10). */
	UFUNCTION(BlueprintCallable, Category = "NeonVeil|HUD")
	void ShowSubtitle(const FText& Speaker, const FText& Line, float Duration = 4.f);

	UFUNCTION(BlueprintCallable, Category = "NeonVeil|HUD")
	void SetHUDVisible(bool bVisible) { bHUDVisible = bVisible; }

	/** Plays lines one after another (each for its Duration), after anything already queued. */
	UFUNCTION(BlueprintCallable, Category = "NeonVeil|HUD")
	void QueueSubtitles(const TArray<FNVSubtitleLine>& Lines);

	/** Persistent instruction under the objectives (simulation prompts). Empty clears it. */
	UFUNCTION(BlueprintCallable, Category = "NeonVeil|HUD")
	void SetInstruction(const FText& Text) { InstructionText = Text; }

	/** Large centred title card, e.g. the end-of-mission card. */
	UFUNCTION(BlueprintCallable, Category = "NeonVeil|HUD")
	void ShowTitleCard(const FText& Title, const FText& Subtitle, float Duration = 5.f);

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "HUD")
	FLinearColor AccentColor = FLinearColor(0.35f, 0.9f, 1.f, 1.f); // controlled cyan

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "HUD")
	FLinearColor WarningColor = FLinearColor(1.f, 0.62f, 0.15f, 1.f); // emergency amber

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "HUD")
	FLinearColor TextColor = FLinearColor(0.92f, 0.95f, 0.97f, 1.f);

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "HUD")
	float SubtitleScale = 1.f;

	/** Global HUD text size multiplier (settings hook). Text is rendered at size, so it stays sharp. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "HUD", meta = (ClampMin = "0.75", ClampMax = "2.5"))
	float TextScale = 1.4f;

	/** Button names in gamepad prompts: PlayStation (Triangle, R3) or Xbox (Y, RS). Settings hook. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "HUD")
	bool bPlayStationGlyphs = true;

	/** Threat warning near the reticle (Bible §10 restrained threat indicator), e.g. "INCOMING VOLLEY". */
	UFUNCTION(BlueprintCallable, Category = "NeonVeil|HUD")
	void ShowThreat(const FText& Text, float Duration = 1.5f);

	/** Surveillance detection meter, 0..1. Set every frame while relevant; fades when not updated. */
	UFUNCTION(BlueprintCallable, Category = "NeonVeil|HUD")
	void SetDetection(float Amount);

	/** Prompt label for an action: "[E]" or "Triangle" depending on the last device used. */
	FString KeyLabel(FName Action) const;

	bool IsUsingGamepad() const { return bUsingGamepad; }

private:
	UFUNCTION()
	void HandleHitConfirmed(AActor* HitActor, bool bWeakPoint);

	UFUNCTION()
	void HandleObjectiveCompleted(FName ObjectiveID);

	UFUNCTION()
	void HandleMeleeHit(AActor* HitActor, bool bTakedown);

	UFUNCTION()
	void HandleAbilityFailed(FGameplayTag AbilityTag, ENVAbilityFailReason Reason);

	UFUNCTION()
	void HandleDamageBlocked(UNVHealthComponent* HealthComp, float BlockedAmount);

	void UpdateInputDevice();
	void DrawAbilities(const ANVPlayerCharacter& Player);
	void DrawAbilityOverlays(const ANVPlayerCharacter& Player);
	void DrawMarks(const ANVPlayerCharacter& Player);
	void DrawThreat();

	void BindToPawn();
	void DrawReticle(const ANVPlayerCharacter& Player);
	void DrawHealth(const ANVPlayerCharacter& Player);
	void DrawAmmo(const ANVPlayerCharacter& Player);
	void DrawObjectives();
	void DrawPrompt(const ANVPlayerCharacter& Player);
	void DrawMessages();
	void DrawTextShadowed(const FString& Text, float X, float Y, const FLinearColor& Color, UFont* Font, float Scale = 1.f, bool bRightAlign = false);
	void MeasureText(const FString& Text, UFont* Font, float Scale, float& OutW, float& OutH) const;
	struct FSlateFontInfo MakeFont(UFont* Font, float Scale) const;
	void DrawInstruction(float Y);

	TWeakObjectPtr<ANVPlayerCharacter> BoundPawn;
	bool bUsingGamepad = false;
	FText ThreatText;
	float ThreatUntil = -1.f;
	float Detection = 0.f;
	float DetectionSetAt = -10.f;
	float ShieldFlashTime = -10.f;
	bool bLastHitTakedown = false;
	float HealthTextTop = 0.f;
	float HitMarkerTime = -10.f;
	bool bHitMarkerWeak = false;

	FText NoticeText;
	float NoticeUntil = -1.f;

	FText SubtitleSpeaker;
	FText SubtitleLine;
	float SubtitleUntil = -1.f;

	bool bHUDVisible = true;

	TArray<FNVSubtitleLine> SubtitleQueue;
	FText InstructionText;
	FText TitleText;
	FText TitleSubText;
	float TitleUntil = -1.f;
	float TitleStart = -1.f;

	UPROPERTY(Transient)
	TObjectPtr<UFont> SmallFont;

	UPROPERTY(Transient)
	TObjectPtr<UFont> LargeFont;
};
