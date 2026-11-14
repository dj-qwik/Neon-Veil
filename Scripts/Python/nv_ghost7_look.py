"""Ghost-7 third-person body: Retro Futuristic Soldier (Fab, Red Mallet Studio; local only, gitignored).
 - Its mesh ships with its own copy of the Manny skeleton: mark the two skeletons compatible so Ghost's existing
   ABP_Unarmed (project Manny) drives it with no retargeting.
 - MI_NV_Ghost7: Bible look - matte-black fabric, charcoal plates, controlled cyan seam light.
 - BP_NVPlayerCharacter: BodyMeshAsset = soldier, material override = MI_NV_Ghost7.
Args: [emission] [save]. Report: Saved/NV_ghost7_look.txt"""
import unreal, sys
args = sys.argv[2:]
emis = float(args[0]) if args and args[0] != "save" else 6.0
OUT = []
EAL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary
SOLDIER = "/Game/RetroFuturisticSoldier/Meshes/SKM_Soldier_Manny"
sk = unreal.load_asset(SOLDIER)
ours = unreal.load_asset("/Game/Characters/Mannequins/Meshes/SK_Mannequin")
theirs = sk.skeleton
for a, b in ((ours, theirs), (theirs, ours)):
    comp = list(a.get_editor_property("compatible_skeletons"))
    if b not in comp:
        comp.append(b)
        a.set_editor_property("compatible_skeletons", comp)
        EAL.save_loaded_asset(a, only_if_is_dirty=False)
OUT.append(f"compat: ours={[s.get_name() for s in ours.get_editor_property('compatible_skeletons')]}")

DIR = "/Game/NeonVeil/Characters/Ghost7"
path = DIR + "/MI_NV_Ghost7"
if EAL.does_asset_exist(path):
    mi = EAL.load_asset(path)
else:
    mi = unreal.AssetToolsHelpers.get_asset_tools().create_asset("MI_NV_Ghost7", DIR, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    MEL.set_material_instance_parent(mi, unreal.load_asset("/Game/RetroFuturisticSoldier/Materials/MI_RetroSoldier_Player"))
MEL.set_material_instance_vector_parameter_value(mi, "FabricColor", unreal.LinearColor(0.012, 0.013, 0.016, 1))
MEL.set_material_instance_vector_parameter_value(mi, "PrimaryColor", unreal.LinearColor(0.03, 0.55, 0.85, 1))
MEL.set_material_instance_scalar_parameter_value(mi, "EmissionStrength", emis)
MEL.update_material_instance(mi)
EAL.save_loaded_asset(mi, only_if_is_dirty=False)
OUT.append(f"MI_NV_Ghost7 emission={emis}")

BP = "/Game/NeonVeil/Core/BP_NVPlayerCharacter"
bp = unreal.load_asset(BP)
cdo = unreal.get_default_object(EAL.load_blueprint_class(BP))
cdo.set_editor_property("body_mesh_asset", sk)
mesh = cdo.get_editor_property("mesh")
mesh.set_editor_property("override_materials", [mi])
EAL.save_loaded_asset(bp, only_if_is_dirty=False)
OUT.append(f"cdo body={cdo.get_editor_property('body_mesh_asset').get_name()} anim={cdo.get_editor_property('body_anim_class')} mats={[m.get_name() for m in mesh.get_editor_property('override_materials')]}")
open(unreal.Paths.project_saved_dir() + "NV_ghost7_look.txt", "w").write("\n".join(str(x) for x in OUT))
