"""Restore the Crown surface MIs saved by nv_megascans_apply.py. Report: Saved/NV_megascans_revert.txt"""
import json, unreal
MEL = unreal.MaterialEditingLibrary
b = json.load(open(unreal.Paths.project_saved_dir() + "NV_megascans_backup.json"))
for mi_name, d in b.items():
    mi = unreal.load_asset("/Game/NeonVeil/Materials/Art/" + mi_name)
    for k, p in d["tex"].items():
        MEL.set_material_instance_texture_parameter_value(mi, k, unreal.load_asset(p.split(".")[0]))
    for k, v in d["s"].items():
        MEL.set_material_instance_scalar_parameter_value(mi, k, v)
    for k, v in d["v"].items():
        MEL.set_material_instance_vector_parameter_value(mi, k, unreal.LinearColor(v[0], v[1], v[2], 1.0))
    MEL.update_material_instance(mi)
    unreal.EditorAssetLibrary.save_loaded_asset(mi, only_if_is_dirty=False)
open(unreal.Paths.project_saved_dir() + "NV_megascans_revert.txt", "w").write("reverted %s" % list(b))
