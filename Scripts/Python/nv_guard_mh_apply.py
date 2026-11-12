"""Switch the three M00 guards to the shared MetaHuman look (BP_Guard: tactical outfit + P05 helmet).
Base mesh = UE5 Manny + ABP_Unarmed (hidden, drives locomotion); merc outfit parts cleared; battery pack kept.
Report: Saved/NV_guard_mh_apply.txt"""
import unreal
out = []
manny = unreal.load_asset("/Game/Characters/Mannequins/Meshes/SKM_Manny_Simple")
anim = unreal.load_object(None, "/Game/Characters/Mannequins/Anims/Unarmed/ABP_Unarmed.ABP_Unarmed_C")
look = unreal.load_object(None, "/Game/NeonVeil/Characters/GuardMH/Guard/BP_Guard.BP_Guard_C")
out.append("look class %s" % look)
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    if not isinstance(a, unreal.NVGuardCharacter):
        continue
    a.set_editor_property("body_mesh_asset", manny)
    a.set_editor_property("body_anim_class", anim)
    a.set_editor_property("outfit_parts", [])
    a.set_editor_property("helmet_mesh_asset", None)
    a.set_editor_property("appearance_class", look)
    a.set_actor_location(a.get_actor_location(), False, False)
    out.append("guard %s appearance %s" % (a.get_actor_label(), a.get_editor_property("appearance_class")))
unreal.EditorLevelLibrary.save_current_level()
open(unreal.Paths.project_saved_dir() + "NV_guard_mh_apply.txt", "w").write("\n".join(out))
