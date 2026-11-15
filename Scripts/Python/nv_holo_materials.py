"""Materials for the cyberware body hologram (GHOST-OS cyberware page).
M_NV_Hologram2 (v1 kept for reference): unlit fresnel rim + drifting scan lines + faint fill, put on the operative's body in the hologram rig.
M_NV_HoloUI:   UI-domain material that shows the rig's scene capture with brightness as opacity (black = see-through).
Idempotent (rebuilds both). Assets in /Game/NeonVeil/UI/Holo."""
import unreal
EAL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary
AT = unreal.AssetToolsHelpers.get_asset_tools()
D = "/Game/NeonVeil/UI/Holo"

import sys
FORCE = "force" in sys.argv[2:]
def fresh(name):
    """New material, or None if it exists (rebuilding a graph in place crashed the material editor; delete the asset
    first, or pass 'force' to write a new copy next to it)."""
    p = f"{D}/{name}"
    if EAL.does_asset_exist(p) and not FORCE:
        return None
    return AT.create_asset(name, D, unreal.Material, unreal.MaterialFactoryNew())
def ex(m, cls, x, y, **props):
    e = MEL.create_material_expression(m, cls, x, y)
    for k, v in props.items():
        e.set_editor_property(k, v)
    return e
C = MEL.connect_material_expressions

# ---------------------------------------------------------------- body hologram
m = fresh("M_NV_Hologram2")
def build_holo(m):
    m.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    m.set_editor_property("blend_mode", unreal.BlendMode.BLEND_OPAQUE)
    m.set_editor_property("used_with_skeletal_mesh", True)
    col = ex(m, unreal.MaterialExpressionVectorParameter, -900, -200, parameter_name="HoloColor", default_value=unreal.LinearColor(0.35, 0.9, 1.0, 1))
    fr = ex(m, unreal.MaterialExpressionFresnel, -900, 0, exponent=3.0, base_reflect_fraction=0.0)
    rim = ex(m, unreal.MaterialExpressionMultiply, -700, 0, const_b=3.4); C(fr, "", rim, "A")
    wp = ex(m, unreal.MaterialExpressionWorldPosition, -1300, 250)
    z = ex(m, unreal.MaterialExpressionComponentMask, -1100, 250, r=False, g=False, b=True, a=False); C(wp, "", z, "")
    t = ex(m, unreal.MaterialExpressionTime, -1300, 400)
    zs = ex(m, unreal.MaterialExpressionMultiply, -950, 250, const_b=0.45); C(z, "", zs, "A")
    ts = ex(m, unreal.MaterialExpressionMultiply, -950, 400, const_b=0.6); C(t, "", ts, "A")
    ad = ex(m, unreal.MaterialExpressionAdd, -800, 300); C(zs, "", ad, "A"); C(ts, "", ad, "B")
    fc = ex(m, unreal.MaterialExpressionFrac, -680, 300); C(ad, "", fc, "")
    sb = ex(m, unreal.MaterialExpressionSubtract, -560, 300, const_b=0.86); C(fc, "", sb, "A")
    sm = ex(m, unreal.MaterialExpressionMultiply, -440, 300, const_b=0.9); C(sb, "", sm, "A")
    sat = ex(m, unreal.MaterialExpressionSaturate, -330, 300); C(sm, "", sat, "")
    # slow sweep band (brighter slice travelling up the body)
    zs2 = ex(m, unreal.MaterialExpressionMultiply, -950, 550, const_b=0.006); C(z, "", zs2, "A")
    ts2 = ex(m, unreal.MaterialExpressionMultiply, -950, 650, const_b=-0.25); C(t, "", ts2, "A")
    ad2 = ex(m, unreal.MaterialExpressionAdd, -800, 600); C(zs2, "", ad2, "A"); C(ts2, "", ad2, "B")
    fc2 = ex(m, unreal.MaterialExpressionFrac, -680, 600); C(ad2, "", fc2, "")
    pw = ex(m, unreal.MaterialExpressionPower, -560, 600, const_exponent=24.0); C(fc2, "", pw, "Base")
    band = ex(m, unreal.MaterialExpressionMultiply, -440, 600, const_b=1.2); C(pw, "", band, "A")
    s1 = ex(m, unreal.MaterialExpressionAdd, -300, 100); C(rim, "", s1, "A"); C(sat, "", s1, "B")
    s2 = ex(m, unreal.MaterialExpressionAdd, -200, 200); C(s1, "", s2, "A"); C(band, "", s2, "B")
    s3 = ex(m, unreal.MaterialExpressionAdd, -100, 200, const_b=0.035); C(s2, "", s3, "A")
    em = ex(m, unreal.MaterialExpressionMultiply, 50, 0); C(col, "", em, "A"); C(s3, "", em, "B")
    MEL.connect_material_property(em, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    MEL.recompile_material(m); EAL.save_loaded_asset(m)

if m:
    build_holo(m)

# ---------------------------------------------------------------- UI presenter
u = fresh("M_NV_HoloUI")
def build_ui(u):
    u.set_editor_property("material_domain", unreal.MaterialDomain.MD_UI)
    u.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
    tx = ex(u, unreal.MaterialExpressionTextureSampleParameter2D, -700, 0, parameter_name="Capture", texture=unreal.load_asset("/Engine/EngineResources/Black"))
    r = ex(u, unreal.MaterialExpressionComponentMask, -450, 150, r=True, g=False, b=False, a=False); C(tx, "RGB", r, "")
    g = ex(u, unreal.MaterialExpressionComponentMask, -450, 230, r=False, g=True, b=False, a=False); C(tx, "RGB", g, "")
    b = ex(u, unreal.MaterialExpressionComponentMask, -450, 310, r=False, g=False, b=True, a=False); C(tx, "RGB", b, "")
    m1 = ex(u, unreal.MaterialExpressionMax, -330, 180); C(r, "", m1, "A"); C(g, "", m1, "B")
    m2 = ex(u, unreal.MaterialExpressionMax, -230, 220); C(m1, "", m2, "A"); C(b, "", m2, "B")
    op = ex(u, unreal.MaterialExpressionMultiply, -130, 220, const_b=2.2); C(m2, "", op, "A")
    so = ex(u, unreal.MaterialExpressionSaturate, -30, 220); C(op, "", so, "")
    MEL.connect_material_property(tx, "RGB", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    MEL.connect_material_property(so, "", unreal.MaterialProperty.MP_OPACITY)
    MEL.recompile_material(u); EAL.save_loaded_asset(u)
if u:
    build_ui(u)
open(unreal.Paths.project_saved_dir() + "NV_holo_materials.txt", "w").write("ok")
