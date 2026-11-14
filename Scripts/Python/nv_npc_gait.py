"""Ambient NPCs: drive their bodies with the native foot-synced UNVBodyAnimInstance (unarmed set) instead of ABP_Unarmed,
and lift their walk speeds into the range the template walk cycle was authored for (~300 cm/s), so strides cover the
ground they travel instead of shuffling. Saves the prologue's external actors. Report: Saved/NV_npc_gait.txt"""
import unreal
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
LES = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
OUT = []
cls = unreal.NVBodyAnimInstance.static_class()
n = 0
for a in EAS.get_all_level_actors():
    if "NVNPC" not in [str(t) for t in a.tags] or not isinstance(a, unreal.NVGuardCharacter):
        continue
    old = a.get_editor_property("walk_speed")
    # original strolling speeds were 90-155; keep their ordering but in a 170-235 band
    new = max(170.0, min(235.0, 110.0 + old * 0.85)) if old < 165.0 else old
    a.set_editor_property("walk_speed", new)
    a.set_editor_property("body_anim_class", cls)
    # Fixed (reference-pose) bounds: the computed pose bounds trailed ~1 m behind walking NPCs, so occlusion culling
    # popped them out of view behind kiosks and pillars while they were in plain sight.
    m = a.get_editor_property("mesh")
    m.set_editor_property("component_use_fixed_skel_bounds", True)
    m.set_editor_property("bounds_scale", 1.2)
    OUT.append(f"{a.get_actor_label()}: speed {old:.0f} -> {new:.0f}")
    n += 1
LES.save_current_level()
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
OUT.insert(0, f"npcs updated: {n}")
open(unreal.Paths.project_saved_dir() + "NV_npc_gait.txt", "w").write("\n".join(OUT))
