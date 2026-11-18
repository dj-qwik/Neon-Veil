#include "Core/NVPlayerController.h"
#include "Debug/NVCheatManager.h"
#include "NeonVeil.h"
#include "Components/InputComponent.h"
#include "InputCoreTypes.h"
#include "Kismet/GameplayStatics.h"
#include "Kismet/KismetSystemLibrary.h"
#include "UI/NVMenuShell.h"

ANVPlayerController::ANVPlayerController()
{
	CheatClass = UNVCheatManager::StaticClass();
}

const TArray<FText>& ANVPlayerController::GetPauseItems()
{
	static const TArray<FText> Items = {
		NSLOCTEXT("NeonVeil", "PauseResume", "Resume"),
		NSLOCTEXT("NeonVeil", "PauseOptions", "Options"),
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
	Bind(EKeys::Q, &ANVPlayerController::MenuPrevTab);
	Bind(EKeys::Gamepad_LeftShoulder, &ANVPlayerController::MenuPrevTab);
	Bind(EKeys::E, &ANVPlayerController::MenuNextTab);
	Bind(EKeys::Gamepad_RightShoulder, &ANVPlayerController::MenuNextTab);
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
	MenuTab = 0;
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
	if (bPauseMenuOpen && MenuTab == 0)
	{
		PauseSelection = (PauseSelection + GetPauseItems().Num() - 1) % GetPauseItems().Num();
	}
}

void ANVPlayerController::MenuDown()
{
	if (bPauseMenuOpen && MenuTab == 0)
	{
		PauseSelection = (PauseSelection + 1) % GetPauseItems().Num();
	}
}

void ANVPlayerController::MenuConfirm()
{
	if (bPauseMenuOpen && MenuTab == 0)
	{
		Activate(PauseSelection);
	}
}

void ANVPlayerController::MenuPrevTab()
{
	if (bPauseMenuOpen)
	{
		SetMenuTab(MenuTab - 1);
	}
}

void ANVPlayerController::MenuNextTab()
{
	if (bPauseMenuOpen)
	{
		SetMenuTab(MenuTab + 1);
	}
}

void ANVPlayerController::SetMenuTab(int32 Tab)
{
	const int32 N = FMath::Max(1, NVUI::MenuPages().Num());
	MenuTab = ((Tab % N) + N) % N;
}

void ANVPlayerController::SetPauseSelection(int32 Index)
{
	if (GetPauseItems().IsValidIndex(Index))
	{
		PauseSelection = Index;
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
		// jump to the OPTIONS tab
		for (int32 i = 0; i < NVUI::MenuPages().Num(); ++i)
		{
			if (NVUI::MenuPages()[i].Id == FName(TEXT("Options")))
			{
				SetMenuTab(i);
			}
		}
		break;
	case 2:
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
