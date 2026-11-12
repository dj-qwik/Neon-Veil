"""Tune rain fields/materials in place. Edit TUNE and re-run. Report: Saved/NV_m9_rain_tune.txt"""
import unreal
TUNE = {
    "near": dict(opacity=0.9, emissive=6.0, width=(2.0, 3.5), length=(70, 130)),
    "mid": dict(opacity=0.6, emissive=4.0, width=(4.0, 7.0), length=(180, 320)),
}
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
MEL = unreal.MaterialEditingLibrary
EAL = unreal.EditorAssetLibrary
ART = "/Game/NeonVeil/Materials/Art"
out = []
for key, mi_name in (("near", "MI_NV_RainDrop_Near"), ("mid", "MI_NV_RainDrop_Mid")):
    t = TUNE[key]
    inst = unreal.load_asset(f"{ART}/{mi_name}")
    MEL.set_material_instance_scalar_parameter_value(inst, "Opacity", t["opacity"])
    MEL.set_material_instance_scalar_parameter_value(inst, "Emissive", t["emissive"])
    EAL.save_loaded_asset(inst, only_if_is_dirty=False)
for a in EAS.get_all_level_actors():
    if str(a.get_folder_path()) != "FX_Rain":
        continue
    t = TUNE["near" if a.get_actor_label().startswith("RainNear") else "mid"]
    a.set_editor_property("width_range", unreal.Vector2D(*t["width"]))
    a.set_editor_property("length_range", unreal.Vector2D(*t["length"]))
    l = a.get_actor_location()
    a.set_actor_location(unreal.Vector(l.x, l.y, l.z + 0.01), False, False)
    out.append(f"{a.get_actor_label()} instances={a.get_editor_property('streaks').get_instance_count()}")
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
with open(unreal.Paths.project_saved_dir() + "NV_m9_rain_tune.txt", "w", encoding="utf-8") as fh:
    fh.write(str(TUNE) + "\n" + "\n".join(out))
