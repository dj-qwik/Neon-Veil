#pragma once

#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "NVMapPreloadSubsystem.generated.h"

/**
 * Loads the next mission's map package in the background while the current map plays, so the hand-off
 * (OpenLevel from inside the prologue tram tunnel) finds the package already in memory and only has to
 * initialise the world. Skipped in PIE, where travel duplicates the editor package instead.
 */
UCLASS()
class NEONVEIL_API UNVMapPreloadSubsystem : public UGameInstanceSubsystem
{
	GENERATED_BODY()

public:
	static UNVMapPreloadSubsystem* Get(const UObject* WorldContext);

	/** Start an async load of the map package (long package name, e.g. /Game/Maps/L_Foo). */
	void Preload(const FString& MapPackageName);

	/** Drop the reference to a preloaded package (called when the next map starts). */
	void Release();

	bool IsReady() const { return PreloadedPackage != nullptr; }

private:
	UPROPERTY(Transient)
	TObjectPtr<UPackage> PreloadedPackage;

	FString Pending;
	double RequestTime = 0.0;
};
