#include "Core/NVPlayerController.h"
#include "Debug/NVCheatManager.h"
#include "NeonVeil.h"
#include "Components/InputComponent.h"
#include "InputCoreTypes.h"
#include "Kismet/GameplayStatics.h"
#include "Kismet/KismetSystemLibrary.h"

ANVPlayerController::ANVPlayerController()
{
	CheatClass = UNVCheatManager::StaticClass();
}

const TArray<FText>& ANVPlayerController::GetPauseItems()
{
	static const TArray<FText> Items = {
		NSLOCTEXT("NeonVeil", "PauseResume", "Resume"),
		NSLOCTEXT("NeonVeil", "PauseRestart", "Restart Mission"),
		NSLOCTEXT("NeonVeil", "PauseQuit", "Quit to Desktop"),
	};
	return Items;
}

void ANVPlayerController::SetupInputComponent()
{
	Super::SetupInputComponent();
	if (!InputComponent)
	{
		return;
	}
	auto Bind = [this](const FKey& Key, void (ANVPlayerController::*Fn)())
	{
		FInputKeyBinding& B = InputComponent->BindKey(Key, IE_Pressed, this, Fn);
		B.bExecuteWhenPaused = true;
		B.bConsumeInput = false;
	};
	Bind(EKeys::Escape, &ANVPlayerController::TogglePauseMenu);
	Bind(EKeys::P, &ANVPlayerController::TogglePauseMenu);
	Bind(EKeys::Gamepad_Special_Right, &ANVPlayerController::TogglePauseMenu);
	Bind(EKeys::Up, &ANVPlayerController::MenuUp);
	Bind(EKeys::W, &ANVPlayerController::MenuUp);
	Bind(EKeys::Gamepad_DPad_Up, &ANVPlayerController::MenuUp);
	Bind(EKeys::Down, &ANVPlayerController::MenuDown);
	Bind(EKeys::S, &ANVPlayerController::MenuDown);
	Bind(EKeys::Gamepad_DPad_Down, &ANVPlayerController::MenuDown);
	Bind(EKeys::Enter, &ANVPlayerController::MenuConfirm);
	Bind(EKeys::SpaceBar, &ANVPlayerController::MenuConfirm);
	Bind(EKeys::Gamepad_FaceButton_Bottom, &ANVPlayerController::MenuConfirm);
	Bind(EKeys::LeftMouseButton, &ANVPlayerController::MenuClick);
	Bind(EKeys::F10, &ANVPlayerController::QuitToDesktop);
}

void ANVPlayerController::SetPauseMenuOpen(bool bOpen)
{
	if (bOpen == bPauseMenuOpen)
	{
		return;
	}
	bPauseMenuOpen = bOpen;
	PauseSelection = 0;
	SetPause(bOpen);
	bShowMouseCursor = bOpen;
	if (bOpen)
	{
		FInputModeGameAndUI Mode;
		Mode.SetHideCursorDuringCapture(false);
		SetInputMode(Mode);
	}
	else
	{
		SetInputMode(FInputModeGameOnly());
	}
	UE_LOG(LogNeonVeil, Log, TEXT("Pause menu %s"), bOpen ? TEXT("opened") : TEXT("closed"));
}

void ANVPlayerController::TogglePauseMenu()
{
	SetPauseMenuOpen(!bPauseMenuOpen);
}

void ANVPlayerController::MenuUp()
{
	if (bPauseMenuOpen)
	{
		PauseSelection = (PauseSelection + GetPauseItems().Num() - 1) % GetPauseItems().Num();
	}
}

void ANVPlayerController::MenuDown()
{
	if (bPauseMenuOpen)
	{
		PauseSelection = (PauseSelection + 1) % GetPauseItems().Num();
	}
}

void ANVPlayerController::MenuConfirm()
{
	if (bPauseMenuOpen)
	{
		Activate(PauseSelection);
	}
}

void ANVPlayerController::PlayerTick(float DeltaTime)
{
	Super::PlayerTick(DeltaTime);
	// Mouse hover selects (rects come from the HUD's last draw).
	float MX, MY;
	if (bPauseMenuOpen && GetMousePosition(MX, MY))
	{
		for (int32 i = 0; i < PauseItemRects.Num(); ++i)
		{
			if (PauseItemRects[i].IsInside(FVector2D(MX, MY)))
			{
				PauseSelection = i;
			}
		}
	}
}

void ANVPlayerController::MenuClick()
{
	float MX, MY;
	if (!bPauseMenuOpen || !GetMousePosition(MX, MY))
	{
		return;
	}
	for (int32 i = 0; i < PauseItemRects.Num(); ++i)
	{
		if (PauseItemRects[i].IsInside(FVector2D(MX, MY)))
		{
			Activate(i);
			return;
		}
	}
}

void ANVPlayerController::Activate(int32 Index)
{
	UE_LOG(LogNeonVeil, Log, TEXT("Pause menu: %s"), *GetPauseItems()[Index].ToString());
	switch (Index)
	{
	case 0:
		SetPauseMenuOpen(false);
		break;
	case 1:
		SetPauseMenuOpen(false);
		UGameplayStatics::OpenLevel(this, FName(*UGameplayStatics::GetCurrentLevelName(this)));
		break;
	default:
		QuitToDesktop();
		break;
	}
}

void ANVPlayerController::QuitToDesktop()
{
	UKismetSystemLibrary::QuitGame(this, this, EQuitPreference::Quit, false);
}
