#include "Core/NVGameplayTags.h"

namespace NVTags
{
	UE_DEFINE_GAMEPLAY_TAG_COMMENT(Damage_Ballistic, "NV.Damage.Ballistic", "Bullet damage");
	UE_DEFINE_GAMEPLAY_TAG_COMMENT(Damage_Melee, "NV.Damage.Melee", "Shock baton and other melee");
	UE_DEFINE_GAMEPLAY_TAG_COMMENT(Damage_Training, "NV.Damage.Training", "Non-lethal simulation rounds");

	UE_DEFINE_GAMEPLAY_TAG_COMMENT(HitZone_WeakPoint, "NV.HitZone.WeakPoint", "Component tag marking a weak point");

	UE_DEFINE_GAMEPLAY_TAG_COMMENT(Ability_OpticalDisruption, "NV.Ability.OpticalDisruption", "Short optical cloak");
	UE_DEFINE_GAMEPLAY_TAG_COMMENT(Ability_KineticShield, "NV.Ability.KineticShield", "Shield burst: blocks incoming damage briefly");
	UE_DEFINE_GAMEPLAY_TAG_COMMENT(Ability_DroneUplink, "NV.Ability.DroneUplink", "Recon drone that marks hostiles");

	UE_DEFINE_GAMEPLAY_TAG_COMMENT(Event_M00_SecurityArchCleared, "NV.Event.M00.SecurityArchCleared", "M00-O01 completion");
	UE_DEFINE_GAMEPLAY_TAG_COMMENT(Event_M00_CalibrationComplete, "NV.Event.M00.CalibrationComplete", "M00-O02 completion");
	UE_DEFINE_GAMEPLAY_TAG_COMMENT(Event_M00_HoloTableReviewed, "NV.Event.M00.HoloTableReviewed", "M00-O03 completion");
	UE_DEFINE_GAMEPLAY_TAG_COMMENT(Event_M00_BiometricScanStarted, "NV.Event.M00.BiometricScanStarted", "M00-O04 completion");
	UE_DEFINE_GAMEPLAY_TAG_COMMENT(Event_M00_SurveillanceBypassed, "NV.Event.M00.SurveillanceBypassed", "Simulation: reached the terminal past the surveillance cone");

	UE_DEFINE_GAMEPLAY_TAG_COMMENT(Event_M00P_EnteredTransitHub, "NV.Event.M00P.EnteredTransitHub", "Prologue: walked into the Crown Line transit hub");
	UE_DEFINE_GAMEPLAY_TAG_COMMENT(Event_M00P_LiftArrived, "NV.Event.M00P.LiftArrived", "Prologue: lift reached the concourse level");
	UE_DEFINE_GAMEPLAY_TAG_COMMENT(Event_M00P_DeparturesChecked, "NV.Event.M00P.DeparturesChecked", "Prologue: checked the departure board (opens the platform gates)");
	UE_DEFINE_GAMEPLAY_TAG_COMMENT(Event_M00P_PlatformReached, "NV.Event.M00P.PlatformReached", "Prologue: reached the Crown Line boarding point");
	UE_DEFINE_GAMEPLAY_TAG_COMMENT(Event_M00P_TramBoarded, "NV.Event.M00P.TramBoarded", "Prologue: boarded the tram (ends the prologue)");
	UE_DEFINE_GAMEPLAY_TAG_COMMENT(Event_M00P_TutorialDone, "NV.Event.M00P.TutorialDone", "Prologue: a movement tutorial step was completed");
	UE_DEFINE_GAMEPLAY_TAG_COMMENT(Event_M00P_PassCollected, "NV.Event.M00P.PassCollected", "Prologue: picked up the crew pass in the north service corridor");
	UE_DEFINE_GAMEPLAY_TAG_COMMENT(Event_M00P_PassRegistered, "NV.Event.M00P.PassRegistered", "Prologue: registered the pass at the east wing security desk");
	UE_DEFINE_GAMEPLAY_TAG_COMMENT(Event_M00P_PlatformPowered, "NV.Event.M00P.PlatformPowered", "Prologue: restored Platform One power from the Platform Two control room");
	UE_DEFINE_GAMEPLAY_TAG_COMMENT(Event_M00P_GearCollected, "NV.Event.M00P.GearCollected", "Prologue: collected gear from the Platform One crew room");

	UE_DEFINE_GAMEPLAY_TAG_COMMENT(Event_M01_EmergencyDoorReached, "NV.Event.M01.EmergencyDoorReached", "M01-O01: drones down, through the emergency door");
	UE_DEFINE_GAMEPLAY_TAG_COMMENT(Event_M01_AlternateExit, "NV.Event.M01.AlternateExit", "M01-O02: turret rerouted or service bypass traversed");
	UE_DEFINE_GAMEPLAY_TAG_COMMENT(Event_M01_ShaftEscaped, "NV.Event.M01.ShaftEscaped", "M01-O03: reached the bottom of the transit shaft");
	UE_DEFINE_GAMEPLAY_TAG_COMMENT(Event_M01_IdentityRecovered, "NV.Event.M01.IdentityRecovered", "M01-O04: damaged agency tag collected");
	UE_DEFINE_GAMEPLAY_TAG_COMMENT(Event_M01_SpillwayReached, "NV.Event.M01.SpillwayReached", "M01-O05: out through the drainage spillway");
	UE_DEFINE_GAMEPLAY_TAG_COMMENT(Event_M01_DroneDown, "NV.Event.M01.DroneDown", "M01 beat: a security drone destroyed");
	UE_DEFINE_GAMEPLAY_TAG_COMMENT(Event_M01_TurretRerouted, "NV.Event.M01.TurretRerouted", "M01 beat: artery sentry turret hacked");
	UE_DEFINE_GAMEPLAY_TAG_COMMENT(Event_M01_LiftCalled, "NV.Event.M01.LiftCalled", "M01 beat: service lift boarded");
	UE_DEFINE_GAMEPLAY_TAG_COMMENT(Event_M01_ReclamationStart, "NV.Event.M01.ReclamationStart", "M01 beat: entered the medical reclamation suite");
	UE_DEFINE_GAMEPLAY_TAG_COMMENT(Event_M01_PlayerKilled, "NV.Event.M01.PlayerKilled", "Player died (checkpoint reload follows)");
}
