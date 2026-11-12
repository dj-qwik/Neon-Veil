#pragma once

#include "CoreMinimal.h"
#include "GameFramework/PlayerController.h"
#include "NVPlayerController.generated.h"

UCLASS()
class NEONVEIL_API ANVPlayerController : public APlayerController
{
	GENERATED_BODY()

public:
	ANVPlayerController();

protected:
	virtual void SetupInputComponent() override;

private:
	/** F10: quit to desktop. Interim until the pause menu exists (the game captures the mouse). */
	void QuitToDesktop();
};
