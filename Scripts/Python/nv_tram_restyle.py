"""Directorate restyle of the (local, gitignored) Dekogon subway material instances: no grime/trash, clean white
interior panels, graphite floor, titanium/graphite ends. Report: Saved/NV_tram_restyle.txt"""
import unreal
MEL = unreal.MaterialEditingLibrary
EAL = unreal.EditorAssetLibrary
out = []
DIRT0 = {"Mask 1 Multiply": 0.0, "Floor Trash Multiply": 0.0, "Directional Mutliply Mask": 0.0, "Mutliply Mask": 0.15}
TINT = {
    "MI_Wall_01": (1.55, 1.6, 1.65),
    "MI_Wallplastic_01": (1.45, 1.5, 1.55),
    "MI_Ceilingpanel_01": (1.2, 1.22, 1.25),
    "MI_Floor_01": (0.32, 0.34, 0.38),
    "MI_Plastic_01": (0.07, 0.075, 0.085),
}
for p in EAL.list_assets("/Game/SubwayTrain/Materials/Instances", recursive=True):
    m = unreal.load_asset(p.split(".")[0])
    if not isinstance(m, unreal.MaterialInstanceConstant):
        continue
    parent = m.get_editor_property("parent")
    try:
        names = [str(x) for x in MEL.get_scalar_parameter_names(m)]
    except Exception:
        names = []
    changed = []
    for k, v in DIRT0.items():
        if k in names:
            MEL.set_material_instance_scalar_parameter_value(m, k, v)
            changed.append(k)
    if m.get_name() in TINT:
        MEL.set_material_instance_vector_parameter_value(m, "Albedo Color Tint", unreal.LinearColor(*TINT[m.get_name()], 1.0))
        changed.append("tint")
    if changed:
        MEL.update_material_instance(m)
        EAL.save_loaded_asset(m)
        out.append("%s: %s" % (m.get_name(), changed))
open(unreal.Paths.project_saved_dir() + "NV_tram_restyle.txt", "w").write("\n".join(out))
