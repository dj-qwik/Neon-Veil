"""Crown surfaces -> Quixel Megascans (free on Fab, local only; textures under /Game/NeonVeil/Textures/Megascans are
gitignored). Floors (MI_DIR_PolishedStone) = Ziarat White Marble, walls/ceilings (MI_DIR_CeramicPanel) = Wall Paint.
Each new texture copies the compression/sRGB/VT settings of the texture it replaces so the master's samplers match.
Old values are saved to Saved/NV_megascans_backup.json (nv_megascans_revert.py restores them).
Report: Saved/NV_megascans_apply.txt"""
import json, unreal
EAL, MEL = unreal.EditorAssetLibrary, unreal.MaterialEditingLibrary
SRC = unreal.Paths.project_saved_dir() + "Megascans/packed/"
DST = "/Game/NeonVeil/Textures/Megascans"
ART = "/Game/NeonVeil/Materials/Art/"
out = []

def imp(name):
    t = unreal.AssetImportTask()
    t.filename = SRC + name + ".png"; t.destination_path = DST; t.destination_name = name
    t.automated = True; t.replace_existing = True; t.save = False
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])
    return unreal.load_asset(DST + "/" + name)

PLAN = {
    "MI_DIR_PolishedStone": ("ZiaratMarble",
        {"TileSize": 200.0, "PanelSize": 200.0, "SeamWidth": 0.35, "SeamDarken": 0.6, "Brightness": 0.82,
         "RoughnessMin": 0.04, "RoughnessMax": 0.22, "NormalStrength": 0.35},
        {"Tint": (0.9, 0.92, 0.96)}),
    "MI_DIR_CeramicPanel": ("WallPaint",
        {"TileSize": 82.0, "PanelSize": 400.0, "SeamWidth": 0.8, "SeamDarken": 0.4, "Brightness": 1.05,
         "RoughnessMin": 0.22, "RoughnessMax": 0.5, "NormalStrength": 0.55},
        {"Tint": (0.95, 0.97, 1.0)}),
}
backup = {}
for mi_name, (ms, scalars, vectors) in PLAN.items():
    mi = unreal.load_asset(ART + mi_name)
    old_tex = {str(v.parameter_info.name): v.parameter_value for v in mi.get_editor_property("texture_parameter_values")}
    backup[mi_name] = {
        "tex": {k: v.get_path_name() for k, v in old_tex.items() if v},
        "s": {str(v.parameter_info.name): v.parameter_value for v in mi.get_editor_property("scalar_parameter_values")},
        "v": {str(v.parameter_info.name): [v.parameter_value.r, v.parameter_value.g, v.parameter_value.b] for v in mi.get_editor_property("vector_parameter_values")},
    }
    for slot, suffix in (("BaseColor", "D"), ("Normal", "N"), ("ORM", "ORM")):
        t = imp("T_MS_%s_%s" % (ms, suffix))
        ref = old_tex.get(slot)
        if ref:
            for p in ("compression_settings", "srgb", "virtual_texture_streaming", "lod_group"):
                t.set_editor_property(p, ref.get_editor_property(p))
        t.set_editor_property("max_texture_size", 2048)
        EAL.save_loaded_asset(t)
        MEL.set_material_instance_texture_parameter_value(mi, slot, t)
        out.append("%s.%s <- %s (%s, vt=%s)" % (mi_name, slot, t.get_name(), str(t.get_editor_property("compression_settings")).split(".")[-1],
                                              t.get_editor_property("virtual_texture_streaming")))
    for k, v in scalars.items():
        MEL.set_material_instance_scalar_parameter_value(mi, k, v)
    for k, v in vectors.items():
        MEL.set_material_instance_vector_parameter_value(mi, k, unreal.LinearColor(*v, 1.0))
    MEL.update_material_instance(mi)
    EAL.save_loaded_asset(mi, only_if_is_dirty=False)
bp = unreal.Paths.project_saved_dir() + "NV_megascans_backup.json"
import os
if not os.path.exists(bp):
    json.dump(backup, open(bp, "w"), indent=1)
    out.append("backup written")
open(unreal.Paths.project_saved_dir() + "NV_megascans_apply.txt", "w").write("\n".join(out))
