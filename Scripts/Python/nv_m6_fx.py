"""NEON VEIL - M6 atmosphere/VFX pass for M00 (Bible §4 hero shot: "parallax traffic layers and
volumetric rain beyond" the 6 m atrium glazing).

 - Rain: a generated streak texture (RawAssets/T_NV_RainStreaks.png) drives M_NV_RainSheet, a
   translucent panning sheet. Sheets are layered outside the glazing at several depths so the rain
   parallaxes as the player moves; far layers are fainter and slower (depth cue).
 - Flying traffic: ANVTrafficStream lanes (instanced light bodies) at several heights/depths.
 - Weapon VFX: Niagara Examples muzzle flash, tracer and impact on all three weapon data assets.
Re-runnable (folder FX_Atmosphere cleared first). Report: Saved/NV_m6_fx.txt
"""
import os
import unreal

REPORT = []
def log(*a):
    msg = " ".join(str(x) for x in a)
    REPORT.append(msg)
    unreal.log("[NV M6 fx] " + msg)

AT = unreal.AssetToolsHelpers.get_asset_tools()
EAL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
LES = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
V = unreal.Vector
FOLDER = "FX_Atmosphere"
TEXD = "/Game/NeonVeil/Textures/FX"
ART = "/Game/NeonVeil/Materials/Art"

def ensure_dir(p):
    if not EAL.does_directory_exist(p):
        EAL.make_directory(p)

def import_texture():
    path = f"{TEXD}/T_NV_RainStreaks"
    if EAL.does_asset_exist(path):
        return unreal.load_asset(path)
    src = os.path.join(unreal.Paths.project_dir(), "RawAssets", "T_NV_RainStreaks.png")
    ensure_dir(TEXD)
    t = unreal.AssetImportTask()
    t.set_editor_property("filename", os.path.abspath(src))
    t.set_editor_property("destination_path", TEXD)
    t.set_editor_property("replace_existing", True)
    t.set_editor_property("automated", True)
    t.set_editor_property("save", True)
    AT.import_asset_tasks([t])
    tex = unreal.load_asset(path)
    tex.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_GRAYSCALE)
    tex.set_editor_property("srgb", False)
    EAL.save_loaded_asset(tex, only_if_is_dirty=False)
    log("imported", path)
    return tex

def x(m, cls, px, py, **props):
    e = MEL.create_material_expression(m, cls, px, py)
    for k, v in props.items():
        e.set_editor_property(k, v)
    return e

def link(a, aout, b, bin_):
    if not MEL.connect_material_expressions(a, aout, b, bin_):
        log("WARN link", a.get_name(), aout, "->", b.get_name(), bin_)

def build_rain_material(tex):
    path = f"{ART}/M_NV_RainSheet"
    if EAL.does_asset_exist(path):
        EAL.delete_asset(path)
    m = AT.create_asset("M_NV_RainSheet", ART, unreal.Material, unreal.MaterialFactoryNew())
    m.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
    m.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    m.set_editor_property("two_sided", True)
    sp = lambda n, v, py: x(m, unreal.MaterialExpressionScalarParameter, -1200, py, parameter_name=n, default_value=v)
    tu, tv = sp("TilingU", 20.0, -200), sp("TilingV", 6.0, -100)
    speed = sp("FallSpeed", 1.6, 0)
    uv = x(m, unreal.MaterialExpressionTextureCoordinate, -1200, -350)
    tiling = x(m, unreal.MaterialExpressionAppendVector, -1000, -150)
    link(tu, "", tiling, "A"); link(tv, "", tiling, "B")
    uvs = x(m, unreal.MaterialExpressionMultiply, -850, -300)
    link(uv, "", uvs, "A"); link(tiling, "", uvs, "B")
    time = x(m, unreal.MaterialExpressionTime, -1000, 100)
    fall = x(m, unreal.MaterialExpressionMultiply, -850, 80)
    link(time, "", fall, "A"); link(speed, "", fall, "B")
    zero = x(m, unreal.MaterialExpressionConstant, -850, 180, r=0.0)
    off = x(m, unreal.MaterialExpressionAppendVector, -700, 120)
    link(zero, "", off, "A"); link(fall, "", off, "B")
    pan = x(m, unreal.MaterialExpressionSubtract, -600, -200)
    link(uvs, "", pan, "A"); link(off, "", pan, "B")
    s = x(m, unreal.MaterialExpressionTextureSampleParameter2D, -400, -200, parameter_name="Streaks", texture=tex,
          sampler_type=unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_GRAYSCALE)
    link(pan, "", s, "UVs")
    col = x(m, unreal.MaterialExpressionVectorParameter, -400, 50, parameter_name="RainColor",
            default_value=unreal.LinearColor(0.55, 0.65, 0.8, 1))
    bright = sp("Brightness", 1.2, 150)
    e1 = x(m, unreal.MaterialExpressionMultiply, -150, 0)
    link(col, "", e1, "A"); link(s, "R", e1, "B")
    e2 = x(m, unreal.MaterialExpressionMultiply, 0, 0)
    link(e1, "", e2, "A"); link(bright, "", e2, "B")
    MEL.connect_material_property(e2, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    op = sp("Opacity", 0.35, 250)
    o1 = x(m, unreal.MaterialExpressionMultiply, -150, 250)
    link(s, "R", o1, "A"); link(op, "", o1, "B")
    fade = x(m, unreal.MaterialExpressionDepthFade, 0, 250)
    link(o1, "", fade, "Opacity")
    MEL.connect_material_property(fade, "", unreal.MaterialProperty.MP_OPACITY)
    MEL.recompile_material(m)
    EAL.save_loaded_asset(m, only_if_is_dirty=False)
    log("built", path)
    return m

def mi(name, parent, scalars, vectors=None):
    path = f"{ART}/{name}"
    if EAL.does_asset_exist(path):
        EAL.delete_asset(path)
    inst = AT.create_asset(name, ART, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    MEL.set_material_instance_parent(inst, parent)
    for k, v in scalars.items():
        MEL.set_material_instance_scalar_parameter_value(inst, k, v)
    for k, v in (vectors or {}).items():
        MEL.set_material_instance_vector_parameter_value(inst, k, unreal.LinearColor(v[0], v[1], v[2], 1))
    MEL.update_material_instance(inst)
    EAL.save_loaded_asset(inst, only_if_is_dirty=False)
    return inst

def emissive_mi(name, rgb, strength):
    return mi(name, unreal.load_asset(f"{ART}/M_NV_Emissive"), {"EmissiveStrength": strength}, {"EmissiveColor": rgb})

PLANE = unreal.load_asset("/Engine/BasicShapes/Plane")
CUBE = unreal.load_asset("/Engine/BasicShapes/Cube")

def sheet(label, center, width, height, mat, yaw=0.0):
    """Vertical rain sheet facing +/-Y (yaw 0) or +/-X (yaw 90)."""
    a = EAS.spawn_actor_from_class(unreal.StaticMeshActor, V(*center), unreal.Rotator(roll=90.0, yaw=yaw))
    c = a.static_mesh_component
    c.set_static_mesh(PLANE)
    c.set_material(0, mat)
    c.set_editor_property("cast_shadow", False)
    c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    a.set_actor_scale3d(V(width / 100.0, height / 100.0, 1.0))
    a.set_actor_label(label)
    a.set_folder_path(FOLDER)
    return a

def main():
    for a in EAS.get_all_level_actors():
        if str(a.get_folder_path()) == FOLDER:
            EAS.destroy_actor(a)

    # ---------------- rain
    tex = import_texture()
    rain = build_rain_material(tex)
    layers = [  # (depth beyond glass cm, opacity, brightness, fall speed, tiling per 100 m)
        (250, 0.8, 8.0, 2.2, 1.0),
        (1400, 0.6, 5.0, 1.7, 0.8),
        (4000, 0.45, 3.0, 1.2, 0.55),
    ]
    for i, (d, op, br, sp, til) in enumerate(layers):
        m = mi(f"MI_NV_Rain_L{i}", rain, {"Opacity": op, "Brightness": br, "FallSpeed": sp,
                                          "TilingU": 120.0 * til, "TilingV": 18.0 * til})
        h = 9000.0
        # Sheets must stay outside every room: the sim suite occupies x 6300..10300, y -1500..1500
        # (east of the atrium glazing) and the atrium x 3500..6300, y -1100..1100.
        if d < 400:
            ax0, ax1 = 2000.0, 6290.0          # atrium-north near layer stops at the sim suite wall
            bx0, bx1 = -2000.0, 3480.0         # skybridge near layers stop at the atrium wall
        else:
            ax0, ax1 = -8000.0, 18000.0
            bx0, bx1 = -8000.0, 3480.0 if 300 + d < 1100 else 12000.0
        sheet(f"Rain_AtriumN_L{i}", ((ax0 + ax1) / 2, 1100 + d, 600), ax1 - ax0, h, m)
        sheet(f"Rain_BridgeS_L{i}", ((bx0 + bx1) / 2, -300 - d, 600), bx1 - bx0, h, m)
        if 300 + d >= 1100 + 400:
            continue                            # north bridge layers beyond the atrium line are covered above
        sheet(f"Rain_BridgeN_L{i}", ((bx0 + bx1) / 2, 300 + d, 600), bx1 - bx0, h, m)
    log("rain sheets placed")

    # ---------------- flying traffic
    cls = getattr(unreal, "NVTrafficStream", None)
    if cls is None:
        log("NVTrafficStream class missing: rebuild C++ first")
    else:
        head = emissive_mi("MI_NV_TrafficHead", (1.0, 0.92, 0.8), 60.0)
        tail = emissive_mi("MI_NV_TrafficTail", (1.0, 0.08, 0.05), 45.0)
        cyan = emissive_mi("MI_NV_TrafficCyan", (0.2, 0.9, 1.0), 50.0)
        lanes = [  # (y, z, cars, speed min/max, mats)
            (22000, -3500, 110, (3500, 6500), (head, tail)),
            (38000, 1800, 70, (4500, 8000), (cyan, tail)),
            (55000, -9000, 160, (3000, 6000), (head, tail)),
            (80000, 4500, 90, (5000, 9000), (head, cyan)),
            (-30000, -5000, 120, (3500, 6500), (head, tail)),
            (-60000, 2500, 80, (4500, 8000), (cyan, tail)),
        ]
        for i, (y, z, n, spd, (fm, rm)) in enumerate(lanes):
            a = EAS.spawn_actor_from_class(cls, V(-100000, y, z), unreal.Rotator())
            a.set_editor_property("lane_length", 220000.0)
            a.set_editor_property("vehicles_per_direction", n)
            a.set_editor_property("speed_range", unreal.Vector2D(spd[0], spd[1]))
            a.set_editor_property("lane_spread", unreal.Vector2D(900.0 + abs(y) * 0.01, 400.0))
            a.set_editor_property("vehicle_scale", V(4.0, 1.4, 0.8) * (1.0 + abs(y) / 60000.0))
            a.set_editor_property("seed", 11 + i)
            a.set_editor_property("vehicle_mesh", CUBE)
            a.set_editor_property("forward_material", fm)
            a.set_editor_property("reverse_material", rm)
            a.set_actor_label(f"Traffic_Lane{i}")
            a.set_folder_path(FOLDER)
            a.post_edit_move(True) if hasattr(a, "post_edit_move") else a.set_actor_location(V(-100000, y, z + 1), False, False)
        log("traffic lanes placed:", len(lanes))

    # ---------------- weapon VFX
    NE = "/Game/NiagaraExamples/FX_Weapons"
    flash = unreal.load_asset(f"{NE}/MuzzleFlashes/NS_MuzzleFlash")
    tracer = unreal.load_asset(f"{NE}/Trails/NS_BulletTracer")
    impact = unreal.load_asset(f"{NE}/Impacts/NS_Impact_Metal")
    hit = unreal.load_asset("/Game/SciFiUISFX/Cues/Impacts/Impact_2_Top_End_Cue")
    for n in ("DA_Weapon_VX9", "DA_Weapon_Kestrel", "DA_Weapon_Harrow"):
        w = unreal.load_asset(f"/Game/NeonVeil/Data/Weapons/{n}")
        if not w:
            continue
        if flash:
            w.set_editor_property("muzzle_flash", flash)
        if tracer:
            w.set_editor_property("tracer", tracer)
        if impact:
            w.set_editor_property("impact_effect", impact)
        if hit:
            w.set_editor_property("hit_confirm_sound", hit)
        EAL.save_loaded_asset(w, only_if_is_dirty=False)
        log("weapon fx ->", n)
    LES.save_current_level()

try:
    main()
finally:
    with open(unreal.Paths.project_saved_dir() + "NV_m6_fx.txt", "w", encoding="utf-8") as fh:
        fh.write("\n".join(REPORT))
