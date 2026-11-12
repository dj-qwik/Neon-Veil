#pragma once

#include "CoreMinimal.h"
#include "GameFramework/HUD.h"
#include "UI/NVSubtitleLine.h"
#include "NVHUD.generated.h"

class ANVPlayerCharacter;
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

private:
	UFUNCTION()
	void HandleHitConfirmed(AActor* HitActor, bool bWeakPoint);

	UFUNCTION()
	void HandleObjectiveCompleted(FName ObjectiveID);

	void BindToPawn();
	void DrawReticle(const ANVPlayerCharacter& Player);
	void DrawHealth(const ANVPlayerCharacter& Player);
	void DrawAmmo(const ANVPlayerCharacter& Player);
	void DrawObjectives();
	void DrawPrompt(const ANVPlayerCharacter& Player);
	void DrawMessages();
	void DrawTextShadowed(const FString& Text, float X, float Y, const FLinearColor& Color, UFont* Font, float Scale = 1.f, bool bRightAlign = false);

	TWeakObjectPtr<ANVPlayerCharacter> BoundPawn;
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
