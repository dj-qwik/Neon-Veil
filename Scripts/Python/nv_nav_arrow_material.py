"""M_NV_NavArrow: translucent, unlit, two-sided glow for the wayfinding arrow (ANVNavArrow loads it by path).
Params: Color (vector), Glow (scalar), Opacity (scalar, animated by the arrow). Skips if it exists (never rebuild
an existing material graph: that crashed the editor). Report: Saved/NV_nav_arrow_material.txt"""
import unreal
EAL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary
AT = unreal.AssetToolsHelpers.get_asset_tools()
D = "/Game/NeonVeil/UI/Nav"
PATH = f"{D}/M_NV_NavArrow"
OUT = []
if EAL.does_asset_exist(PATH):
    OUT.append("exists")
else:
    m = AT.create_asset("M_NV_NavArrow", D, unreal.Material, unreal.MaterialFactoryNew())
    m.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
    m.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    m.set_editor_property("two_sided", True)
    col = MEL.create_material_expression(m, unreal.MaterialExpressionVectorParameter, -500, -100)
    col.set_editor_property("parameter_name", "Color")
    col.set_editor_property("default_value", unreal.LinearColor(0.15, 1.0, 0.35, 1))
    glow = MEL.create_material_expression(m, unreal.MaterialExpressionScalarParameter, -500, 50)
    glow.set_editor_property("parameter_name", "Glow"); glow.set_editor_property("default_value", 3.0)
    mul = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -250, -50)
    MEL.connect_material_expressions(col, "", mul, "A")
    MEL.connect_material_expressions(glow, "", mul, "B")
    op = MEL.create_material_expression(m, unreal.MaterialExpressionScalarParameter, -500, 200)
    op.set_editor_property("parameter_name", "Opacity"); op.set_editor_property("default_value", 0.5)
    MEL.connect_material_property(mul, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    MEL.connect_material_property(op, "", unreal.MaterialProperty.MP_OPACITY)
    MEL.recompile_material(m)
    EAL.save_loaded_asset(m)
    OUT.append("created " + PATH)
open(unreal.Paths.project_saved_dir() + "NV_nav_arrow_material.txt", "w").write("\n".join(OUT))
