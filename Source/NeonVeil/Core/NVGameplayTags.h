#pragma once

#include "NativeGameplayTags.h"

// Native gameplay tags shared by C++ systems. Mission-specific tags live in Config/Tags.
namespace NVTags
{
	// Damage types
	NEONVEIL_API UE_DECLARE_GAMEPLAY_TAG_EXTERN(Damage_Ballistic);
	NEONVEIL_API UE_DECLARE_GAMEPLAY_TAG_EXTERN(Damage_Melee);
	NEONVEIL_API UE_DECLARE_GAMEPLAY_TAG_EXTERN(Damage_Training);

	// Hit zones
	NEONVEIL_API UE_DECLARE_GAMEPLAY_TAG_EXTERN(HitZone_WeakPoint);

	// Cyberware abilities (Bible §9)
	NEONVEIL_API UE_DECLARE_GAMEPLAY_TAG_EXTERN(Ability_OpticalDisruption);
	NEONVEIL_API UE_DECLARE_GAMEPLAY_TAG_EXTERN(Ability_KineticShield);
	NEONVEIL_API UE_DECLARE_GAMEPLAY_TAG_EXTERN(Ability_DroneUplink);

	// Objective events (M00)
	NEONVEIL_API UE_DECLARE_GAMEPLAY_TAG_EXTERN(Event_M00_SecurityArchCleared);
	NEONVEIL_API UE_DECLARE_GAMEPLAY_TAG_EXTERN(Event_M00_CalibrationComplete);
	NEONVEIL_API UE_DECLARE_GAMEPLAY_TAG_EXTERN(Event_M00_HoloTableReviewed);
	NEONVEIL_API UE_DECLARE_GAMEPLAY_TAG_EXTERN(Event_M00_BiometricScanStarted);
	NEONVEIL_API UE_DECLARE_GAMEPLAY_TAG_EXTERN(Event_M00_SurveillanceBypassed);
}
