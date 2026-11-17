"""Prologue: the sky car parked outside the Veyra Central transit hub (ANVSkyCarLiftoff, build ga46+).
Imports the converted Fab "Cyberpunk Hovercar" (atiqa, Standard licence; converted in Blender: nose +X, 5.4 m, canopy
split off with its hinge as pivot) from Saved/Fab/SkyCar into /Game/NeonVeil/Fab/SkyCar (gitignored), builds its
materials on M_NV_SkyCar (Glow parameter drives strips/thrusters), places the car, a driver NPC (a copy of a street
citizen) who boards it, the ElevenLabs sounds and Ghost-7's lines. Idempotent. Args: [nofbx]. Report: Saved/NV_skycar.txt"""
import os, sys
import unreal
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
LES = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
EAL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary
AT = unreal.AssetToolsHelpers.get_asset_tools()
V, R = unreal.Vector, unreal.Rotator
OUT = []
def log(*a): OUT.append(" ".join(str(x) for x in a))
ARGS = [a for a in sys.argv[1:] if not a.endswith(".py")]
PROJ = unreal.Paths.project_dir()
SRC = os.path.join(PROJ, "Saved", "Fab", "SkyCar")
DST = "/Game/NeonVeil/Fab/SkyCar"
MAT_DIR = "/Game/NeonVeil/Materials/Vehicles"
AUD = "/Game/NeonVeil/Audio/SkyCar"
MAP = "/Game/NeonVeil/Maps/M00/L_M00_Prologue"
ZS = -12000.0
CAR_LOC, CAR_YAW = (6430.0, -8180.0), -90.0          # west kerb just north of the second crosswalk, nose south toward the player
CAR_SCALE = 1.3                                      # 7 m long, 2.2 m tall: a big, expensive machine
XW1, XW2 = -13400.0, -9000.0                         # crosswalk centre lines (6 m deep)
FOLDER = "P_Street/SkyCar"

def imp(file, dest, name, **opts):
    t = unreal.AssetImportTask()
    t.filename = file; t.destination_path = dest; t.destination_name = name
    t.replace_existing = True; t.automated = True; t.save = True
    AT.import_asset_tasks([t])
    return unreal.load_asset(f"{dest}/{name}")

def master():
    path = f"{MAT_DIR}/M_NV_SkyCar"
    if EAL.does_asset_exist(path):
        return unreal.load_asset(path)
    m = AT.create_asset("M_NV_SkyCar", MAT_DIR, unreal.Material, unreal.MaterialFactoryNew())
    white = unreal.load_asset("/Engine/EngineResources/WhiteSquareTexture")
    def tex(name, x, y):
        n = MEL.create_material_expression(m, unreal.MaterialExpressionTextureSampleParameter2D, x, y)
        n.set_editor_property("parameter_name", name); n.set_editor_property("texture", white)
        return n
    def vec(name, val, x, y):
        n = MEL.create_material_expression(m, unreal.MaterialExpressionVectorParameter, x, y)
        n.set_editor_property("parameter_name", name); n.set_editor_property("default_value", unreal.LinearColor(*val)); return n
    def sca(name, val, x, y):
        n = MEL.create_material_expression(m, unreal.MaterialExpressionScalarParameter, x, y)
        n.set_editor_property("parameter_name", name); n.set_editor_property("default_value", val); return n
    def mul(a, b, x, y, oa="", ob=""):
        n = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, x, y)
        MEL.connect_material_expressions(a, oa, n, "A"); MEL.connect_material_expressions(b, ob, n, "B"); return n
    base = mul(tex("BaseTex", -900, -300), vec("BaseTint", (1, 1, 1, 1), -900, -100), -500, -250, "RGB", "")
    MEL.connect_material_property(base, "", unreal.MaterialProperty.MP_BASE_COLOR)
    rough = mul(tex("RoughTex", -900, 100), sca("Roughness", 0.5, -900, 300), -500, 150, "R", "")
    MEL.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    MEL.connect_material_property(sca("Metallic", 0.0, -500, 350), "", unreal.MaterialProperty.MP_METALLIC)
    e1 = mul(tex("EmisTex", -900, 500), vec("EmissiveColor", (0, 0, 0, 1), -900, 700), -600, 600, "RGB", "")
    e2 = mul(e1, sca("Glow", 0.0, -600, 800), -350, 650)
    MEL.connect_material_property(e2, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    MEL.recompile_material(m)
    EAL.save_loaded_asset(m)
    return m

def mi(name, parent, scalars=None, vectors=None, textures=None):
    path = f"{DST}/{name}"
    x = unreal.load_asset(path) if EAL.does_asset_exist(path) else AT.create_asset(name, DST, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    MEL.set_material_instance_parent(x, parent)
    for k, v in (scalars or {}).items(): MEL.set_material_instance_scalar_parameter_value(x, k, v)
    for k, v in (vectors or {}).items(): MEL.set_material_instance_vector_parameter_value(x, k, unreal.LinearColor(*v))
    for k, v in (textures or {}).items():
        if v: MEL.set_material_instance_texture_parameter_value(x, k, v)
    MEL.update_material_instance(x); EAL.save_loaded_asset(x)
    return x

def slot_material(slot, mats):
    s = slot.lower()
    for key, m in (("gloss", "Paint"), ("cdp_body", "Glass"), ("cdp_metal", "Metal"), ("cdp_plastic", "Plastic"),
                   ("paint", "Accent"), ("thruster", "Thruster"), ("white", "Light"), ("material", "Dark")):
        if key in s:
            return mats[m]
    return mats["Dark"]

def line(speaker, text, dur):
    l = unreal.NVSubtitleLine()
    l.set_editor_property("speaker", unreal.Text(speaker)); l.set_editor_property("text", unreal.Text(text))
    l.set_editor_property("duration", dur); l.set_editor_property("as_comms", False)
    return l

def ground(x, y):
    w = unreal.EditorLevelLibrary.get_editor_world()
    hit = unreal.SystemLibrary.line_trace_single(w, V(x, y, ZS + 600), V(x, y, ZS - 400), unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,
                                                 True, [], unreal.DrawDebugTrace.NONE, True)
    if hit:
        vs = [v for v in hit.to_tuple() if isinstance(v, unreal.Vector)]
        if vs: return vs[0].z
    return ZS

try:
    if not unreal.EditorLevelLibrary.get_editor_world().get_path_name().startswith(MAP):
        LES.load_level(MAP)
    # --- meshes + textures
    T = {}
    for n in ("Metal_D", "Metal_R", "Plastic_D", "Light_E", "Body_R"):
        f = os.path.join(SRC, f"T_NV_SkyCar_{n}.png")
        T[n] = imp(f, f"{DST}/Textures", f"T_NV_SkyCar_{n}") if os.path.exists(f) else None
    if "nofbx" not in ARGS:
        for n in ("SM_NV_SkyCar_Body", "SM_NV_SkyCar_Canopy"):
            imp(os.path.join(SRC, n + ".fbx"), DST, n)
    body = unreal.load_asset(f"{DST}/SM_NV_SkyCar_Body"); canopy = unreal.load_asset(f"{DST}/SM_NV_SkyCar_Canopy")
    b = body.get_bounding_box()
    log("body bounds", b.min, b.max, "slots", [str(s.material_slot_name) for s in body.static_materials])
    # --- materials
    M = master()
    mats = {
        "Paint": mi("MI_NV_SkyCar_Paint", M, {"Metallic": 0.85, "Roughness": 0.2}, {"BaseTint": (0.010, 0.011, 0.014, 1)}),
        "Glass": mi("MI_NV_SkyCar_Glass", M, {"Metallic": 0.2, "Roughness": 0.04}, {"BaseTint": (0.004, 0.005, 0.007, 1)}),
        "Metal": mi("MI_NV_SkyCar_Metal", M, {"Metallic": 0.9, "Roughness": 0.85}, {"BaseTint": (1.3, 1.3, 1.3, 1)}, {"BaseTex": T["Metal_D"], "RoughTex": T["Metal_R"]}),
        "Plastic": mi("MI_NV_SkyCar_Plastic", M, {"Metallic": 0.0, "Roughness": 0.55}, {"BaseTint": (0.8, 0.8, 0.8, 1)}, {"BaseTex": T["Plastic_D"]}),
        "Accent": mi("MI_NV_SkyCar_Accent", M, {"Metallic": 0.9, "Roughness": 0.28}, {"BaseTint": (0.02, 0.09, 0.13, 1), "EmissiveColor": (0.0, 1.2, 1.8, 1)}),
        "Thruster": mi("MI_NV_SkyCar_Thruster", M, {"Metallic": 0.0, "Roughness": 0.3}, {"BaseTint": (0.0, 0.3, 0.45, 1), "EmissiveColor": (2.0, 14.0, 24.0, 1)}),
        "Light": mi("MI_NV_SkyCar_Light", M, {"Metallic": 0.0, "Roughness": 0.2}, {"BaseTint": (0.6, 0.6, 0.6, 1), "EmissiveColor": (30.0, 30.0, 34.0, 1)}, {"EmisTex": None}),
        "Dark": mi("MI_NV_SkyCar_Dark", M, {"Metallic": 0.3, "Roughness": 0.5}, {"BaseTint": (0.01, 0.012, 0.015, 1)}),
    }
    for mesh in (body, canopy):
        for i, s in enumerate(mesh.static_materials):
            mesh.set_material(i, slot_material(str(s.material_slot_name), mats))
        EAL.save_loaded_asset(mesh)

    # --- sounds (ElevenLabs, Art/Audio/SkyCar)
    snd = {}
    for n, loop in (("SW_NV_SkyCar_Canopy", False), ("SW_NV_SkyCar_PowerUp", False), ("SW_NV_SkyCar_Idle", True), ("SW_NV_SkyCar_Liftoff", False)):
        f = os.path.join(PROJ, "Art", "Audio", "SkyCar", n + ".wav")
        if os.path.exists(f):
            w = imp(f, AUD, n); w.set_editor_property("looping", loop); EAL.save_loaded_asset(w); snd[n] = w
    att_path = f"{AUD}/ATT_NV_SkyCar"
    att = unreal.load_asset(att_path) if EAL.does_asset_exist(att_path) else AT.create_asset("ATT_NV_SkyCar", AUD, unreal.SoundAttenuation, unreal.SoundAttenuationFactory())
    st = att.get_editor_property("attenuation")
    st.set_editor_property("falloff_distance", 9000.0)
    st.set_editor_property("attenuation_shape_extents", V(400, 0, 0))
    att.set_editor_property("attenuation", st); EAL.save_loaded_asset(att)

    # --- the car
    for a in EAS.get_all_level_actors():
        if str(a.get_folder_path()) == FOLDER:
            a.destroy_actor()
    gz = ground(*CAR_LOC)
    car = EAS.spawn_actor_from_class(unreal.NVSkyCarLiftoff, V(CAR_LOC[0], CAR_LOC[1], gz + 4), R(yaw=CAR_YAW))
    car.set_actor_label("SkyCar_Liftoff"); car.set_folder_path(FOLDER)
    car.get_editor_property("car_root").set_relative_scale3d(V(CAR_SCALE, CAR_SCALE, CAR_SCALE))
    car.get_editor_property("body").set_static_mesh(body)
    cp = car.get_editor_property("canopy"); cp.set_static_mesh(canopy)
    sp = lambda k, v: car.set_editor_property(k, v)
    sp("canopy_sound", snd.get("SW_NV_SkyCar_Canopy")); sp("power_up_sound", snd.get("SW_NV_SkyCar_PowerUp"))
    sp("hum_sound", snd.get("SW_NV_SkyCar_Idle")); sp("liftoff_sound", snd.get("SW_NV_SkyCar_Liftoff")); sp("attenuation", att)
    fx = None
    for p in ("/Game/NiagaraExamples/FX_Smoke/NS_Smoke_Plume",):
        fx = unreal.load_asset(p) if EAL.does_asset_exist(p) else fx
    sp("lift_dust_fx", fx); sp("lift_dust_scale", 1.6)
    # merge into the southbound street lane (Sky_Street_A_S: x 6046, z -7800, heading -Y), right over the player's head
    sp("join_point", V(6046, -11800, -7800)); sp("join_direction", V(0, -1, 0))
    # lights wake as Ghost clears the first crosswalk; liftoff as he steps onto the second (car is just past it)
    sp("progress_direction", V(0, 1, 0))
    sp("lights_on_plane", V(7046, XW1 + 300, ZS)); sp("liftoff_plane", V(7046, XW2 - 300, ZS))
    sp("lights_on_distance", 100000.0); sp("liftoff_distance", 560.0)
    sp("min_idle_before_liftoff", 1.0); sp("spool_time", 0.9)
    sp("blocker_extent", V(480, 300, 380))
    sp("board_point", V(20, -200, 0)); sp("seat_point", V(20, -20, 50))
    sp("lines_on_lights_on", [line("Ghost-7", "Parked across a tram stop. Somebody's important.", 3.4)])
    sp("lines_on_liftoff", [line("Ghost-7", "That's Veyra. The money floats... the rest of us get the rain.", 4.6)])

    # --- driver: a copy of a street citizen, walking out of the hub to the kerb-side cockpit
    src = next((a for a in EAS.get_all_level_actors() if a.get_actor_label() == "NPC_St_E2"), None)
    if src:
        d = EAS.duplicate_actor(src)
        start = V(5650, -7450, ZS + 100)
        d.set_actor_location(start, False, False); d.set_actor_rotation(R(yaw=-45), False)
        d.set_actor_label("NPC_SkyCarDriver"); d.set_folder_path(FOLDER); d.tags = [unreal.Name("NVNPC")]
        board_local = car.get_editor_property("board_point")
        board = car.get_actor_transform().transform_location(board_local)
        d.set_editor_property("patrol_points", [V(board.x - start.x, board.y - start.y, 0)])
        d.set_editor_property("wait_time_range", unreal.Vector2D(60, 90))
        d.set_editor_property("walk_speed", 175.0)
        d.set_editor_property("glance_radius", 0.0)
        sp("driver", d)
        log("driver", d.get_actor_label(), "board", board)
    log("car", car.get_actor_location(), "ground", gz)
    LES.save_current_level()
    log("saved")
except Exception:
    import traceback
    log(traceback.format_exc())
open(unreal.Paths.project_saved_dir() + "NV_skycar.txt", "w").write("\n".join(OUT))
