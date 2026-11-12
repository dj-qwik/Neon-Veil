"""NEON VEIL - volumetric rain (replaces the near/mid panning rain sheets, which tiled visibly).
 - M_NV_RainDrop: unlit translucent streak; per-instance custom data (phase, speed, brightness, height) drives a
   World Position Offset fall-and-wrap, so the GPU animates every streak independently. Soft width/length
   profile, camera-depth fade so nothing pops in front of the lens.
 - ANVRainField volumes (C++) outside the skybridge glass (both sides), along the tram approach, and outside
   the atrium's 6 m glazing, in a near layer (fine fast streaks) and a mid layer (longer, fainter).
 - Old sheet layers L0/L1 removed; far sheet L2 kept as distant haze, fainter.
Re-runnable (folder FX_Rain cleared). Report: Saved/NV_m9_rain.txt"""
import unreal

REPORT = []
def log(*a):
    msg = " ".join(str(x) for x in a)
    REPORT.append(msg)
    unreal.log("[NV rain] " + msg)

AT = unreal.AssetToolsHelpers.get_asset_tools()
EAL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
LES = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ART = "/Game/NeonVeil/Materials/Art"
V = unreal.Vector
FOLDER = "FX_Rain"

def build_material():
    path = f"{ART}/M_NV_RainDrop"
    if EAL.does_asset_exist(path):
        EAL.delete_asset(path)
    m = AT.create_asset("M_NV_RainDrop", ART, unreal.Material, unreal.MaterialFactoryNew())
    m.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    m.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
    m.set_editor_property("two_sided", True)
    m.set_editor_property("used_with_instanced_static_meshes", True)

    def x(cls, px, py, **p):
        e = MEL.create_material_expression(m, cls, px, py)
        for k, v in p.items():
            e.set_editor_property(k, v)
        return e
    def link(a, ap, b, bp):
        MEL.connect_material_expressions(a, ap, b, bp)
    def op(cls, a, b, px, py):
        e = x(cls, px, py)
        link(a, "", e, "A"); link(b, "", e, "B")
        return e

    phase = x(unreal.MaterialExpressionPerInstanceCustomData, -1400, -200, data_index=0)
    speed = x(unreal.MaterialExpressionPerInstanceCustomData, -1400, -100, data_index=1)
    bright = x(unreal.MaterialExpressionPerInstanceCustomData, -1400, 0, data_index=2)
    height = x(unreal.MaterialExpressionPerInstanceCustomData, -1400, 100, data_index=3)
    time = x(unreal.MaterialExpressionTime, -1400, -320)

    # WPO.z = (phase - frac(time*speed/height + phase)) * height
    ts = op(unreal.MaterialExpressionMultiply, time, speed, -1200, -300)
    tsh = op(unreal.MaterialExpressionDivide, ts, height, -1050, -300)
    t = op(unreal.MaterialExpressionAdd, tsh, phase, -900, -300)
    fr = x(unreal.MaterialExpressionFrac, -750, -300)
    link(t, "", fr, "")
    d = op(unreal.MaterialExpressionSubtract, phase, fr, -600, -300)
    dz = op(unreal.MaterialExpressionMultiply, d, height, -450, -300)
    zero2 = x(unreal.MaterialExpressionConstant2Vector, -450, -400, r=0.0, g=0.0)
    wpo = op(unreal.MaterialExpressionAppendVector, zero2, dz, -300, -350)
    MEL.connect_material_property(wpo, "", unreal.MaterialProperty.MP_WORLD_POSITION_OFFSET)

    # streak profile: (1-|2u-1|) * 4v(1-v)
    uv = x(unreal.MaterialExpressionTextureCoordinate, -1400, 300)
    u = x(unreal.MaterialExpressionComponentMask, -1250, 260, r=True, g=False, b=False, a=False)
    v = x(unreal.MaterialExpressionComponentMask, -1250, 380, r=False, g=True, b=False, a=False)
    link(uv, "", u, ""); link(uv, "", v, "")
    two = x(unreal.MaterialExpressionConstant, -1250, 200, r=2.0)
    one = x(unreal.MaterialExpressionConstant, -1250, 470, r=1.0)
    u2 = op(unreal.MaterialExpressionMultiply, u, two, -1100, 240)
    u2m = op(unreal.MaterialExpressionSubtract, u2, one, -980, 240)
    ua = x(unreal.MaterialExpressionAbs, -860, 240)
    link(u2m, "", ua, "")
    uw = x(unreal.MaterialExpressionOneMinus, -740, 240)
    link(ua, "", uw, "")
    vm = x(unreal.MaterialExpressionOneMinus, -1100, 400)
    link(v, "", vm, "")
    vv = op(unreal.MaterialExpressionMultiply, v, vm, -980, 400)
    four = x(unreal.MaterialExpressionConstant, -980, 480, r=4.0)
    vl = op(unreal.MaterialExpressionMultiply, vv, four, -860, 400)
    shape = op(unreal.MaterialExpressionMultiply, uw, vl, -620, 320)

    opac_p = x(unreal.MaterialExpressionScalarParameter, -620, 450, parameter_name="Opacity", default_value=0.5)
    # near-camera fade: saturate((PixelDepth - 40) / 80)
    pd = x(unreal.MaterialExpressionPixelDepth, -900, 560)
    c40 = x(unreal.MaterialExpressionConstant, -900, 640, r=40.0)
    c80 = x(unreal.MaterialExpressionConstant, -760, 640, r=80.0)
    pdo = op(unreal.MaterialExpressionSubtract, pd, c40, -760, 560)
    pdd = op(unreal.MaterialExpressionDivide, pdo, c80, -620, 560)
    cdf = x(unreal.MaterialExpressionSaturate, -480, 560)
    link(pdd, "", cdf, "")
    a1 = op(unreal.MaterialExpressionMultiply, shape, bright, -460, 340)
    a2 = op(unreal.MaterialExpressionMultiply, a1, opac_p, -320, 380)
    a3 = op(unreal.MaterialExpressionMultiply, a2, cdf, -180, 420)
    MEL.connect_material_property(a3, "", unreal.MaterialProperty.MP_OPACITY)

    col = x(unreal.MaterialExpressionVectorParameter, -620, 0, parameter_name="Color",
            default_value=unreal.LinearColor(0.62, 0.72, 0.88, 1))
    em_p = x(unreal.MaterialExpressionScalarParameter, -620, 120, parameter_name="Emissive", default_value=1.6)
    e1 = op(unreal.MaterialExpressionMultiply, col, bright, -460, 40)
    e2 = op(unreal.MaterialExpressionMultiply, e1, em_p, -320, 60)
    MEL.connect_material_property(e2, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    MEL.recompile_material(m)
    EAL.save_loaded_asset(m, only_if_is_dirty=False)
    log("built", path)
    return m

def mi(name, parent, opacity, emissive):
    path = f"{ART}/{name}"
    inst = unreal.load_asset(path) if EAL.does_asset_exist(path) else AT.create_asset(
        name, ART, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    MEL.set_material_instance_parent(inst, parent)
    MEL.set_material_instance_scalar_parameter_value(inst, "Opacity", opacity)
    MEL.set_material_instance_scalar_parameter_value(inst, "Emissive", emissive)
    EAL.save_loaded_asset(inst, only_if_is_dirty=False)
    return inst

def field(label, center, extent, count, mat, length, width, speed, bright, yaw=0.0, seed=1):
    a = EAS.spawn_actor_from_class(unreal.NVRainField, V(*center), unreal.Rotator(0, yaw, 0))
    a.set_editor_property("extent", V(*extent))
    a.set_editor_property("count", count)
    a.set_editor_property("length_range", unreal.Vector2D(*length))
    a.set_editor_property("width_range", unreal.Vector2D(*width))
    a.set_editor_property("speed_range", unreal.Vector2D(*speed))
    a.set_editor_property("brightness_range", unreal.Vector2D(*bright))
    a.set_editor_property("seed", seed)
    a.set_editor_property("material", mat)
    a.set_actor_label(label)
    a.set_folder_path(FOLDER)
    a.set_actor_location(V(center[0], center[1], center[2] + 0.01), False, False)  # re-runs construction with the new settings
    return a

def main():
    for a in EAS.get_all_level_actors():
        if str(a.get_folder_path()) == FOLDER:
            EAS.destroy_actor(a)
    removed = 0
    for a in EAS.get_all_level_actors():
        lab = a.get_actor_label()
        if lab.startswith("Rain_") and (lab.endswith("_L0") or lab.endswith("_L1")):
            EAS.destroy_actor(a)
            removed += 1
    log("removed sheet layers", removed)
    l2 = unreal.load_asset(f"{ART}/MI_NV_Rain_L2")
    if l2:
        MEL.set_material_instance_scalar_parameter_value(l2, "Opacity", 0.25)
        EAL.save_loaded_asset(l2, only_if_is_dirty=False)

    base = build_material()
    near = mi("MI_NV_RainDrop_Near", base, 0.55, 1.7)
    mid = mi("MI_NV_RainDrop_Mid", base, 0.32, 1.1)
    NEAR = dict(length=(30, 65), width=(0.5, 1.1), speed=(900, 1200), bright=(0.3, 1.0))
    MID = dict(length=(90, 170), width=(1.2, 2.4), speed=(800, 1050), bright=(0.25, 0.8))
    s = 1
    # skybridge (glass at y = +-300); stop at the atrium wall x = 3480
    for side, sgn in (("S", -1), ("N", 1)):
        field(f"RainNear_Bridge{side}", (1100, sgn * 800, 350), (2400, 450, 1000), 4200, near, seed=s, **NEAR); s += 1
        field(f"RainMid_Bridge{side}", (1100, sgn * 2400, 600), (3600, 1100, 1800), 3500, mid, seed=s, **MID); s += 1
        # tram approach (x -7000..-1300)
        field(f"RainNear_Tram{side}", (-4200, sgn * 700, 300), (3000, 400, 900), 3200, near, seed=s, **NEAR); s += 1
    # atrium north glazing (y = 1100, x 3500..6300)
    field("RainNear_AtriumN", (4900, 1650, 600), (1500, 500, 1200), 4200, near, seed=s, **NEAR); s += 1
    field("RainMid_AtriumN", (4900, 3400, 900), (4000, 1200, 2200), 4000, mid, seed=s, **MID); s += 1
    total = sum(a.get_editor_property("count") for a in EAS.get_all_level_actors() if str(a.get_folder_path()) == FOLDER)
    log("rain fields placed; total streaks", total)
    LES.save_current_level()

try:
    main()
finally:
    with open(unreal.Paths.project_saved_dir() + "NV_m9_rain.txt", "w", encoding="utf-8") as fh:
        fh.write("\n".join(REPORT))
