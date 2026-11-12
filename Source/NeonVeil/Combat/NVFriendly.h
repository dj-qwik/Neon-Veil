#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"

/**
 * Friendly-fire safety. Actors tagged "Friendly" (M00 Directorate guards) can't be shot, struck or
 * marked by Ghost-7: the weapon simply doesn't fire while one is in the sights.
 */
namespace NVFriendly
{
	inline const FName Tag(TEXT("Friendly"));

	inline bool IsFriendly(const AActor* Actor)
	{
		return Actor && Actor->ActorHasTag(Tag);
	}
}
