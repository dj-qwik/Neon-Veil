"""Ghost-7 suit: calm the reflections. The Retro Soldier master has no roughness/metal controls and its plates read as
noisy mirror metal under Lumen in the wet night street. Make a local copy of the master (inside the pack's own folder,
which stays gitignored) with RoughnessMin (max) and MetallicScale (multiply) params, then parent MI_NV_Ghost7 to it.
Also BaseTint (multiply on base colour): rough metal picks up the warm street light and reads beige, so the plates are
darkened toward the Bible's charcoal. Args: [rough_min] [metal_scale] [base_tint]. Report: Saved/NV_ghost7_material.txt"""
import unreal, sys
args = sys.argv[2:]
rough_min = float(args[0]) if len(args) > 0 else 0.5
metal_scale = float(args[1]) if len(args) > 1 else 1.0
base_tint = float(args[2]) if len(args) > 2 else 0.3
OUT = []
EAL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary
SRC = "/Game/RetroFuturisticSoldier/Materials/M_RetroSoldier"
DST = "/Game/RetroFuturisticSoldier/NV/M_NV_Ghost7Soldier"

if not EAL.does_asset_exist(DST):
    EAL.duplicate_asset(SRC, DST)
    mat = unreal.load_asset(DST)
    MP = unreal.MaterialProperty
    # Roughness = max(original, RoughnessMin)
    node = MEL.get_material_property_input_node(mat, MP.MP_ROUGHNESS)
    outname = MEL.get_material_property_input_node_output_name(mat, MP.MP_ROUGHNESS) if node else ""
    p = MEL.create_material_expression(mat, unreal.MaterialExpressionScalarParameter, -600, 400)
    p.set_editor_property("parameter_name", "RoughnessMin")
    p.set_editor_property("default_value", rough_min)
    if node:
        mx = MEL.create_material_expression(mat, unreal.MaterialExpressionMax, -300, 400)
        MEL.connect_material_expressions(node, outname, mx, "A")
        MEL.connect_material_expressions(p, "", mx, "B")
        MEL.connect_material_property(mx, "", MP.MP_ROUGHNESS)
    else:
        MEL.connect_material_property(p, "", MP.MP_ROUGHNESS)
    OUT.append(f"roughness src: {node.get_name() if node else None} [{outname}]")
    # Metallic = original * MetallicScale
    node = MEL.get_material_property_input_node(mat, MP.MP_METALLIC)
    outname = MEL.get_material_property_input_node_output_name(mat, MP.MP_METALLIC) if node else ""
    q = MEL.create_material_expression(mat, unreal.MaterialExpressionScalarParameter, -600, 600)
    q.set_editor_property("parameter_name", "MetallicScale")
    q.set_editor_property("default_value", metal_scale)
    if node:
        mul = MEL.create_material_expression(mat, unreal.MaterialExpressionMultiply, -300, 600)
        MEL.connect_material_expressions(node, outname, mul, "A")
        MEL.connect_material_expressions(q, "", mul, "B")
        MEL.connect_material_property(mul, "", MP.MP_METALLIC)
    OUT.append(f"metallic src: {node.get_name() if node else None} [{outname}]")
    MEL.recompile_material(mat)
    EAL.save_loaded_asset(mat, only_if_is_dirty=False)

mat = unreal.load_asset(DST)
if "BaseTint" not in [str(n) for n in MEL.get_scalar_parameter_names(mat)]:
    MP = unreal.MaterialProperty
    node = MEL.get_material_property_input_node(mat, MP.MP_BASE_COLOR)
    outname = MEL.get_material_property_input_node_output_name(mat, MP.MP_BASE_COLOR) if node else ""
    t = MEL.create_material_expression(mat, unreal.MaterialExpressionScalarParameter, -600, 200)
    t.set_editor_property("parameter_name", "BaseTint")
    t.set_editor_property("default_value", base_tint)
    if node:
        mul = MEL.create_material_expression(mat, unreal.MaterialExpressionMultiply, -300, 200)
        MEL.connect_material_expressions(node, outname, mul, "A")
        MEL.connect_material_expressions(t, "", mul, "B")
        MEL.connect_material_property(mul, "", MP.MP_BASE_COLOR)
    OUT.append(f"basecolor src: {node.get_name() if node else None} [{outname}]")
    MEL.recompile_material(mat)
    EAL.save_loaded_asset(mat, only_if_is_dirty=False)
mi = unreal.load_asset("/Game/NeonVeil/Characters/Ghost7/MI_NV_Ghost7")
if mi.get_editor_property("parent") != mat:
    MEL.set_material_instance_parent(mi, mat)
MEL.set_material_instance_scalar_parameter_value(mi, "RoughnessMin", rough_min)
MEL.set_material_instance_scalar_parameter_value(mi, "MetallicScale", metal_scale)
MEL.set_material_instance_scalar_parameter_value(mi, "BaseTint", base_tint)
MEL.update_material_instance(mi)
EAL.save_loaded_asset(mi, only_if_is_dirty=False)
OUT.append(f"MI_NV_Ghost7 parent={mi.get_editor_property('parent').get_name()} rough_min={rough_min} metal_scale={metal_scale} base_tint={base_tint}")
OUT.append(f"params: {MEL.get_scalar_parameter_names(mi)}")
open(unreal.Paths.project_saved_dir() + "NV_ghost7_material.txt", "w").write("\n".join(str(x) for x in OUT))
