#include "Core/NVGameplayTags.h"

namespace NVTags
{
	UE_DEFINE_GAMEPLAY_TAG_COMMENT(Damage_Ballistic, "NV.Damage.Ballistic", "Bullet damage");
	UE_DEFINE_GAMEPLAY_TAG_COMMENT(Damage_Melee, "NV.Damage.Melee", "Shock baton and other melee");
	UE_DEFINE_GAMEPLAY_TAG_COMMENT(Damage_Training, "NV.Damage.Training", "Non-lethal simulation rounds");

	UE_DEFINE_GAMEPLAY_TAG_COMMENT(HitZone_WeakPoint, "NV.HitZone.WeakPoint", "Component tag marking a weak point");

	UE_DEFINE_GAMEPLAY_TAG_COMMENT(Event_M00_SecurityArchCleared, "NV.Event.M00.SecurityArchCleared", "M00-O01 completion");
	UE_DEFINE_GAMEPLAY_TAG_COMMENT(Event_M00_CalibrationComplete, "NV.Event.M00.CalibrationComplete", "M00-O02 completion");
	UE_DEFINE_GAMEPLAY_TAG_COMMENT(Event_M00_HoloTableReviewed, "NV.Event.M00.HoloTableReviewed", "M00-O03 completion");
	UE_DEFINE_GAMEPLAY_TAG_COMMENT(Event_M00_BiometricScanStarted, "NV.Event.M00.BiometricScanStarted", "M00-O04 completion");
}
