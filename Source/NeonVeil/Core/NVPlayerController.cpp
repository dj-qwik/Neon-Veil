#include "Core/NVPlayerController.h"
#include "Debug/NVCheatManager.h"
#include "Components/InputComponent.h"
#include "InputCoreTypes.h"
#include "Kismet/KismetSystemLibrary.h"

ANVPlayerController::ANVPlayerController()
{
	CheatClass = UNVCheatManager::StaticClass();
}

void ANVPlayerController::SetupInputComponent()
{
	Super::SetupInputComponent();
	if (InputComponent)
	{
		InputComponent->BindKey(EKeys::F10, IE_Pressed, this, &ANVPlayerController::QuitToDesktop);
	}
}

void ANVPlayerController::QuitToDesktop()
{
	UKismetSystemLibrary::QuitGame(this, this, EQuitPreference::Quit, false);
}
