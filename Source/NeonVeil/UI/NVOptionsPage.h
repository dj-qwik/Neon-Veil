#pragma once

#include "CoreMinimal.h"
#include "UI/NVMenuShell.h"

namespace NVUI
{
	/** OPTIONS tab of the GHOST-OS menu: controls, gameplay, audio and display. Changes apply and save at once. */
	TSharedRef<SWidget> BuildOptionsPage(const FNVMenuContext& Ctx);
}
