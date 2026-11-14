"""Probe the Ghost-7 soldier materials: slots, parents, scalar/vector/texture params. Report: Saved/NV_ghost_mat.txt"""
import unreal
OUT = []
MEL = unreal.MaterialEditingLibrary
sk = unreal.load_asset("/Game/RetroFuturisticSoldier/Meshes/SKM_Soldier_Manny")
for i, m in enumerate(sk.materials):
    OUT.append(f"slot {i} {m.material_slot_name} -> {m.material_interface.get_path_name() if m.material_interface else None}")
cdo = unreal.get_default_object(unreal.EditorAssetLibrary.load_blueprint_class("/Game/NeonVeil/Core/BP_NVPlayerCharacter"))
OUT.append(f"overrides: {[x.get_name() if x else None for x in cdo.get_editor_property('mesh').get_editor_property('override_materials')]}")
seen = set()
def dump(mi, depth=0):
    if not mi or mi.get_path_name() in seen:
        return
    seen.add(mi.get_path_name())
    pad = "  " * depth
    OUT.append(f"{pad}{mi.get_class().get_name()} {mi.get_path_name()}")
    if isinstance(mi, unreal.MaterialInstance):
        for n in MEL.get_scalar_parameter_names(mi):
            OUT.append(f"{pad}  S {n} = {MEL.get_material_instance_scalar_parameter_value(mi, n)}")
        for n in MEL.get_vector_parameter_names(mi):
            OUT.append(f"{pad}  V {n} = {MEL.get_material_instance_vector_parameter_value(mi, n)}")
        for n in MEL.get_texture_parameter_names(mi):
            t = MEL.get_material_instance_texture_parameter_value(mi, n)
            OUT.append(f"{pad}  T {n} = {t.get_name() if t else None}")
        dump(mi.get_editor_property("parent"), depth + 1)
    else:
        for n in MEL.get_scalar_parameter_names(mi):
            OUT.append(f"{pad}  S {n} = {MEL.get_material_default_scalar_parameter_value(mi, n)}")
for m in sk.materials:
    dump(m.material_interface)
dump(unreal.load_asset("/Game/NeonVeil/Characters/Ghost7/MI_NV_Ghost7"))
open(unreal.Paths.project_saved_dir() + "NV_ghost_mat.txt", "w").write("\n".join(str(x) for x in OUT))
