"""Veyra Central exterior: the hub's upper facade (rows 2+, above the lobby) used the tram-station trim material, which
read as a huge pale peach wall that washed out the street. Give it a dark night-glass variant so the neon bands and
signage carry the building. Rows 0-1 (the lobby walls, also seen from inside) keep the original.
Args: [k] [save] - k scales the darkness (default 0.7). Report: Saved/NV_hub_facade_night.txt"""
import unreal, sys
args = sys.argv[2:]
k = float(args[0]) if args and args[0] != "save" else 0.7
save = "save" in args
OUT = []
EAL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary
DIR = "/Game/NeonVeil/Materials/Prologue"
NAME = "MI_NV_HubFacade_Night"
path = f"{DIR}/{NAME}"
if EAL.does_asset_exist(path):
    mi = EAL.load_asset(path)
else:
    mi = unreal.AssetToolsHelpers.get_asset_tools().create_asset(NAME, DIR, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    MEL.set_material_instance_parent(mi, unreal.load_object(None, "/Game/SciFiTramStation/Materials/M_Trim_B.M_Trim_B"))
MEL.set_material_instance_vector_parameter_value(mi, "Color1", unreal.LinearColor(0.045 * k, 0.055 * k, 0.07 * k, 1))
MEL.set_material_instance_vector_parameter_value(mi, "Color2", unreal.LinearColor(0.012 * k, 0.014 * k, 0.02 * k, 1))
MEL.set_material_instance_vector_parameter_value(mi, "Emissive_color", unreal.LinearColor(0, 0, 0, 1))
MEL.update_material_instance(mi)
EAL.save_loaded_asset(mi)
n = 0
for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
    lab = a.get_actor_label()
    if not lab.startswith("Hub_Facade_"):
        continue
    try:
        row = int(lab.split("_")[2])
    except ValueError:
        continue
    if row < 2:
        continue
    for c in a.get_components_by_class(unreal.StaticMeshComponent):
        for i in range(c.get_num_materials()):
            c.set_material(i, mi)
    n += 1
OUT.append(f"night facade on {n} pieces, k={k}")
if save:
    unreal.EditorLoadingAndSavingUtils.save_current_level()
    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    OUT.append("saved")
open(unreal.Paths.project_saved_dir() + "NV_hub_facade_night.txt", "w").write("\n".join(OUT))
