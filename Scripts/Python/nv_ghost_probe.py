"""Probe the Retro Futuristic Soldier pack and Ghost's current body. Report: Saved/NV_ghost_probe.txt"""
import unreal
OUT = []
MEL = unreal.MaterialEditingLibrary
sk = unreal.load_asset("/Game/RetroFuturisticSoldier/Meshes/SKM_Soldier_Manny")
OUT.append(f"soldier skeleton = {sk.skeleton.get_path_name()}")
OUT.append(f"soldier mats = {[m.material_interface.get_path_name() if m.material_interface else None for m in sk.materials]}")
OUT.append(f"soldier slots = {[str(m.material_slot_name) for m in sk.materials]}")
for p in ("/Game/RetroFuturisticSoldier/Materials/MI_RetroSoldier_Player", "/Game/RetroFuturisticSoldier/DemoAssets/Materials/MI_Soldier_1", "/Game/RetroFuturisticSoldier/DemoAssets/Materials/MI_Soldier_9"):
    m = unreal.load_asset(p)
    OUT.append(f"== {p}")
    for n in MEL.get_scalar_parameter_names(m):
        OUT.append(f"  s {n} = {MEL.get_material_instance_scalar_parameter_value(m, n)}")
    for n in MEL.get_vector_parameter_names(m):
        v = MEL.get_material_instance_vector_parameter_value(m, n)
        OUT.append(f"  v {n} = ({v.r:.3f},{v.g:.3f},{v.b:.3f},{v.a:.2f})")
    for n in MEL.get_static_switch_parameter_names(m):
        OUT.append(f"  sw {n} = {MEL.get_material_instance_static_switch_parameter_value(m, n)}")
bp = unreal.EditorAssetLibrary.load_blueprint_class("/Game/NeonVeil/Core/BP_NVPlayerCharacter")
cdo = unreal.get_default_object(bp)
mesh = cdo.get_editor_property("mesh")
OUT.append(f"ghost mesh = {mesh.get_skeletal_mesh_asset().get_path_name() if mesh.get_skeletal_mesh_asset() else None} anim={mesh.get_editor_property('anim_class')} rel={mesh.get_editor_property('relative_location')} rot={mesh.get_editor_property('relative_rotation')}")
ours = mesh.get_skeletal_mesh_asset().skeleton if mesh.get_skeletal_mesh_asset() else None
if ours:
    OUT.append(f"ghost skeleton = {ours.get_path_name()} compat={[s.get_path_name() for s in ours.get_editor_property('compatible_skeletons')]}")
open(unreal.Paths.project_saved_dir() + "NV_ghost_probe.txt", "w").write("\n".join(str(x) for x in OUT))
