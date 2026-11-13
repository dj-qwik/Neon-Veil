"""Tune the Megascans marble floor (calmer veins, less ripple). Report: Saved/NV_ms_tune.txt"""
import unreal
MEL = unreal.MaterialEditingLibrary
mi = unreal.load_asset("/Game/NeonVeil/Materials/Art/MI_DIR_PolishedStone")
for k, v in {"TileSize": 160.0, "PanelSize": 160.0, "SeamWidth": 0.3, "SeamDarken": 0.55, "Brightness": 1.05,
             "NormalStrength": 0.12, "RoughnessMin": 0.05, "RoughnessMax": 0.2}.items():
    MEL.set_material_instance_scalar_parameter_value(mi, k, v)
MEL.set_material_instance_vector_parameter_value(mi, "Tint", unreal.LinearColor(0.97, 0.98, 1.0, 1.0))
MEL.update_material_instance(mi)
unreal.EditorAssetLibrary.save_loaded_asset(mi, only_if_is_dirty=False)
open(unreal.Paths.project_saved_dir() + "NV_ms_tune.txt", "w").write("ok")
