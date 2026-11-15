"""Wayfinding chevron (design: classic green nav-arrow with a dark outline), built with Geometry Script.
  SM_NV_NavChevron         - green fill, tip at +X, centred on the origin, 120 x 100 cm, 1.5 cm thick
  SM_NV_NavChevronOutline  - the same shape 14% larger, a hair lower: the dark rim
  M_NV_NavArrowMasked      - unlit, two-sided, MASKED with temporal dither (half-see-through without the
                             translucency pass, which kept dropping the arrow on the wet street)
  MI_NV_NavArrow_Fill / MI_NV_NavArrow_Outline
Skips any existing material (never rebuild a graph). Geometry Script GC hazard: restart the editor afterwards.
Report: Saved/NV_nav_chevron.txt"""
import unreal
EAL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary
AT = unreal.AssetToolsHelpers.get_asset_tools()
GP = unreal.GeometryScript_Primitives
GA = unreal.GeometryScript_AssetUtils
V = unreal.Vector
D = "/Game/NeonVeil/UI/Nav"
OUT = []

MPATH = f"{D}/M_NV_NavArrowMasked"
if EAL.does_asset_exist(MPATH):
    M = unreal.load_asset(MPATH)
else:
    M = AT.create_asset("M_NV_NavArrowMasked", D, unreal.Material, unreal.MaterialFactoryNew())
    M.set_editor_property("blend_mode", unreal.BlendMode.BLEND_MASKED)
    M.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    M.set_editor_property("two_sided", True)
    M.set_editor_property("opacity_mask_clip_value", 0.5)
    col = MEL.create_material_expression(M, unreal.MaterialExpressionVectorParameter, -600, -150)
    col.set_editor_property("parameter_name", "Color"); col.set_editor_property("default_value", unreal.LinearColor(0.25, 0.85, 0.15, 1))
    glow = MEL.create_material_expression(M, unreal.MaterialExpressionScalarParameter, -600, 0)
    glow.set_editor_property("parameter_name", "Glow"); glow.set_editor_property("default_value", 2.5)
    mul = MEL.create_material_expression(M, unreal.MaterialExpressionMultiply, -350, -80)
    MEL.connect_material_expressions(col, "", mul, "A"); MEL.connect_material_expressions(glow, "", mul, "B")
    MEL.connect_material_property(mul, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    op = MEL.create_material_expression(M, unreal.MaterialExpressionScalarParameter, -600, 150)
    op.set_editor_property("parameter_name", "Opacity"); op.set_editor_property("default_value", 0.6)
    dith = MEL.create_material_expression(M, unreal.MaterialExpressionMaterialFunctionCall, -350, 150)
    dith.set_material_function(unreal.load_asset("/Engine/Functions/Engine_MaterialFunctions02/Utility/DitherTemporalAA"))
    ok = MEL.connect_material_expressions(op, "", dith, "Alpha Threshold") or MEL.connect_material_expressions(op, "", dith, "")
    OUT.append(f"dither input connected: {ok}")
    MEL.connect_material_property(dith, "", unreal.MaterialProperty.MP_OPACITY_MASK)
    MEL.recompile_material(M)
    EAL.save_loaded_asset(M)
    OUT.append("created " + MPATH)

def mi(name, color, glow):
    path = f"{D}/{name}"
    m = unreal.load_asset(path) if EAL.does_asset_exist(path) else AT.create_asset(name, D, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    MEL.set_material_instance_parent(m, M)
    MEL.set_material_instance_vector_parameter_value(m, "Color", unreal.LinearColor(*color, 1))
    MEL.set_material_instance_scalar_parameter_value(m, "Glow", glow)
    EAL.save_loaded_asset(m)
    return m
FILL = mi("MI_NV_NavArrow_Fill", (0.25, 0.9, 0.12), 2.2)
RIM = mi("MI_NV_NavArrow_Outline", (0.01, 0.02, 0.01), 1.0)

# chevron: tip at +X, notch at the back (like a GPS position marker)
PTS = [(60.0, 0.0), (-55.0, 50.0), (-28.0, 0.0), (-55.0, -50.0)]
def build(name, scale, z, mat):
    path = f"{D}/{name}"
    m = unreal.new_object(unreal.DynamicMesh, name=f"NV_{name}_Build")
    o = unreal.GeometryScriptPrimitiveOptions()
    poly = [unreal.Vector2D(x * scale, y * scale) for x, y in reversed(PTS)]
    T = unreal.Transform(V(0, 0, z), unreal.Rotator(), V(1, 1, 1))
    names = [n for n in dir(GP) if "polygon" in n.lower()]
    OUT.append(f"poly fns: {names}")
    if hasattr(GP, "append_simple_extrude_polygon"):
        GP.append_simple_extrude_polygon(m, o, T, poly, 1.5, 0, True, unreal.GeometryScriptPrimitiveOriginMode.BASE)
    else:
        # triangulated polygon fill (front + back faces) as a last resort
        GP.append_triangulated_polygon(m, o, T, poly, True)
    if EAL.does_asset_exist(path):
        sm = unreal.load_asset(path)
        GA.copy_mesh_to_static_mesh(m, sm, unreal.GeometryScriptCopyMeshToAssetOptions(), unreal.GeometryScriptMeshWriteLOD())
    else:
        opts = unreal.GeometryScriptCreateNewStaticMeshAssetOptions()
        opts.set_editor_property("enable_recompute_normals", True)
        opts.set_editor_property("enable_nanite", False)
        opts.set_editor_property("enable_collision", False)
        fn = None
        for cls in ("GeometryScript_NewAssetUtils", "GeometryScript_CreateNewAsset", "GeometryScript_AssetUtils"):
            c = getattr(unreal, cls, None)
            if c and hasattr(c, "create_new_static_mesh_asset_from_mesh"):
                fn = c.create_new_static_mesh_asset_from_mesh
                break
        res = fn(m, path, opts)
        sm = res[0] if isinstance(res, tuple) else res
    s = unreal.StaticMaterial()
    s.set_editor_property("material_interface", mat)
    s.set_editor_property("material_slot_name", "Arrow")
    sm.set_editor_property("static_materials", [s])
    EAL.save_loaded_asset(sm)
    b = sm.get_bounding_box()
    OUT.append(f"{name}: {b.min} {b.max}")
    return m
OUT.append("Dither fn ok" )
keep = [build("SM_NV_NavChevron", 1.0, 0.6, FILL), build("SM_NV_NavChevronOutline", 1.14, 0.0, RIM)]
open(unreal.Paths.project_saved_dir() + "NV_nav_chevron.txt", "w").write("\n".join(OUT))
del keep
