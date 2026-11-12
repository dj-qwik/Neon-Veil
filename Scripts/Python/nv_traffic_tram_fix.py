"""(1) Traffic: per-car directional lights. Front face (travel direction) glows white/cyan, back face red, sides dim,
so approaching cars show headlights and receding cars show tail lights from any view. (2) Tram made still.
Report: Saved/NV_traffic_tram_fix.txt"""
import unreal
EAL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary
out = []
D = "/Game/NeonVeil/Materials/FX"
MP = D + "/M_NV_TrafficCar"
if not EAL.does_asset_exist(MP):
    m = unreal.AssetToolsHelpers.get_asset_tools().create_asset("M_NV_TrafficCar", D, unreal.Material, unreal.MaterialFactoryNew())
    m.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    C = lambda cls, x, y: MEL.create_material_expression(m, cls, x, y)
    n = C(unreal.MaterialExpressionVertexNormalWS, -1200, 0)
    mx = C(unreal.MaterialExpressionComponentMask, -1000, 0)
    mx.set_editor_property("r", True); mx.set_editor_property("g", False); mx.set_editor_property("b", False); mx.set_editor_property("a", False)
    sign = C(unreal.MaterialExpressionScalarParameter, -1000, 150); sign.set_editor_property("parameter_name", "Sign"); sign.set_editor_property("default_value", 1.0)
    d = C(unreal.MaterialExpressionMultiply, -800, 50)
    MEL.connect_material_expressions(n, "", mx, ""); MEL.connect_material_expressions(mx, "", d, "A"); MEL.connect_material_expressions(sign, "", d, "B")
    f = C(unreal.MaterialExpressionSaturate, -600, 0); MEL.connect_material_expressions(d, "", f, "")
    neg = C(unreal.MaterialExpressionOneMinus, -600, 150)
    # back = saturate(-d) = saturate(1 - (d + 1)) ; use OneMinus(d) - 1 via Subtract
    add1 = C(unreal.MaterialExpressionAdd, -700, 150); one = C(unreal.MaterialExpressionConstant, -800, 250); one.set_editor_property("r", 1.0)
    MEL.connect_material_expressions(d, "", add1, "A"); MEL.connect_material_expressions(one, "", add1, "B")
    MEL.connect_material_expressions(add1, "", neg, "")
    b = C(unreal.MaterialExpressionSaturate, -450, 150); MEL.connect_material_expressions(neg, "", b, "")
    p = C(unreal.MaterialExpressionConstant, -600, 350); p.set_editor_property("r", 8.0)
    fp = C(unreal.MaterialExpressionPower, -350, 0); MEL.connect_material_expressions(f, "", fp, "Base"); MEL.connect_material_expressions(p, "", fp, "Exponent")
    bp = C(unreal.MaterialExpressionPower, -300, 150); MEL.connect_material_expressions(b, "", bp, "Base"); MEL.connect_material_expressions(p, "", bp, "Exponent")
    head = C(unreal.MaterialExpressionVectorParameter, -350, -200); head.set_editor_property("parameter_name", "HeadColor"); head.set_editor_property("default_value", unreal.LinearColor(1, 0.92, 0.8, 1))
    tail = C(unreal.MaterialExpressionVectorParameter, -300, 300); tail.set_editor_property("parameter_name", "TailColor"); tail.set_editor_property("default_value", unreal.LinearColor(1, 0.08, 0.05, 1))
    hm = C(unreal.MaterialExpressionMultiply, -150, -100); MEL.connect_material_expressions(head, "", hm, "A"); MEL.connect_material_expressions(fp, "", hm, "B")
    tm = C(unreal.MaterialExpressionMultiply, -150, 200); MEL.connect_material_expressions(tail, "", tm, "A"); MEL.connect_material_expressions(bp, "", tm, "B")
    side = C(unreal.MaterialExpressionScalarParameter, -150, 400); side.set_editor_property("parameter_name", "SideGlow"); side.set_editor_property("default_value", 0.05)
    sm = C(unreal.MaterialExpressionMultiply, 0, 400); MEL.connect_material_expressions(head, "", sm, "A"); MEL.connect_material_expressions(side, "", sm, "B")
    s1 = C(unreal.MaterialExpressionAdd, 50, 50); MEL.connect_material_expressions(hm, "", s1, "A"); MEL.connect_material_expressions(tm, "", s1, "B")
    s2 = C(unreal.MaterialExpressionAdd, 150, 150); MEL.connect_material_expressions(s1, "", s2, "A"); MEL.connect_material_expressions(sm, "", s2, "B")
    inten = C(unreal.MaterialExpressionScalarParameter, 150, 300); inten.set_editor_property("parameter_name", "Intensity"); inten.set_editor_property("default_value", 50.0)
    em = C(unreal.MaterialExpressionMultiply, 300, 150); MEL.connect_material_expressions(s2, "", em, "A"); MEL.connect_material_expressions(inten, "", em, "B")
    MEL.connect_material_property(em, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    MEL.recompile_material(m)
    EAL.save_loaded_asset(m)
    out.append("built M_NV_TrafficCar")
base = unreal.load_asset(MP)

def mi(name, sign, head, tail, inten):
    p = D + "/" + name
    i = unreal.load_asset(p) if EAL.does_asset_exist(p) else unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        name, D, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    i.set_editor_property("parent", base)
    MEL.set_material_instance_scalar_parameter_value(i, "Sign", sign)
    MEL.set_material_instance_vector_parameter_value(i, "HeadColor", unreal.LinearColor(*head, 1))
    MEL.set_material_instance_vector_parameter_value(i, "TailColor", unreal.LinearColor(1, 0.08, 0.05, 1))
    MEL.set_material_instance_scalar_parameter_value(i, "Intensity", inten)
    EAL.save_loaded_asset(i)
    return i

WHITE, CYAN = (1, 0.92, 0.8), (0.2, 0.9, 1.0)
car = {
    ("white", 1): mi("MI_NV_TrafficCar_White_Fwd", 1.0, WHITE, None, 55.0),
    ("white", -1): mi("MI_NV_TrafficCar_White_Rev", -1.0, WHITE, None, 55.0),
    ("cyan", 1): mi("MI_NV_TrafficCar_Cyan_Fwd", 1.0, CYAN, None, 50.0),
    ("cyan", -1): mi("MI_NV_TrafficCar_Cyan_Rev", -1.0, CYAN, None, 50.0),
}
n = 0
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    if a.get_class().get_name() == "NVTrafficStream":
        fm = a.get_editor_property("forward_material")
        rm = a.get_editor_property("reverse_material")
        fk = "cyan" if fm and "Cyan" in fm.get_name() else "white"
        rk = "cyan" if rm and "Cyan" in rm.get_name() else "white"
        a.set_editor_property("forward_material", car[(fk, 1)])
        a.set_editor_property("reverse_material", car[(rk, -1)])
        a.set_actor_location(a.get_actor_location(), False, False)
        rot = a.get_actor_rotation()
        out.append("%s rot %s fwd %s rev %s" % (a.get_actor_label(), rot, fk, rk))
        n += 1
out.append("traffic lanes updated: %d" % n)
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    if a.get_class().get_name() == "NVTramArrival":
        a.set_editor_property("distance", 0.0)
        a.set_editor_property("duration", 1.0)
        a.set_editor_property("ride_sound", None)
        out.append("tram %s made still" % a.get_actor_label())
unreal.EditorLevelLibrary.save_current_level()
open(unreal.Paths.project_saved_dir() + "NV_traffic_tram_fix.txt", "w").write("\n".join(out))
