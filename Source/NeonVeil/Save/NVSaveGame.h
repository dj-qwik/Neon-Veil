#pragma once

#include "CoreMinimal.h"
#include "GameFramework/SaveGame.h"
#include "Combat/NVWeaponComponent.h"
#include "NVSaveGame.generated.h"

/** Mission checkpoint snapshot (Bible §11: checkpoint, inventory, upgrades, flags). */
UCLASS()
class NEONVEIL_API UNVSaveGame : public USaveGame
{
	GENERATED_BODY()

public:
	static constexpr int32 CurrentVersion = 1;

	UPROPERTY()
	int32 Version = CurrentVersion;

	/** Long package name of the map, e.g. /Game/NeonVeil/Maps/M00/L_M00_GlassCrown */
	UPROPERTY()
	FString MapPackage;

	UPROPERTY()
	FName MissionID;

	UPROPERTY()
	TArray<FName> CompletedObjectives;

	UPROPERTY()
	FName CheckpointID;

	UPROPERTY()
	float Health = 100.f;

	UPROPERTY()
	TArray<FNVWeaponSlot> WeaponSlots;

	UPROPERTY()
	int32 CurrentWeaponSlot = 0;

	/** Story/world flags for later missions (betrayal state, unlocked doors...). */
	UPROPERTY()
	TArray<FName> Flags;

	UPROPERTY()
	FDateTime SavedAt;
};
