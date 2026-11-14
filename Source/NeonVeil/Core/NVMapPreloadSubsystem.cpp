#include "Core/NVMapPreloadSubsystem.h"

#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "HAL/PlatformTime.h"
#include "UObject/Package.h"
#include "UObject/UObjectGlobals.h"
#include "NeonVeil.h"

UNVMapPreloadSubsystem* UNVMapPreloadSubsystem::Get(const UObject* WorldContext)
{
	const UWorld* World = WorldContext ? WorldContext->GetWorld() : nullptr;
	const UGameInstance* GI = World ? World->GetGameInstance() : nullptr;
	return GI ? GI->GetSubsystem<UNVMapPreloadSubsystem>() : nullptr;
}

void UNVMapPreloadSubsystem::Preload(const FString& MapPackageName)
{
	const UWorld* World = GetGameInstance() ? GetGameInstance()->GetWorld() : nullptr;
	if (MapPackageName.IsEmpty() || (World && World->IsPlayInEditor()))
	{
		return;
	}
	if (Pending == MapPackageName)
	{
		return;
	}
	Pending = MapPackageName;
	RequestTime = FPlatformTime::Seconds();
	TWeakObjectPtr<UNVMapPreloadSubsystem> WeakThis(this);
	LoadPackageAsync(MapPackageName, FLoadPackageAsyncDelegate::CreateLambda(
		[WeakThis](const FName& PackageName, UPackage* Package, EAsyncLoadingResult::Type Result)
		{
			if (UNVMapPreloadSubsystem* Self = WeakThis.Get())
			{
				if (Result == EAsyncLoadingResult::Succeeded && Package && Self->Pending == PackageName.ToString())
				{
					Self->PreloadedPackage = Package;
					UE_LOG(LogNeonVeil, Log, TEXT("Preloaded %s in %.1f s"), *PackageName.ToString(), FPlatformTime::Seconds() - Self->RequestTime);
				}
				else
				{
					UE_LOG(LogNeonVeil, Warning, TEXT("Preload of %s failed"), *PackageName.ToString());
				}
			}
		}));
	UE_LOG(LogNeonVeil, Log, TEXT("Preloading %s in the background"), *MapPackageName);
}

void UNVMapPreloadSubsystem::Release()
{
	PreloadedPackage = nullptr;
	Pending.Reset();
}
