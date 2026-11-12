"""NEON VEIL - Milestone 2: M00 'The Glass Crown' graybox (Bible §4).

Builds /Game/NeonVeil/Maps/M00/L_M00_GlassCrown from scratch at the Bible's dimensions:
  A  Arrival tram / skybridge   35 m long            x    0 .. 3500
  B  Security atrium            28 x 22 x 12 m       x 3500 .. 6300
  C  Combat simulation suite    40 x 30 m            x 6300 .. 10300
  D  Operations gallery         45 m corridor        x10300 .. 14800
  E  Director antechamber       16 x 14 m            x14800 .. 16400
plus DA_Mission_M00 (M00-O01..O04), BP_NVGameMode_M00, checkpoints, gated doors, the scan arch,
the simulation director, holo-table, biometric panel and optional world-building interactions.

All geometry here is graybox (engine cubes + TEMP_ materials). It is replaced in the art pass.
Re-runnable: the map is rebuilt each run. Report: Saved/NV_setup_m00.txt
"""
import unreal

REPORT = []
def log(*a):
    msg = " ".join(str(x) for x in a)
    REPORT.append(msg)
    unreal.log("[NV M00] " + msg)

AT = unreal.AssetToolsHelpers.get_asset_tools()
EAL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary
LES = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

def ensure_dir(p):
    if not EAL.does_directory_exist(p):
        EAL.make_directory(p)

def get_or_create(name, folder, cls, factory):
    path = f"{folder}/{name}"
    if EAL.does_asset_exist(path):
        return unreal.load_asset(path)
    ensure_dir(folder)
    a = AT.create_asset(name, folder, cls, factory)
    log("created", path)
    return a

def tag(n):
    t = unreal.GameplayTag()
    t.import_text(f'(TagName="{n}")')
    return t

def T(s):
    return unreal.Text(s)

def line(speaker, text, dur=3.8):
    l = unreal.NVSubtitleLine()
    l.set_editor_property("speaker", T(speaker))
    l.set_editor_property("text", T(text))
    l.set_editor_property("duration", dur)
    return l

def V(x, y, z):
    return unreal.Vector(x, y, z)

def R(pitch=0.0, yaw=0.0, roll=0.0):
    return unreal.Rotator(pitch=pitch, yaw=yaw, roll=roll)

# ------------------------------------------------------------------ TEMP materials
MAT = "/Game/NeonVeil/Tests/Materials"
def make_material(name, base, emissive=None, rough=0.5, metal=0.0, opacity=None):
    path = f"{MAT}/{name}"
    if EAL.does_asset_exist(path):
        return unreal.load_asset(path)
    m = get_or_create(name, MAT, unreal.Material, unreal.MaterialFactoryNew())
    if opacity is not None:
        m.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
        m.set_editor_property("translucency_lighting_mode", unreal.TranslucencyLightingMode.TLM_SURFACE)
    def const3(rgb, y, prop):
        e = MEL.create_material_expression(m, unreal.MaterialExpressionConstant3Vector, -400, y)
        e.set_editor_property("constant", unreal.LinearColor(rgb[0], rgb[1], rgb[2], 1))
        MEL.connect_material_property(e, "", prop)
    def const1(v, y, prop):
        e = MEL.create_material_expression(m, unreal.MaterialExpressionConstant, -400, y)
        e.set_editor_property("r", v)
        MEL.connect_material_property(e, "", prop)
    const3(base, 0, unreal.MaterialProperty.MP_BASE_COLOR)
    if emissive:
        const3(emissive, 150, unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    const1(rough, 300, unreal.MaterialProperty.MP_ROUGHNESS)
    const1(metal, 400, unreal.MaterialProperty.MP_METALLIC)
    if opacity is not None:
        const1(opacity, 500, unreal.MaterialProperty.MP_OPACITY)
    MEL.recompile_material(m)
    EAL.save_loaded_asset(m)
    return m

M_WHITE = make_material("TEMP_M_CrownCeramic", (0.72, 0.74, 0.76), None, 0.35)
M_FLOOR = make_material("TEMP_M_CrownFloor_v2", (0.30, 0.31, 0.33), None, 0.5, 0.0)
M_DARK = make_material("TEMP_M_Titanium", (0.06, 0.065, 0.07), None, 0.3, 1.0)
M_GLASS = make_material("TEMP_M_Glass", (0.02, 0.03, 0.035), None, 0.05, 0.0, opacity=0.18)
M_DARKGLASS = make_material("TEMP_M_DarkGlass", (0.005, 0.006, 0.008), None, 0.03, 0.0)
M_CYAN = make_material("TEMP_M_CyanEmissive", (0.0, 0.0, 0.0), (0.2, 1.6, 2.4), 0.5)
M_DATA = make_material("TEMP_M_DataWall", (0.0, 0.0, 0.0), (0.15, 0.6, 1.0), 0.5)
M_CITY = make_material("TEMP_M_CityBlock", (0.015, 0.016, 0.02), None, 0.6)
M_CITYLIT = make_material("TEMP_M_CityWindows", (0.0, 0.0, 0.0), (1.4, 0.9, 0.5), 0.6)
M_TERMINAL = unreal.load_asset(f"{MAT}/TEMP_M_Terminal")
M_CONE = make_material("TEMP_M_ConeVis", (0.0, 0.0, 0.0), (1.6, 0.12, 0.08), 0.5, 0.0, opacity=0.12)
M_PAD = make_material("TEMP_M_DrillPad", (0.0, 0.0, 0.0), (0.2, 1.2, 1.8), 0.5)

CUBE = unreal.load_asset("/Engine/BasicShapes/Cube")
CYL = unreal.load_asset("/Engine/BasicShapes/Cylinder")
SPHERE = unreal.load_asset("/Engine/BasicShapes/Sphere")

# ------------------------------------------------------------------ mission data
f = unreal.DataAssetFactory()
f.set_editor_property("data_asset_class", unreal.NVMissionData)
mission = get_or_create("DA_Mission_M00", "/Game/NeonVeil/Data/Missions", unreal.NVMissionData, f)
def obj(oid, text, event, prereq=None, policy=unreal.NVCheckpointPolicy.ON_COMPLETE):
    o = unreal.NVObjectiveDef()
    o.set_editor_property("objective_id", oid)
    o.set_editor_property("display_text", T(text))
    o.set_editor_property("completion_event_tag", tag(event))
    o.set_editor_property("prerequisites", [prereq] if prereq else [])
    o.set_editor_property("checkpoint_policy", policy)
    return o
mission.set_editor_property("mission_id", "M00")
mission.set_editor_property("mission_title", T("The Glass Crown"))
mission.set_editor_property("objectives", [
    obj("M00-O01", "Report to Directorate security", "NV.Event.M00.SecurityArchCleared"),
    obj("M00-O02", "Calibrate your combat suite", "NV.Event.M00.CalibrationComplete", "M00-O01"),
    obj("M00-O03", "Review your assignment", "NV.Event.M00.HoloTableReviewed", "M00-O02"),
    obj("M00-O04", "Meet the Director", "NV.Event.M00.BiometricScanStarted", "M00-O03", unreal.NVCheckpointPolicy.NONE),
])
EAL.save_loaded_asset(mission)

# ------------------------------------------------------------------ game mode
def make_bp(name, folder, parent):
    path = f"{folder}/{name}"
    if EAL.does_asset_exist(path):
        bp = unreal.load_asset(path)
    else:
        bf = unreal.BlueprintFactory()
        bf.set_editor_property("parent_class", parent)
        ensure_dir(folder)
        bp = AT.create_asset(name, folder, unreal.Blueprint, bf)
        log("created", path)
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    cls = EAL.load_blueprint_class(path)
    return bp, cls, unreal.get_default_object(cls)

pawn_cls = EAL.load_blueprint_class("/Game/NeonVeil/Core/BP_NVPlayerCharacter")
gbp, gcls, gcdo = make_bp("BP_NVGameMode_M00", "/Game/NeonVeil/Core", unreal.NVGameMode)
gcdo.set_editor_property("default_pawn_class", pawn_cls)
gcdo.set_editor_property("mission", mission)
EAL.save_loaded_asset(gbp)
target_cls = EAL.load_blueprint_class("/Game/NeonVeil/Tests/BP_NVTrainingTarget_Test")

# ------------------------------------------------------------------ level
MAP = "/Game/NeonVeil/Maps/M00/L_M00_GlassCrown"
ensure_dir("/Game/NeonVeil/Maps/M00")
if EAL.does_asset_exist(MAP):
    LES.load_level(MAP)
    for a in EAS.get_all_level_actors():
        if not isinstance(a, unreal.WorldSettings):
            EAS.destroy_actor(a)
else:
    LES.new_level(MAP)

def spawn(cls, label, loc, rot=None, folder=None):
    a = EAS.spawn_actor_from_class(cls, V(*loc), rot or R())
    a.set_actor_label(label)
    if folder:
        a.set_folder_path(folder)
    return a

def box(label, center, size, mat, folder="Graybox", rot=None, mesh=CUBE):
    a = spawn(unreal.StaticMeshActor, label, center, rot, folder)
    c = a.static_mesh_component
    c.set_static_mesh(mesh)
    a.set_actor_scale3d(V(size[0] / 100.0, size[1] / 100.0, size[2] / 100.0))
    c.set_material(0, mat)
    return a

def wall_x(label, x, y0, y1, z0, z1, mat, thick=40, openings=(), folder="Graybox"):
    """Wall across the X axis (spanning Y) with door openings [(y_center, width, height)]."""
    cuts = sorted(openings)
    y = y0
    i = 0
    for (yc, w, h) in cuts:
        a, b = yc - w / 2, yc + w / 2
        if a > y:
            box(f"{label}_{i}", (x, (y + a) / 2, (z0 + z1) / 2), (thick, a - y, z1 - z0), mat, folder); i += 1
        box(f"{label}_{i}_lintel", (x, yc, (z0 + h + z1) / 2), (thick, w, z1 - z0 - h), mat, folder); i += 1
        y = b
    if y < y1:
        box(f"{label}_{i}", (x, (y + y1) / 2, (z0 + z1) / 2), (thick, y1 - y, z1 - z0), mat, folder)

def wall_y(label, y, x0, x1, z0, z1, mat, thick=40, folder="Graybox"):
    box(label, ((x0 + x1) / 2, y, (z0 + z1) / 2), (x1 - x0, thick, z1 - z0), mat, folder)

def room(label, x0, x1, y0, y1, h, floor=M_FLOOR, ceil=M_WHITE, folder="Graybox"):
    box(f"{label}_Floor", ((x0 + x1) / 2, (y0 + y1) / 2, -20), (x1 - x0, y1 - y0, 40), floor, folder)
    box(f"{label}_Ceiling", ((x0 + x1) / 2, (y0 + y1) / 2, h + 20), (x1 - x0, y1 - y0, 40), ceil, folder)

def light(label, loc, lumens=6000, radius=1800, color=(1.0, 0.97, 0.93), folder="Lighting"):
    a = spawn(unreal.PointLight, label, loc, None, folder)
    lc = a.point_light_component
    lc.set_editor_property("intensity_units", unreal.LightUnits.LUMENS)
    lc.set_intensity(lumens)
    lc.set_attenuation_radius(radius)
    lc.set_light_color(unreal.LinearColor(*color, 1.0))
    return a

DOOR_H = 360

# ---------------- A. Arrival tram / skybridge (35 m)
FA = "A_Skybridge"
box("A_Floor", (1750, 0, -20), (3500, 600, 40), M_FLOOR, FA)
box("A_Roof", (1750, 0, 470), (3500, 600, 40), M_DARK, FA)
wall_y("A_Glass_L", -300, 0, 3500, 0, 450, M_GLASS, 10, FA)
wall_y("A_Glass_R", 300, 0, 3500, 0, 450, M_GLASS, 10, FA)
for i in range(8):
    x = 250 + i * 450
    box(f"A_Rib_L{i}", (x, -300, 225), (30, 30, 450), M_DARK, FA)
    box(f"A_Rib_R{i}", (x, 300, 225), (30, 30, 450), M_DARK, FA)
# Tram car: hollow shell, open toward the bridge, so the player starts standing inside it.
box("A_TramFloor", (-700, 0, -20), (1400, 700, 40), M_FLOOR, FA)
box("A_TramRoof", (-700, 0, 390), (1200, 520, 30), M_DARK, FA)
box("A_TramSide_L", (-700, -250, 195), (1200, 20, 390), M_DARK, FA)
box("A_TramSide_R", (-700, 250, 195), (1200, 20, 390), M_DARK, FA)
box("A_TramRear", (-1310, 0, 195), (20, 520, 390), M_DARK, FA)
for i in range(3):
    box(f"A_TramWindow_L{i}", (-1000 + i * 300, -238, 230), (220, 6, 110), M_GLASS, FA)
    box(f"A_TramWindow_R{i}", (-1000 + i * 300, 238, 230), (220, 6, 110), M_GLASS, FA)
light("A_TramLight", (-700, 0, 360), 1200, 700, (0.85, 0.95, 1.0))
for i in range(4):
    light(f"A_Light{i}", (400 + i * 850, 0, 420), 2500, 900, (0.85, 0.95, 1.0))
ps = spawn(unreal.PlayerStart, "PlayerStart_TramExit", (-650, 0, 100), R(yaw=0), FA)

# ---------------- B. Security atrium (28 x 22 x 12 m)
FB = "B_Atrium"
room("B", 3500, 6300, -1100, 1100, 1200, folder=FB)
wall_x("B_Wall_West", 3500, -1100, 1100, 0, 1200, M_WHITE, 40, [(0, 600, 450)], FB)
wall_x("B_Wall_East", 6300, -1100, 1100, 0, 1200, M_WHITE, 40, [(0, 420, DOOR_H)], FB)
wall_y("B_Wall_South", -1100, 3500, 6300, 0, 1200, M_WHITE, 40, FB)
# North wall: 6 m high glazing onto the skyline (hero shot), solid above.
wall_y("B_Glazing", 1100, 3500, 6300, 0, 600, M_GLASS, 10, FB)
wall_y("B_Wall_North_Upper", 1100, 3500, 6300, 600, 1200, M_WHITE, 40, FB)
for i in range(7):
    box(f"B_Mullion{i}", (3500 + 400 * i, 1100, 300), (25, 25, 600), M_DARK, FB)
# Three-storey volume: mezzanine balconies on the south side.
for lvl, z in enumerate((400, 800)):
    box(f"B_Mezzanine{lvl}", (4900, -950, z), (2800, 300, 30), M_WHITE, FB)
    box(f"B_MezzRail{lvl}", (4900, -800, z + 55), (2800, 6, 80), M_GLASS, FB)
# Focal sculpture: stacked rings around a light column (TEMP form).
box("B_Sculpture_Column", (4900, 0, 450), (60, 60, 900), M_CYAN, FB, mesh=CYL)
for i, (z, s) in enumerate(((150, 520), (420, 440), (700, 360), (950, 260))):
    box(f"B_Sculpture_Ring{i}", (4900, 0, z), (s, s, 18), M_DARK, FB, mesh=CYL)
box("B_Sculpture_Plinth", (4900, 0, 20), (700, 700, 40), M_DARK, FB, mesh=CYL)
# Security scan arch in front of the suite door.
box("B_Arch_PostL", (5900, -230, 160), (60, 40, 320), M_DARK, FB)
box("B_Arch_PostR", (5900, 230, 160), (60, 40, 320), M_DARK, FB)
box("B_Arch_Header", (5900, 0, 335), (60, 500, 30), M_CYAN, FB)
box("B_Barrier_L", (5900, -700, 55), (40, 900, 110), M_GLASS, FB)
box("B_Barrier_R", (5900, 700, 55), (40, 900, 110), M_GLASS, FB)
arch = spawn(unreal.NVObjectiveTrigger, "B_SecurityArch_Scan", (5900, 0, 120), None, FB)
arch.get_editor_property("volume").set_box_extent(V(60, 200, 120))
arch.set_editor_property("event_tag", tag("NV.Event.M00.SecurityArchCleared"))
arch.set_editor_property("required_active_objective", "M00-O01")
arch.set_editor_property("delay", 1.6)
arch.set_editor_property("start_notice", T("Scanning..."))
arch.set_editor_property("complete_notice", T("Access confirmed: Ghost-7"))
arch.set_editor_property("lines_on_complete", [
    line("Security", "Clearance verified. Proceed to the simulation suite for calibration."),
])
for i, (x, y) in enumerate(((4200, -600), (4200, 600), (5600, -600), (5600, 600))):
    light(f"B_Light{i}", (x, y, 1050), 9000, 2600)
# Agency guards (Bible §4 "moving guards"; §8 archetype). Non-hostile in M00; placeholder mannequins.
GUARD_MESH = unreal.load_asset("/Game/Characters/Mannequins/Meshes/SKM_Manny_Simple")
GUARD_ANIM = unreal.load_object(None, "/Game/Characters/Mannequins/Anims/Unarmed/ABP_Unarmed.ABP_Unarmed_C")
guard_immune = unreal.GameplayTagContainer()
guard_immune.import_text('(GameplayTags=((TagName="NV.Damage.Ballistic"),(TagName="NV.Damage.Training"),(TagName="NV.Damage.Melee")))')
def guard(label, loc, yaw, route, waits=(2.0, 4.0), speed=150.0):
    g = spawn(unreal.NVGuardCharacter, label, loc, R(yaw=yaw), FB)
    g.set_editor_property("body_mesh_asset", GUARD_MESH)
    g.set_editor_property("body_anim_class", GUARD_ANIM)
    # Route points are relative to the spawn point; convert from world for readability.
    import math
    c, s_ = math.cos(math.radians(-yaw)), math.sin(math.radians(-yaw))
    rel = []
    for (wx, wy) in route:
        dx, dy = wx - loc[0], wy - loc[1]
        rel.append(V(dx * c - dy * s_, dx * s_ + dy * c, 0))
    g.set_editor_property("patrol_points", rel)
    g.set_editor_property("wait_time_range", unreal.Vector2D(waits[0], waits[1]))
    g.set_editor_property("walk_speed", speed)
    g.get_editor_property("health").set_editor_property("immune_damage_types", guard_immune)
    return g
# Loop around the sculpture; second guard paces the glazing; third holds the arch.
guard("B_Guard_Loop", (4100, -650, 100), 0, [(4100, -650), (5600, -650), (5600, 650), (4100, 650)])
guard("B_Guard_Glazing", (3900, 880, 100), 0, [(3900, 880), (5300, 880)], waits=(3.0, 6.0), speed=120.0)
guard("B_Guard_Arch", (5750, 330, 100), 180, [(5750, 330), (5750, 620)], waits=(4.0, 7.0), speed=110.0)
nav = spawn(unreal.NavMeshBoundsVolume, "B_NavBounds", (4900, 0, 300), None, FB)
nav.set_actor_scale3d(V(2800 / 200.0, 2200 / 200.0, 800 / 200.0))
light("B_Sculpture_Light", (4900, 0, 300), 3000, 900, (0.6, 0.9, 1.0))

# ---------------- C. Combat simulation suite (40 x 30 m)
FC = "C_SimSuite"
room("C", 6300, 10300, -1500, 1500, 900, folder=FC)
wall_x("C_Wall_East", 10300, -1500, 1500, 0, 900, M_WHITE, 40, [(0, 420, DOOR_H)], FC)
wall_y("C_Wall_South", -1500, 6300, 10300, 0, 900, M_WHITE, 40, FC)
wall_y("C_Wall_North", 1500, 6300, 10300, 0, 900, M_WHITE, 40, FC)
wall_x("C_Wall_West_Fill", 6300, -1500, -1100, 0, 900, M_WHITE, 40, (), FC)
wall_x("C_Wall_West_Fill2", 6300, 1100, 1500, 0, 900, M_WHITE, 40, (), FC)
box("C_Wall_West_Upper", (6300, 0, 1050), (40, 2200, 300), M_WHITE, FC)
# Two lanes split by a divider with gaps.
for i, (x0, x1) in enumerate(((7200, 7900), (8300, 9000), (9400, 9900))):
    box(f"C_Divider{i}", ((x0 + x1) / 2, 0, 150), (x1 - x0, 40, 300), M_DARK, FC)
# Cover at Bible vault heights.
for i, (x, y, h) in enumerate(((7300, -800, 90), (7300, 800, 120), (8100, -500, 60), (8100, 600, 90),
                               (8800, -900, 120), (8800, 900, 60), (9300, -400, 90), (9300, 400, 120))):
    box(f"C_Cover{i}", (x, y, h / 2), (60, 220, h), M_WHITE, FC)
# Upper catwalk on the north side with a ramp.
box("C_Catwalk", (8550, 1300, 400), (2700, 360, 30), M_DARK, FC)
box("C_CatwalkRail", (8550, 1120, 455), (2700, 6, 80), M_GLASS, FC)
# Ramp rises 4 m over 8 m toward +X (26.6 deg, under the 46 deg walkable limit).
box("C_CatwalkRamp", (6800, 1300, 200), (895, 360, 30), M_DARK, FC, R(pitch=26.57))
for i in range(6):
    light(f"C_Light{i}", (6900 + (i % 3) * 1300, -700 if i < 3 else 700, 850), 9000, 2200)
# Targets (holographic TEMP): 3 moving, 2 shielded. Hidden until their step.
t_moving, t_shield = [], []
# Targets face the player (yaw 180), so local +Y patrol is world -Y.
# Each patrol stays inside its lane (the divider sits on y = 0).
for i, (x, y, py) in enumerate(((7800, -1100, -700), (8300, 300, -800), (8900, -350, 750))):
    t = spawn(target_cls, f"C_Target_Moving{i}", (x, y, 0), R(yaw=180), FC)
    t.set_editor_property("patrol_offset", V(0, py, 0))
    t_moving.append(t)
# Shielded targets ~19 m out, after the ADS step has been taught; weak point enlarged.
for i, (x, y) in enumerate(((8700, -800), (8700, 800))):
    t = spawn(target_cls, f"C_Target_Shielded{i}", (x, y, 0), R(yaw=180), FC)
    t.get_editor_property("health").set_editor_property("max_shield", 60.0)
    t.get_editor_property("weak_point").set_editor_property("relative_scale3d", V(0.7, 0.7, 0.3))
    t_shield.append(t)

# Sentry drone target (Bible: 1 drone): hovering disc with a glowing stabilizer core underneath.
t_drone = spawn(target_cls, "C_Target_Drone", (9200, 600, 380), R(yaw=180), FC)  # ~4.6 m: clear of the 3 m dividers
t_drone.set_editor_property("patrol_offset", V(0, 1200, 0))   # local +Y = world -Y (yaw 180)
t_drone.set_editor_property("patrol_speed", 220.0)
t_drone.set_editor_property("bob_amplitude", 35.0)
t_drone.get_editor_property("health").set_editor_property("max_health", 80.0)
t_drone.get_editor_property("body").set_editor_property("relative_scale3d", V(1.0, 1.0, 0.25))
core = t_drone.get_editor_property("weak_point")
core.set_editor_property("relative_scale3d", V(0.3, 0.3, 1.2))
core.set_editor_property("relative_location", V(0, 0, -110))

# Cover drill (north lane, near the entrance): barrier, area behind it, emitter at the far wall.
box("C_DrillBarrier", (7050, 700, 65), (60, 400, 130), M_WHITE, FC)
def area(label, center, size, folder=FC):
    a = spawn(unreal.TriggerBox, label, center, None, folder)
    a.get_component_by_class(unreal.BoxComponent).set_box_extent(V(size[0] / 2, size[1] / 2, size[2] / 2))
    return a
a_cover = area("C_Area_Cover", (6880, 700, 100), (220, 380, 200))
emitter = spawn(unreal.NVSimVolleyEmitter, "C_VolleyEmitter", (9850, 700, 280), None, FC)
emitter.set_editor_property("spread_deg", 0.3)
# Shield drill: exposed pad in the north lane.
box("C_ShieldPad", (7700, 950, 2), (200, 200, 4), M_PAD, FC)
a_shield = area("C_Area_Shield", (7700, 950, 100), (200, 200, 200))

# Baton dummy: gunfire (training and live rounds) doesn't register, 300 HP so the takedown is the practical answer.
t_dummy = spawn(target_cls, "C_Target_MeleeDummy", (7000, 350, 0), R(yaw=180), FC)
dh = t_dummy.get_editor_property("health")
dh.set_editor_property("max_health", 300.0)
imm = unreal.GameplayTagContainer()
imm.import_text('(GameplayTags=((TagName="NV.Damage.Ballistic"),(TagName="NV.Damage.Training")))')
dh.set_editor_property("immune_damage_types", imm)

# Drone-uplink drill: walled enclosure (open top, 2.0 m) in the south lane with 3 concealed profiles.
EX0, EX1, EY0, EY1, EH = 9400, 10000, -1350, -650, 200
box("C_Enclosure_N", ((EX0 + EX1) / 2, EY1, EH / 2), (EX1 - EX0, 30, EH), M_DARK, FC)
box("C_Enclosure_S", ((EX0 + EX1) / 2, EY0, EH / 2), (EX1 - EX0, 30, EH), M_DARK, FC)
box("C_Enclosure_W", (EX0, (EY0 + EY1) / 2, EH / 2), (30, EY1 - EY0, EH), M_DARK, FC)
box("C_Enclosure_E", (EX1, (EY0 + EY1) / 2, EH / 2), (30, EY1 - EY0, EH), M_DARK, FC)
t_hidden = []
for i, (x, y) in enumerate(((9720, -950), (9820, -1150), (9860, -820))):
    t_hidden.append(spawn(target_cls, f"C_Target_Concealed{i}", (x, y, 0), R(yaw=180), FC))

# Optical-disruption drill: camera on the east wall watching the catwalk; terminal at the far end.
cam = spawn(unreal.NVSurveillanceCamera, "C_SurveillanceCamera", (10230, 1300, 750), R(pitch=-10, yaw=180), FC)
cam.set_editor_property("view_distance", 2200.0)
cam.set_editor_property("half_angle", 14.0)
cam.set_editor_property("sweep_angle", 20.0)
cam.set_editor_property("sweep_period", 5.0)
cam.set_editor_property("cone_material", M_CONE)
term = spawn(unreal.NVInteractableActor, "C_RelayTerminal", (9820, 1380, 475), R(yaw=180), FC)  # mesh is the root: place the actor itself
tm = term.get_editor_property("mesh")
tm.set_static_mesh(CUBE)
tm.set_editor_property("relative_scale3d", V(0.5, 0.5, 1.2))
tm.set_material(0, M_TERMINAL)
term.set_editor_property("prompt", T("Bypass surveillance relay"))
term.set_editor_property("hold_duration", 1.0)
term.set_editor_property("single_use", False)
term.set_editor_property("required_active_objective", "M00-O02")
term.set_editor_property("completion_event_tag", tag("NV.Event.M00.SurveillanceBypassed"))
reset = spawn(unreal.TargetPoint, "C_ConeResetPoint", (6420, 1300, 120), R(yaw=0), FC)

def step(kind, instruction, lines=(), targets=(), duration=1.0, slot=0, **kw):
    s = unreal.NVSimStep()
    s.set_editor_property("type", kind)
    s.set_editor_property("instruction", T(instruction))
    s.set_editor_property("lines", list(lines))
    s.set_editor_property("targets", list(targets))
    s.set_editor_property("duration", duration)
    s.set_editor_property("weapon_slot", slot)
    for k, v in kw.items():
        s.set_editor_property(k, v)
    return s
K = unreal.NVSimStepType
sim = spawn(unreal.NVSimulationDirector, "C_SimulationDirector", (6800, 0, 150), None, FC)
sim.get_editor_property("start_volume").set_box_extent(V(250, 1000, 150))
sim.set_editor_property("objective_id", "M00-O02")
sim.set_editor_property("completion_tag", tag("NV.Event.M00.CalibrationComplete"))
sim.set_editor_property("steps", [
    step(K.CLEAR_TARGETS, "Neutralise the moving targets",
         [line("Simulation", "Calibration sequence initiated. Moving targets live."),
          line("AION", "Baseline reflexes nominal, Ghost-7. Proceed.")], t_moving),
    step(K.HOLD_AIM, "Aim down sights to stabilise the suite {Aim}",
         [line("Simulation", "Optics calibration. Hold your sight picture.")], duration=1.0),
    step(K.CLEAR_TARGETS, "Shielded targets: strike the weak point",
         [line("Simulation", "Hardened profiles. Shields absorb body hits; weak points do not.")], t_shield),
    step(K.EQUIP_WEAPON, "Switch to the Kestrel SMG {NextWeapon}",
         [line("Simulation", "Secondary weapon class. Confirm handling.")], slot=1),
    step(K.CLEAR_TARGETS, "Sentry drone: hit the glowing stabilizer core",
         [line("Simulation", "Aerial profile. Stabilizer core exposed on the underside.")], [t_drone]),
    step(K.VOLLEY, "Incoming fire: get behind the barrier and crouch {Crouch}",
         [line("Simulation", "Cover discipline. Live training rounds inbound.")], duration=2.5,
         emitter=emitter, area=a_cover, warmup_seconds=1.5, warning_text=T("Incoming volley"),
         fail_lines=[line("Simulation", "You were exposed. Resetting.", 2.5)]),
    step(K.VOLLEY, "Stand on the marker and survive the volley: Kinetic Shield {Ability2}",
         [line("Simulation", "No cover this time. Trust the shield, Ghost-7.")], duration=2.0,
         emitter=emitter, area=a_shield, warmup_seconds=1.2, warning_text=T("Incoming volley - shield now"),
         fail_lines=[line("Simulation", "Shield timing off. Resetting.", 2.5)]),
    step(K.CLEAR_TARGETS, "Shock baton {Melee}: strike, then strike again while it staggers",
         [line("Simulation", "Close-quarters profile. Staggered targets are open to a takedown.")], [t_dummy]),
    step(K.MARK_TARGETS, "Drone uplink {Ability3}: locate 3 concealed profiles in the south enclosure",
         [line("Simulation", "Profiles concealed behind hard cover. Use the uplink.")], t_hidden, min_marks=3),
    step(K.WAIT_FOR_EVENT, "Optical disruption {Ability1}: reach the catwalk relay unseen",
         [line("Simulation", "Surveillance cone active. Stay out of it, or stay invisible."),
          line("AION", "The cameras up here answer to the Directorate. Remember that.")],
         event_tag=tag("NV.Event.M00.SurveillanceBypassed"), cameras=[cam], reset_point=reset,
         fail_lines=[line("Simulation", "Detected. Return to the ramp.", 2.5)]),
    step(K.WAIT, "Calibration finalising", duration=2.0),
])
sim.set_editor_property("lines_on_complete", [
    line("AION", "Combat suite calibrated. The Director's office has your assignment queued in the operations gallery."),
])

# ---------------- D. Operations gallery (45 m)
FD = "D_Gallery"
room("D", 10300, 14800, -400, 400, 500, folder=FD)
wall_y("D_Wall_South", -400, 10300, 14800, 0, 500, M_DARK, 40, FD)
wall_y("D_Wall_North", 400, 10300, 14800, 0, 500, M_WHITE, 40, FD)
wall_x("D_Wall_East", 14800, -400, 400, 0, 500, M_WHITE, 40, [(0, 400, DOOR_H)], FD)
box("D_DataWall", (12550, -375, 250), (3800, 8, 350), M_DATA, FD)
box("D_HoloTable_Base", (12550, 0, 45), (300, 160, 90), M_DARK, FD)
for i in range(6):
    light(f"D_Light{i}", (10700 + i * 760, 150, 460), 3500, 1100)
holo = spawn(unreal.NVInteractableActor, "D_HoloTable", (12550, 0, 100), None, FD)
hm = holo.get_editor_property("mesh")
hm.set_static_mesh(CUBE)
hm.set_editor_property("relative_scale3d", V(2.6, 1.4, 0.08))
hm.set_material(0, M_CYAN)
holo.set_editor_property("prompt", T("Review assignment"))
holo.set_editor_property("hold_duration", 0.8)
holo.set_editor_property("required_active_objective", "M00-O03")
holo.set_editor_property("completion_event_tag", tag("NV.Event.M00.HoloTableReviewed"))
holo.set_editor_property("lines_on_use", [
    line("AION", "Assignment: personal briefing with the Director. Your clearance is elevated for the duration."),
    line("AION", "Proceed to the antechamber. Biometric authorization will be required at the door.", 4.2),
])

# ---------------- E. Director antechamber (16 x 14 m)
FE = "E_Antechamber"
room("E", 14800, 16400, -700, 700, 600, folder=FE)
wall_x("E_Wall_West_L", 14800, -700, -400, 0, 600, M_WHITE, 40, (), FE)
wall_x("E_Wall_West_R", 14800, 400, 700, 0, 600, M_WHITE, 40, (), FE)
wall_y("E_Wall_South", -700, 14800, 16400, 0, 600, M_WHITE, 40, FE)
wall_y("E_Wall_North", 700, 14800, 16400, 0, 600, M_WHITE, 40, FE)
box("E_DarkGlass", (16400, 0, 300), (40, 1400, 600), M_DARKGLASS, FE)
for i, (x, y) in enumerate(((15200, -450), (15200, 450), (15900, -450), (15900, 450))):
    box(f"E_Pillar{i}", (x, y, 300), (80, 80, 600), M_DARK, FE)
box("E_Panel_Plinth", (16250, 0, 60), (60, 120, 120), M_DARK, FE)
panel = spawn(unreal.NVInteractableActor, "E_BiometricPanel", (16250, 0, 145), None, FE)
pm = panel.get_editor_property("mesh")
pm.set_static_mesh(CUBE)
pm.set_editor_property("relative_scale3d", V(0.1, 0.5, 0.6))
pm.set_material(0, M_CYAN)
panel.set_editor_property("prompt", T("Initiate biometric scan"))
panel.set_editor_property("hold_duration", 1.5)
panel.set_editor_property("required_active_objective", "M00-O04")
panel.set_editor_property("completion_event_tag", tag("NV.Event.M00.BiometricScanStarted"))
light("E_Light_L", (15600, -500, 560), 2500, 900)
light("E_Light_R", (15600, 500, 560), 2500, 900)

# ---------------- Doors (gated by objectives)
def door(label, x, width, open_when_complete, folder):
    d = spawn(unreal.NVObjectiveDoor, label, (x, 0, 0), None, folder)
    half = width / 2
    for comp_name, y in (("panel_left", -half / 2), ("panel_right", half / 2)):
        c = d.get_editor_property(comp_name)
        c.set_static_mesh(CUBE)
        c.set_editor_property("relative_location", V(0, y, DOOR_H / 2))
        c.set_editor_property("relative_scale3d", V(0.12, half / 100.0, DOOR_H / 100.0))
        c.set_material(0, M_DARK)
    d.set_editor_property("open_when_complete", open_when_complete)
    d.set_editor_property("slide_distance", half + 10)
    return d
door("Door_B_to_C", 6300, 420, "M00-O01", FB)
door("Door_C_to_D", 10300, 420, "M00-O02", FC)
door("Door_D_to_E", 14800, 400, "M00-O03", FD)

# ---------------- Checkpoints (Bible: atrium, sim-suite exit, gallery)
def checkpoint(label, cid, oid, loc, folder):
    c = spawn(unreal.NVCheckpoint, label, loc, R(yaw=0), folder)
    c.set_editor_property("checkpoint_id", cid)
    c.set_editor_property("objective_id", oid)
    return c
checkpoint("CP_M00_Atrium", "CP_M00_Atrium", "M00-O01", (6600, 0, 100), FC)
checkpoint("CP_M00_SimExit", "CP_M00_SimExit", "M00-O02", (10550, 0, 100), FD)
checkpoint("CP_M00_Gallery", "CP_M00_Gallery", "M00-O03", (15050, 0, 100), FE)

# ---------------- Contextual VO + optional world-building interactions
arrival = spawn(unreal.NVObjectiveTrigger, "A_ArrivalVO", (900, 0, 120), None, FA)
arrival.get_editor_property("volume").set_box_extent(V(80, 300, 150))
arrival.set_editor_property("lines_on_complete", [
    line("AION", "Welcome back, Ghost-7. Crown Sector is secure. The Directorate is expecting you."),
    line("AION", "Report to security for access confirmation.", 3.0),
])

def optional(label, loc, rot_yaw, prompt, lines, scale=(0.15, 1.6, 0.9), folder=FB):
    a = spawn(unreal.NVInteractableActor, label, loc, R(yaw=rot_yaw), folder)
    m = a.get_editor_property("mesh")
    m.set_static_mesh(CUBE)
    m.set_editor_property("relative_scale3d", V(*scale))
    m.set_material(0, M_TERMINAL)
    a.set_editor_property("prompt", T(prompt))
    a.set_editor_property("lines_on_use", lines)
    return a
optional("B_Opt_NewsFeed", (4000, -1070, 220), 0, "Read news feed", [
    line("Crown News", "Directorate approval holds at 91 percent. Lower-district curfew extended indefinitely."),
    line("Crown News", "AION oversight credited with a fourteenth consecutive quarter without a Crown Sector incident.", 4.5),
])
optional("B_Opt_ProtestClip", (5400, -1070, 220), 0, "Watch muted public feed", [
    line("Public Feed", "[Muted footage: a crowd beneath the elevated rail. Captions withheld by Directorate order.]", 4.5),
])
optional("B_Opt_TrophyCase", (3800, 700, 100), 90, "Inspect commendation case", [
    line("Plaque", "Directorate Commendation, Asset Ghost-7. For service beyond the public record.", 4.0),
], scale=(1.2, 0.6, 1.4))
optional("D_Opt_TerminalLog", (11200, 370, 130), 180, "Read operations log", [
    line("Ops Log", "02:14 Crown perimeter nominal. 02:15 Director's calendar cleared by request of AION.", 4.5),
], folder=FD)

# ---------------- Sky, atmosphere, skyline (TEMP)
FS = "Sky"
# 02:17 local: the atmosphere's sun sits below the horizon (night sky); a separate dim,
# cool moon key light provides shape. Final night lighting is the M6 lighting pass.
sun = spawn(unreal.DirectionalLight, "SunBelowHorizon", (0, 0, 2000), R(pitch=12, yaw=60), FS)
sun.light_component.set_intensity(2.0)
sun.light_component.set_editor_property("atmosphere_sun_light", True)
sun.light_component.set_editor_property("cast_shadows", False)
moon = spawn(unreal.DirectionalLight, "MoonKey", (0, 0, 2100), R(pitch=-35, yaw=40), FS)
moon.light_component.set_intensity(0.25)
moon.light_component.set_light_color(unreal.LinearColor(0.6, 0.72, 1.0, 1))
moon.light_component.set_editor_property("forward_shading_priority", 1)
sky = spawn(unreal.SkyLight, "SkyLight", (0, 0, 2500), None, FS)
sky.light_component.set_editor_property("real_time_capture", True)
sky.light_component.set_intensity(0.6)
spawn(unreal.SkyAtmosphere, "SkyAtmosphere", (0, 0, 0), None, FS)
fog = spawn(unreal.ExponentialHeightFog, "HeightFog", (0, 0, -3000), None, FS)
fog.component.set_editor_property("enable_volumetric_fog", True)
ppv = spawn(unreal.PostProcessVolume, "GlobalPostProcess", (0, 0, 0), None, FS)
ppv.set_editor_property("unbound", True)
import random
random.seed(17)
for i in range(70):
    side = 1 if i % 2 == 0 else -1
    x = random.uniform(-15000, 35000)
    y = side * random.uniform(5000, 26000)
    w = random.uniform(1500, 4500)
    h = random.uniform(4000, 22000)
    top = random.uniform(-3000, 9000)
    box(f"City{i}", (x, y, top - h / 2), (w, w * random.uniform(0.6, 1.4), h), M_CITY, "Skyline")
    if i % 3 == 0:
        box(f"CityLit{i}", (x, y - side * (w * 0.35), top - h * 0.3), (w * 0.8, 30, h * 0.4), M_CITYLIT, "Skyline")

world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
world.get_world_settings().set_editor_property("default_game_mode", gcls)
LES.save_current_level()
log("saved", MAP, "actors:", len(EAS.get_all_level_actors()))

with open(unreal.Paths.project_saved_dir() + "NV_setup_m00.txt", "w", encoding="utf-8") as fh:
    fh.write("\n".join(REPORT))
log("done")
