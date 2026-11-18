"""NEON VEIL - M01 'Black Protocol' graybox (Act I bible §05), built into L_M00_GlassCrown so the betrayal at the
Director's door carries straight on with no load (M00's mission data ContinuesInto M01).

  A  Antechamber lockdown     the M00 antechamber (x 14800..16400, y +-700); emergency door cut in the north wall
  B  Server artery (55 m)     x 15300..15900, y 720..5600; sentry turret at the far end; maintenance terminal in an
                              east alcove; service crawlway (140 cm) behind the west wall; lift lobby y 5600..6600
  C  Transit shaft (45 m)     x 15200..16400, y 6600..7400, z 600 .. -4500; service lift fails, jams at -2800;
                              ledges at -2800 / -3300 / -3800 with assisted grabs over the gaps
  D  Medical reclamation      x 16400..18800, y 6100..7900, floor -4500 (24 x 18 m)
  E  Waste transfer conduit   x 18800..27800, y 6500..7500 (90 m), hostile troopers, pipe banks for cover
  F  Drainage spillway        x 27800..31800, open to the sky, ramp down into the rain; mission end trigger

Everything it adds is in folders M01_* and tagged NVM01; a re-run deletes and rebuilds them. One-time edits to M00
(north wall cut for the emergency door) are logged. Saves the level. Run in the full-uproject session only
(Scripts/BUILD_NOTES.md). Report: Saved/NV_setup_m01.txt
"""
import json
import math
import os
import unreal

REPORT = []
def log(*a):
    msg = " ".join(str(x) for x in a)
    REPORT.append(msg)
    unreal.log("[NV M01] " + msg)

AT = unreal.AssetToolsHelpers.get_asset_tools()
EAL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary
LES = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
UES = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
PROJ = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
MAP = "/Game/NeonVeil/Maps/M00/L_M00_GlassCrown"
TAG = "NVM01"

if not UES.get_editor_world().get_path_name().startswith(MAP):
    LES.load_level(MAP)

def V(x, y, z): return unreal.Vector(x, y, z)
def R(pitch=0.0, yaw=0.0, roll=0.0): return unreal.Rotator(roll=roll, pitch=pitch, yaw=yaw)
def T(s): return unreal.Text(s)
def gtag(n):
    t = unreal.GameplayTag()
    t.import_text(f'(TagName="{n}")')
    return t

# ------------------------------------------------------------------ lines (shared with the VO pipeline)
LINES = {l["id"]: l for l in json.load(open(os.path.join(PROJ, "Scripts", "VO", "M01_lines.json"), encoding="utf-8"))}
def lines(*ids):
    out = []
    for i in ids:
        d = LINES[i]
        s = unreal.NVSubtitleLine()
        s.set_editor_property("speaker", T(d["speaker"]))
        s.set_editor_property("text", T(d["text"]))
        s.set_editor_property("duration", float(d.get("dur", 3.5)))
        if d["speaker"] == "Ops":
            s.set_editor_property("as_comms", True)
            s.set_editor_property("channel", T("DIRECTORATE OPS"))
        out.append(s)
    return out

# ------------------------------------------------------------------ materials (graybox)
MAT = "/Game/NeonVeil/Tests/Materials"
def make_material(name, base, emissive=None, rough=0.5, metal=0.0):
    path = f"{MAT}/{name}"
    if EAL.does_asset_exist(path):
        return unreal.load_asset(path)
    m = AT.create_asset(name, MAT, unreal.Material, unreal.MaterialFactoryNew())
    def c3(rgb, y, prop):
        e = MEL.create_material_expression(m, unreal.MaterialExpressionConstant3Vector, -400, y)
        e.set_editor_property("constant", unreal.LinearColor(rgb[0], rgb[1], rgb[2], 1))
        MEL.connect_material_property(e, "", prop)
    def c1(v, y, prop):
        e = MEL.create_material_expression(m, unreal.MaterialExpressionConstant, -400, y)
        e.set_editor_property("r", v)
        MEL.connect_material_property(e, "", prop)
    c3(base, 0, unreal.MaterialProperty.MP_BASE_COLOR)
    if emissive:
        c3(emissive, 150, unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    c1(rough, 300, unreal.MaterialProperty.MP_ROUGHNESS)
    c1(metal, 400, unreal.MaterialProperty.MP_METALLIC)
    MEL.recompile_material(m)
    EAL.save_loaded_asset(m)
    log("material", name)
    return m

M_WHITE = make_material("TEMP_M_CrownCeramic", (0.72, 0.74, 0.76), None, 0.35)
M_FLOOR = make_material("TEMP_M_CrownFloor_v2", (0.30, 0.31, 0.33), None, 0.5)
M_DARK = make_material("TEMP_M_Titanium", (0.06, 0.065, 0.07), None, 0.3, 1.0)
M_SERVICE = make_material("TEMP_M_ServiceConcrete", (0.16, 0.165, 0.17), None, 0.8)
M_GRIME = make_material("TEMP_M_ConduitGrime", (0.07, 0.075, 0.07), None, 0.9)
M_WET = make_material("TEMP_M_WetConcrete", (0.04, 0.045, 0.05), None, 0.12)
M_RACK = make_material("TEMP_M_ServerRack", (0.02, 0.022, 0.025), (0.0, 0.15, 0.25), 0.4, 0.6)
M_HAZARD = make_material("TEMP_M_HazardYellow", (0.6, 0.45, 0.02), None, 0.6)
M_CYAN = make_material("TEMP_M_CyanEmissive", (0.0, 0.0, 0.0), (0.2, 1.6, 2.4), 0.5)
M_REDGLOW = make_material("TEMP_M_RedLaser", (0.0, 0.0, 0.0), (12.0, 0.2, 0.1), 0.5)
M_GREENGLOW = make_material("TEMP_M_GreenLaser", (0.0, 0.0, 0.0), (0.2, 10.0, 1.0), 0.5)
M_DRONE = make_material("TEMP_M_DroneShell", (0.12, 0.125, 0.13), None, 0.25, 1.0)
M_TRACER_RED = make_material("TEMP_M_TracerRedHot", (0.0, 0.0, 0.0), (18.0, 3.0, 0.8), 0.5)
M_TERMINAL = unreal.load_asset(f"{MAT}/TEMP_M_Terminal")

CUBE = unreal.load_asset("/Engine/BasicShapes/Cube")
CYL = unreal.load_asset("/Engine/BasicShapes/Cylinder")

# ------------------------------------------------------------------ mission data
def mission_asset(name):
    path = f"/Game/NeonVeil/Data/Missions/{name}"
    if EAL.does_asset_exist(path):
        return unreal.load_asset(path)
    f = unreal.DataAssetFactory()
    f.set_editor_property("data_asset_class", unreal.NVMissionData)
    return AT.create_asset(name, "/Game/NeonVeil/Data/Missions", unreal.NVMissionData, f)

def obj(oid, text, event, prereq=None):
    o = unreal.NVObjectiveDef()
    o.set_editor_property("objective_id", oid)
    o.set_editor_property("display_text", T(text))
    o.set_editor_property("completion_event_tag", gtag(event))
    o.set_editor_property("prerequisites", [prereq] if prereq else [])
    # every M01 objective saves when it becomes active, at the checkpoint tagged with its ID (start of that beat)
    o.set_editor_property("checkpoint_policy", unreal.NVCheckpointPolicy.ON_ACTIVATE)
    return o

m01 = mission_asset("DA_Mission_M01")
m01.set_editor_property("mission_id", "M01")
m01.set_editor_property("mission_title", T("Black Protocol"))
m01.set_editor_property("objectives", [
    obj("M01-O01", "Survive the lockdown", "NV.Event.M01.EmergencyDoorReached"),
    obj("M01-O02", "Find an alternate exit", "NV.Event.M01.AlternateExit", "M01-O01"),
    obj("M01-O03", "Escape the transit shaft", "NV.Event.M01.ShaftEscaped", "M01-O02"),
    obj("M01-O04", "Recover your identity", "NV.Event.M01.IdentityRecovered", "M01-O03"),
    obj("M01-O05", "Reach the lower city", "NV.Event.M01.SpillwayReached", "M01-O04"),
])
EAL.save_loaded_asset(m01)
m00 = unreal.load_asset("/Game/NeonVeil/Data/Missions/DA_Mission_M00")
m00.set_editor_property("continues_into", m01)
EAL.save_loaded_asset(m00)
gbp = unreal.load_asset("/Game/NeonVeil/Core/BP_NVGameMode_M00")
gcdo = unreal.get_default_object(EAL.load_blueprint_class("/Game/NeonVeil/Core/BP_NVGameMode_M00"))
gcdo.set_editor_property("end_card_title", T("Below the Veil"))
gcdo.set_editor_property("end_card_subtitle", T("Mission M02 is not built yet. End of the current build."))
gcdo.set_editor_property("show_end_card", True)
EAL.save_loaded_asset(gbp)
log("mission data: M00 continues into M01; end card now M02")

# ------------------------------------------------------------------ clean previous run
for a in list(EAS.get_all_level_actors()):
    if TAG in [str(t) for t in a.tags]:
        EAS.destroy_actor(a)
ACT = {a.get_actor_label(): a for a in EAS.get_all_level_actors()}

def tagit(a, label, folder):
    a.set_actor_label(label)
    a.set_folder_path(folder)
    a.tags = [unreal.Name(TAG)]
    return a

def spawn(cls, label, loc, rot=None, folder="M01"):
    a = EAS.spawn_actor_from_class(cls, V(*loc), rot or R())
    return tagit(a, label, folder)

def box(label, center, size, mat, folder, rot=None, mesh=CUBE, movable=False, collide=True):
    a = spawn(unreal.StaticMeshActor, label, center, rot, folder)
    c = a.static_mesh_component
    if movable:
        c.set_mobility(unreal.ComponentMobility.MOVABLE)
    c.set_static_mesh(mesh)
    a.set_actor_scale3d(V(size[0] / 100.0, size[1] / 100.0, size[2] / 100.0))
    c.set_material(0, mat)
    if not collide:
        c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    # enclosed graybox: no shadow casting (the city key light otherwise renders virtual shadow pages for 45 m of
    # shaft and 90 m of tunnel that nobody sees; that pushed the 8 GB GPU over budget)
    c.set_cast_shadow(False)
    return a

def span(label, a0, a1, axis, fixed, z0, z1, mat, folder, thick=40, cuts=()):
    """Wall from a0 to a1 along `axis` ('x' or 'y') at the other coordinate `fixed`, floor z0 to top z1,
    with openings [(centre, width, height)] measured from z0."""
    pieces = []
    pos = a0
    i = 0
    def seg(p0, p1, zb, zt, tag_):
        nonlocal i
        if p1 - p0 < 1 or zt - zb < 1:
            return
        c = (p0 + p1) / 2
        if axis == "x":
            pieces.append(box(f"{label}_{tag_}{i}", (c, fixed, (zb + zt) / 2), (p1 - p0, thick, zt - zb), mat, folder))
        else:
            pieces.append(box(f"{label}_{tag_}{i}", (fixed, c, (zb + zt) / 2), (thick, p1 - p0, zt - zb), mat, folder))
        i += 1
    for (c, w, h) in sorted(cuts):
        seg(pos, c - w / 2, z0, z1, "w")
        seg(c - w / 2, c + w / 2, z0 + h, z1, "l")
        pos = c + w / 2
    seg(pos, a1, z0, z1, "w")
    return pieces

def slab(label, x0, x1, y0, y1, z, mat, folder, thick=40):
    return box(label, ((x0 + x1) / 2, (y0 + y1) / 2, z - thick / 2), (x1 - x0, y1 - y0, thick), mat, folder)

def light(label, loc, lumens, radius, color, folder, visible=True):
    a = spawn(unreal.PointLight, label, loc, None, folder)
    lc = a.point_light_component
    lc.set_mobility(unreal.ComponentMobility.MOVABLE)
    lc.set_editor_property("intensity_units", unreal.LightUnits.LUMENS)
    lc.set_intensity(lumens)
    lc.set_attenuation_radius(radius)
    lc.set_light_color(unreal.LinearColor(color[0], color[1], color[2], 1.0))
    lc.set_editor_property("cast_shadows", False)
    return a

def nav(label, center, size, folder):
    a = spawn(unreal.NavMeshBoundsVolume, label, center, None, folder)
    a.set_actor_scale3d(V(size[0] / 200.0, size[1] / 200.0, size[2] / 200.0))
    return a

def trigger(label, center, extent, event, required, folder, line_ids=(), delay=0.0):
    t = spawn(unreal.NVObjectiveTrigger, label, center, None, folder)
    t.get_editor_property("volume").set_box_extent(V(*extent))
    if event:
        t.set_editor_property("event_tag", gtag(event))
    if required:
        t.set_editor_property("required_active_objective", required)
    t.set_editor_property("delay", delay)
    if line_ids:
        t.set_editor_property("lines_on_complete", lines(*line_ids))
    return t

def checkpoint(label, oid, loc, yaw, folder):
    c = spawn(unreal.NVCheckpoint, label, loc, R(yaw=yaw), folder)
    c.set_editor_property("checkpoint_id", label)
    c.set_editor_property("objective_id", oid)
    return c

DOOR_H = 300
def door(label, loc, yaw, width, folder, open_when_active=None, height=DOOR_H):
    d = spawn(unreal.NVObjectiveDoor, label, loc, R(yaw=yaw), folder)
    half = width / 2
    for comp_name, y in (("panel_left", -half / 2), ("panel_right", half / 2)):
        c = d.get_editor_property(comp_name)
        c.set_static_mesh(CUBE)
        c.set_editor_property("relative_location", V(0, y, height / 2))
        c.set_editor_property("relative_scale3d", V(0.14, half / 100.0, height / 100.0))
        c.set_material(0, M_DARK)
    d.set_editor_property("slide_distance", half + 10)
    if open_when_active:
        d.set_editor_property("open_when_active", open_when_active)
    return d

def clone_guard(src_label, label, loc, yaw, route, folder, waits=(2.0, 4.0), speed=140.0, hostile=True):
    src = ACT.get(src_label)
    if not src:
        log("no source guard", src_label)
        return None
    g = EAS.duplicate_actor(src)
    g.set_actor_location_and_rotation(V(*loc), R(yaw=yaw), False, False)
    tagit(g, label, folder)
    c, s_ = math.cos(math.radians(-yaw)), math.sin(math.radians(-yaw))
    rel = [V((wx - loc[0]) * c - (wy - loc[1]) * s_, (wx - loc[0]) * s_ + (wy - loc[1]) * c, 0) for (wx, wy) in route]
    g.set_editor_property("patrol_points", rel)
    g.set_editor_property("wait_time_range", unreal.Vector2D(*waits))
    g.set_editor_property("walk_speed", speed)
    g.set_editor_property("glance_radius", 0.0)
    g.set_editor_property("start_hostile", hostile)
    g.set_editor_property("non_hostile", not hostile)
    make_damageable(g)
    return g

def make_damageable(g):
    """Directorate trooper tuning: hurtable, readable bursts, survivable for a few seconds in the open."""
    g.get_editor_property("health").set_editor_property("immune_damage_types", unreal.GameplayTagContainer())
    gun = arm_gun(g)
    gun.set_editor_property("damage", 4.0)
    gun.set_editor_property("spread_deg", 4.5)
    g.set_editor_property("burst_pause", unreal.Vector2D(1.3, 2.4))

NS = "/Game/NiagaraExamples"
def try_load(p):
    return unreal.load_asset(p) if EAL.does_asset_exist(p) else None
SPARKS = try_load(f"{NS}/FX_Sparks/NS_Spark_Burst")
EXPLOSION = try_load(f"{NS}/FX_Explosions/NS_Explosion")
SMOKE = try_load(f"{NS}/FX_Smoke/NS_Smoke_Plume")
SHOT = try_load("/Game/Sci-Fi_Shots_Pack2_Game_Of_Weapons/Wave/SciFi_Shot_P2__88_")
BOOM = try_load("/Game/FreeWeaponSFX/Cue/GrenadeLauncher/sfx_wpn_gl_explosion_Cue")
log("fx", bool(SPARKS), bool(EXPLOSION), bool(SMOKE), "shot sound", bool(SHOT), "boom", bool(BOOM))

def arm_gun(actor_or_comp_owner):
    g = actor_or_comp_owner.get_editor_property("gun")
    g.set_editor_property("tracer_material", M_TRACER_RED)
    if SHOT:
        g.set_editor_property("shot_sound", SHOT)
    # no Niagara on every shot: GPU particle spawns tipped this 8 GB laptop GPU over its video-memory budget
    # (D3D device removed) during the lockdown fight
    return g

# ================================================================== A. antechamber lockdown
FA = "M01_A_Lockdown"
# one-time cut of the north wall for the emergency door (x 15480..15720)
for name in ("E_Wall_North", "E_Wall_North_EtherN2", "E_WallLight_N", "E_WallLight_N_EtherN0", "E_WallLight_N_EtherP0"):
    if name in ACT:
        EAS.destroy_actor(ACT.pop(name))
        log("removed for the emergency door:", name)
span("A_NorthWall", 14800, 16400, "x", 700, 0, 600, M_WHITE, FA, cuts=[(15600, 240, DOOR_H)])
em_door = door("A_EmergencyDoor", (15600, 700, 0), 90, 240, FA)
box("A_EmergencyDoor_Sign", (15600, 676, 340), (200, 4, 40), M_REDGLOW, FA, collide=False)
shutter = box("A_Shutter_DirectorGlass", (16370, 0, 940), (24, 1400, 620), M_DARK, FA, movable=True)
alarm_lights = [light(f"A_Emergency_{i}", p, 9000, 1400, (1.0, 0.05, 0.03), FA) for i, p in
                enumerate([(15600, 640, 540), (15000, 0, 560), (16200, 0, 560), (15600, -640, 540)])]
drones = []
for i, (dock, yaw) in enumerate((((15300, 350, 575), -45), ((15900, -300, 575), 135))):
    d = spawn(unreal.NVSecurityDrone, f"A_Drone_{i}", dock, R(yaw=yaw), FA)
    d.set_editor_property("bounds_min", V(14900, -620, 170))
    d.set_editor_property("bounds_max", V(16300, 620, 520))
    for comp in ("body", "ring"):
        d.get_editor_property(comp).set_material(0, M_DRONE)
    d.get_editor_property("eye").set_material(0, M_REDGLOW)
    arm_gun(d)
    if SPARKS:
        d.set_editor_property("destroyed_fx", SPARKS)
    if BOOM:
        d.set_editor_property("destroyed_sound", BOOM)
    drones.append(d)
# troopers arrive through the gallery door after AION re-designates him
troopers_a = [clone_guard("G2_E_Guard_Sentry", f"A_Trooper_{i}", p, 0.0, [], FA, hostile=False)
              for i, p in enumerate([(14250, 180, 100), (14100, -160, 100)])]
for g in troopers_a:
    if g:
        g.set_editor_property("non_hostile", True)
checkpoint("CP_M01_Lockdown", "M01-O01", (15250, 0, 100), 0, FA)
trigger("A_EmergencyExitReached", (15600, 900, 120), (200, 120, 150), "NV.Event.M01.EmergencyDoorReached", "M01-O01", FA)

# ================================================================== B. server artery
FB = "M01_B_Artery"
slab("B_Floor", 15060, 15900, 720, 5600, 0, M_SERVICE, FB)
slab("B_Ceiling", 15300, 15900, 720, 5600, 470, M_SERVICE, FB)
span("B_WestWall", 720, 5600, "y", 15300, 0, 450, M_SERVICE, FB, cuts=[(1600, 160, 140)])
span("B_EastWall", 720, 5600, "y", 15900, 0, 450, M_SERVICE, FB, cuts=[(2600, 320, 300)])
# racks: mirrored spine, gaps at the crawlway and the alcove
for side, x in (("W", 15380), ("E", 15820)):
    for j, (y0, y1) in enumerate(((900, 1440), (1760, 2420), (2800, 3650), (3900, 4650), (4900, 5250))):
        box(f"B_Rack_{side}{j}", (x, (y0 + y1) / 2, 120), (120, y1 - y0, 240), M_RACK, FB)
for j, (x, y) in enumerate(((15600, 1950), (15520, 3300), (15680, 4400))):
    box(f"B_Cover_{j}", (x, y, 55), (160, 90, 110), M_HAZARD, FB)
# east alcove with the maintenance terminal
slab("B_Alcove_Floor", 15900, 16220, 2440, 2760, 0, M_SERVICE, FB)
slab("B_Alcove_Ceil", 15900, 16220, 2440, 2760, 330, M_SERVICE, FB)
span("B_Alcove_N", 15900, 16240, "x", 2760, 0, 330, M_SERVICE, FB)
span("B_Alcove_S", 15900, 16240, "x", 2440, 0, 330, M_SERVICE, FB)
span("B_Alcove_E", 2440, 2760, "y", 16220, 0, 330, M_SERVICE, FB)
term = spawn(unreal.NVInteractableActor, "B_Terminal_Reroute", (16180, 2600, 120), R(yaw=180), FB)
tm = term.get_editor_property("mesh")
tm.set_static_mesh(CUBE)
tm.set_editor_property("relative_scale3d", V(0.15, 0.9, 0.7))
tm.set_material(0, M_TERMINAL)
term.set_editor_property("prompt", T("Reroute sentry targeting"))
term.set_editor_property("hold_duration", 2.5)
term.set_editor_property("completion_event_tag", gtag("NV.Event.M01.TurretRerouted"))
term.set_editor_property("lines_on_use", lines("M01_Ghost_04"))
# service crawlway behind the west wall (crouch: 140 cm), exits into the lift lobby behind the turret
slab("B_Crawl_Ceil", 15060, 15300, 1520, 5600, 160, M_SERVICE, FB, thick=20)
span("B_Crawl_W", 1520, 5600, "y", 15080, 0, 150, M_SERVICE, FB)
span("B_Crawl_S", 15060, 15300, "x", 1520, 0, 150, M_SERVICE, FB)
light("B_Crawl_Light0", (15180, 2600, 120), 300, 500, (1.0, 0.6, 0.2), FB)
light("B_Crawl_Light1", (15180, 4400, 120), 300, 500, (1.0, 0.6, 0.2), FB)
trigger("B_BypassExit", (15180, 5650, 80), (90, 60, 80), "NV.Event.M01.AlternateExit", "M01-O02", FB, ("M01_Ghost_05",))
trigger("B_ArteryEntryVO", (15600, 1000, 120), (300, 120, 150), None, "M01-O02", FB, ("M01_Ghost_03",))
flicker = [light(f"B_Light_{i}", (15600, y, 405), 2600, 1300, (0.75, 0.9, 1.0), FB) for i, y in enumerate(range(1100, 5600, 1100))]
turret = spawn(unreal.NVSentryTurret, "B_SentryTurret", (15600, 5450, 0), R(yaw=-90), FB)
for comp in ("base", "head_mesh", "barrel"):
    turret.get_editor_property(comp).set_material(0, M_DARK)
turret.set_editor_property("laser_hostile", M_REDGLOW)
turret.set_editor_property("laser_friendly", M_GREENGLOW)
turret.set_editor_property("reroute_event_tag", gtag("NV.Event.M01.TurretRerouted"))
turret.set_editor_property("objective_event_on_reroute", gtag("NV.Event.M01.AlternateExit"))
turret.set_editor_property("start_mode", unreal.NVTurretMode.OFF)
tg = arm_gun(turret)
tg.set_editor_property("damage", 6.0)
turret.set_editor_property("burst_shots", 5)
checkpoint("CP_M01_Artery", "M01-O02", (15600, 820, 100), 90, FB)
# lift lobby
slab("B_Lobby_Floor", 15000, 16200, 5600, 6600, 0, M_SERVICE, FB)
slab("B_Lobby_Ceil", 15000, 16200, 5600, 6600, 470, M_SERVICE, FB)
span("B_Lobby_S", 15000, 16200, "x", 5600, 0, 450, M_SERVICE, FB, cuts=[(15180, 160, 140), (15600, 600, 450)])
span("B_Lobby_W", 5600, 6600, "y", 15000, 0, 450, M_SERVICE, FB)
span("B_Lobby_E", 5600, 6600, "y", 16200, 0, 450, M_SERVICE, FB)
span("B_Lobby_N_West", 15000, 15200, "x", 6600, 0, 450, M_SERVICE, FB)
# running the sentry's gauntlet into the lobby also counts (no soft-lock if he simply gets past it)
trigger("B_LobbyReached", (15800, 6150, 120), (380, 400, 150), "NV.Event.M01.AlternateExit", "M01-O02", FB)
light("B_Lobby_Light", (15600, 6100, 410), 3200, 1400, (1.0, 0.85, 0.7), FB)
troopers_b = [clone_guard("G2_E_Guard_Sentry", "B_Trooper_0", (15300, 6200, 100), 0.0, [(15300, 6200), (15900, 6200)], FB),
              clone_guard("G2_E_Guard_Sentry", "B_Trooper_1", (15900, 5900, 100), 180.0, [(15900, 5900), (15400, 5900), (15400, 6400)], FB)]
checkpoint("CP_M01_Lift", "M01-O03", (15600, 6000, 100), 90, FB)
nav("B_NavBounds", (15600, 3650, 220), (1400, 6200, 600), FB)

# ================================================================== C. transit shaft
FC = "M01_C_Shaft"
SX0, SX1, SY0, SY1, ZB, ZT = 15200, 16400, 6600, 7400, -4500, 600
span("C_South_Upper", SX0, SX1, "x", SY0, 0, ZT, M_SERVICE, FC, cuts=[(15500, 500, 450)])
span("C_South_Lower", SX0, SX1, "x", SY0, ZB, 0, M_SERVICE, FC)
span("C_North", SX0, SX1, "x", SY1, ZB, ZT, M_SERVICE, FC)
span("C_West", SY0, SY1, "y", SX0, ZB, ZT, M_SERVICE, FC)
span("C_East", SY0, SY1, "y", SX1, ZB, ZT, M_SERVICE, FC, cuts=[(7000, 400, 300)])
slab("C_Top", SX0, SX1, SY0, SY1, ZT + 40, M_SERVICE, FC)
slab("C_Bottom", SX0, SX1, SY0, SY1, ZB, M_GRIME, FC)
# cab: floor is the moving root, the rest is attached to it
CX0, CX1, CY0, CY1 = 15260, 15740, 6620, 7100
cab = box("C_Cab_Floor", ((CX0 + CX1) / 2, (CY0 + CY1) / 2, -10), (CX1 - CX0, CY1 - CY0, 20), M_DARK, FC, movable=True)
cab_parts = [
    box("C_Cab_Roof", ((CX0 + CX1) / 2, (CY0 + CY1) / 2, 310), (CX1 - CX0, CY1 - CY0, 20), M_DARK, FC, movable=True),
    box("C_Cab_West", (CX0 + 10, (CY0 + CY1) / 2, 150), (20, CY1 - CY0, 300), M_SERVICE, FC, movable=True),
    box("C_Cab_North", ((CX0 + CX1) / 2, CY1 - 10, 150), (CX1 - CX0, 20, 300), M_SERVICE, FC, movable=True),
]
hatch = box("C_Cab_EastHatch", (CX1 - 10, (CY0 + CY1) / 2, 150), (20, CY1 - CY0, 300), M_HAZARD, FC, movable=True)
gate = box("C_Cab_Gate", ((CX0 + CX1) / 2, CY0 + 10, 450), (CX1 - CX0, 16, 290), M_DARK, FC, movable=True)
cab_light = light("C_Cab_Light", ((CX0 + CX1) / 2, (CY0 + CY1) / 2, 280), 1800, 700, (1.0, 0.92, 0.8), FC)
for p in cab_parts + [hatch, gate]:
    p.attach_to_actor(cab, "", unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD, False)
cab_light.attach_to_actor(cab, "", unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD, False)
trigger("C_LiftCall", ((CX0 + CX1) / 2, (CY0 + CY1) / 2 + 60, 100), (180, 150, 90), "NV.Event.M01.LiftCalled", "M01-O03", FC, delay=1.0)
# ledges: P1 level with the jammed cab (gap 260), P2 drop, P3 across another gap, then the floor
P1 = box("C_Ledge_P1", (16200, 6830, -2820), (400, 420, 40), M_HAZARD, FC)
P2 = box("C_Ledge_P2", (16200, 7230, -3320), (400, 300, 40), M_HAZARD, FC)
P3 = box("C_Ledge_P3", (15475, 7245, -3820), (550, 270, 40), M_HAZARD, FC)
g1 = spawn(unreal.NVAssistGrab, "C_Grab_ToP1", (15870, 6860, -2760), None, FC)
g1.get_editor_property("volume").set_box_extent(V(130, 220, 200))
g1.get_editor_property("land_point").set_world_location(V(16150, 6860, -2700), False, False)
g2 = spawn(unreal.NVAssistGrab, "C_Grab_ToP3", (15880, 7245, -3760), None, FC)
g2.get_editor_property("volume").set_box_extent(V(130, 140, 200))
g2.get_editor_property("land_point").set_world_location(V(15600, 7245, -3700), False, False)
for i, z in enumerate((-600, -1700, -2600, -3500, -4300)):
    light(f"C_Shaft_Light{i}", (16330, 7330, z), 1600, 1500, (1.0, 0.3, 0.15), FC)
trigger("C_ShaftBottom", (16150, 7000, -4400), (230, 380, 120), "NV.Event.M01.ShaftEscaped", "M01-O03", FC, ("M01_Ghost_07",))
checkpoint("CP_M01_ShaftBottom", "M01-O04", (16100, 7000, -4400), 0, FC)

# ================================================================== D. medical reclamation
FD = "M01_D_Medical"
DX0, DX1, DY0, DY1, DZ, DH = 16400, 18800, 6100, 7900, -4500, 600
slab("D_Floor", DX0, DX1, DY0, DY1, DZ, M_WHITE, FD)
slab("D_Ceiling", DX0, DX1, DY0, DY1, DZ + DH + 40, M_WHITE, FD)
span("D_North", DX0, DX1, "x", DY1, DZ, DZ + DH, M_WHITE, FD)
span("D_South", DX0, DX1, "x", DY0, DZ, DZ + DH, M_WHITE, FD)
span("D_East", DY0, DY1, "y", DX1, DZ, DZ + DH, M_WHITE, FD, cuts=[(7000, 300, 300)])
span("D_West_S", DY0, SY0, "y", DX0, DZ, DZ + DH, M_WHITE, FD)
span("D_West_N", SY1, DY1, "y", DX0, DZ, DZ + DH, M_WHITE, FD)
suite_door = door("D_SuiteDoor", (DX0 + 20, 7000, DZ), 0, 400, FD, open_when_active="M01-O04")
# surgical bay just inside the door: partition walls make a 3 m vestibule he has to cross
span("D_Bay_N", DX0, 16900, "x", 7180, DZ, DZ + 320, M_WHITE, FD, thick=20)
span("D_Bay_S", DX0, 16900, "x", 6820, DZ, DZ + 320, M_WHITE, FD, thick=20)
arms = []
for i, (ax, ay, sx, sy) in enumerate(((16500, 6880, 1, 1), (16800, 6880, -1, 1), (16500, 7120, 1, -1), (16800, 7120, -1, -1))):
    arm = box(f"D_SurgicalArm_{i}", (ax, ay, DZ + 470), (30, 30, 220), M_DARK, FD, movable=True)
    tip = box(f"D_SurgicalArm_{i}_Tip", (ax, ay, DZ + 350), (16, 16, 30), M_CYAN, FD, movable=True, collide=False)
    tip.attach_to_actor(arm, "", unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD, False)
    arm.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    mv = unreal.NVMover()
    mv.set_editor_property("actor", arm)
    mv.set_editor_property("offset", V(sx * 60, sy * 50, -120))
    mv.set_editor_property("rotation", R(pitch=-28 * sx, roll=28 * sy))
    arms.append(mv)
trigger("D_ReclamationStart", (16650, 7000, DZ + 100), (130, 160, 100), "NV.Event.M01.ReclamationStart", "M01-O04", FD)
suite_lights = [light(f"D_Light_{i}", p, 5000, 1600, (0.9, 0.95, 1.0), FD) for i, p in
                enumerate([(16650, 7000, DZ + 560), (17600, 6600, DZ + 560), (17600, 7400, DZ + 560), (18400, 7000, DZ + 560)])]
for i, (x, y) in enumerate(((17400, 6450), (17400, 7550), (18200, 6450), (18200, 7550))):
    box(f"D_Gurney_{i}", (x, y, DZ + 45), (220, 90, 90), M_WHITE, FD)
tray = box("D_TagTray", (17300, 7000, DZ + 50), (120, 70, 100), M_DARK, FD)
# the interaction sweep must reach the tag, not clip the tray's edge
tray.static_mesh_component.set_collision_response_to_channel(unreal.CollisionChannel.ECC_VISIBILITY, unreal.CollisionResponseType.ECR_IGNORE)
tagi = spawn(unreal.NVInteractableActor, "D_AgencyTag", (17300, 7000, DZ + 104), R(yaw=0), FD)
tgm = tagi.get_editor_property("mesh")
tgm.set_static_mesh(CUBE)
tgm.set_editor_property("relative_scale3d", V(0.3, 0.2, 0.05))
tgm.set_material(0, M_CYAN)
tagi.set_editor_property("prompt", T("Take your agency tag"))
tagi.set_editor_property("completion_event_tag", gtag("NV.Event.M01.IdentityRecovered"))
tagi.set_editor_property("lines_on_use", lines("M01_Ghost_10"))
checkpoint("CP_M01_Suite", "M01-O05", (17550, 7000, DZ + 100), 0, FD)

# ================================================================== E. waste transfer conduit
FE = "M01_E_Conduit"
EX0, EX1, EY0, EY1, EZ, EH = 18800, 27800, 6500, 7500, -4500, 500
slab("E_Floor", EX0, EX1, EY0, EY1, EZ, M_GRIME, FE)
slab("E_Ceiling", EX0, EX1, EY0, EY1, EZ + EH + 40, M_GRIME, FE)
span("E_North", EX0, EX1, "x", EY1, EZ, EZ + EH, M_GRIME, FE)
span("E_South", EX0, EX1, "x", EY0, EZ, EZ + EH, M_GRIME, FE)
# central pipe bank with crossing gaps; crates and low ducts along both lanes
for j, (x0, x1) in enumerate(((19300, 20600), (21000, 22900), (23300, 24800), (25200, 26900))):
    box(f"E_PipeBank_{j}", ((x0 + x1) / 2, 7000, EZ + 90), (x1 - x0, 140, 180), M_DARK, FE)
for j, (x, y) in enumerate(((19800, 6700), (20900, 7320), (22200, 6680), (23700, 7330), (24900, 6700), (26200, 7300))):
    box(f"E_Crate_{j}", (x, y, EZ + 60), (150, 130, 120), M_HAZARD, FE)
# a low duct section to slip under on the south lane
box("E_LowDuct", (24000, 6680, EZ + 260), (1200, 360, 240), M_DARK, FE)
for i, x in enumerate(range(19400, 27800, 1600)):
    light(f"E_Light_{i}", (x, 7000 + (-300 if i % 2 else 300), EZ + 470), 1400, 1200, (1.0, 0.75, 0.45), FE)
troopers_e = [
    clone_guard("G2_E_Guard_Sentry", "E_Trooper_0", (19900, 7300, EZ + 100), 0.0, [(19900, 7300), (22800, 7300)], FE, (2.0, 4.0), 120.0),
    clone_guard("G2_E_Guard_Sentry", "E_Trooper_1", (25800, 6720, EZ + 100), 180.0, [(25800, 6720), (22700, 6720)], FE, (2.5, 4.5), 115.0),
    clone_guard("G2_E_Guard_Sentry", "E_Trooper_2", (27200, 7000, EZ + 100), 180.0, [(27200, 7000), (27200, 7300), (27200, 6700)], FE, (3.0, 6.0), 90.0),
]
trigger("E_ConduitEntryVO", (19000, 7000, EZ + 120), (150, 300, 150), None, "M01-O05", FE, ("M01_Ghost_11",))
nav("E_NavBounds", (23300, 7000, EZ + 250), (9200, 1100, 700), FE)

# ================================================================== F. drainage spillway
FF = "M01_F_Spillway"
ramp_len, drop = 1200.0, 500.0
pitch = math.degrees(math.atan2(drop, ramp_len))
box("F_Ramp", (27800 + ramp_len / 2, 7000, EZ - drop / 2 - 20), (math.hypot(ramp_len, drop), 1000, 40), M_WET, FF, rot=R(pitch=-pitch))
slab("F_Channel", 29000, 31800, 6500, 7500, EZ - drop, M_WET, FF)
span("F_North", 27800, 31800, "x", 7500, EZ - drop, EZ + 1500, M_WET, FF)
span("F_South", 27800, 31800, "x", 6500, EZ - drop, EZ + 1500, M_WET, FF)
span("F_Grate", 6500, 7500, "y", 31800, EZ - drop, EZ + 300, M_DARK, FF)
light("F_Spill_Light", (30500, 7000, EZ + 200), 2500, 3000, (0.4, 0.55, 0.9), FF)
trigger("F_ReachLowerCity", (30900, 7000, EZ - drop + 120), (300, 480, 150), "NV.Event.M01.SpillwayReached", "M01-O05", FF, ("M01_Ghost_12", "M01_AION_11"))

# ================================================================== director
FX = "M01_Director"
dr = spawn(unreal.NVBlackProtocolDirector, "M01_BlackProtocolDirector", (15600, 0, 300), None, FX)
def P(name, value):
    dr.set_editor_property(name, value)
P("revocation_lines", lines("M01_AION_01", "M01_Ghost_01", "M01_AION_02"))
P("designation_lines", lines("M01_AION_03", "M01_Ops_01"))
P("door_open_lines", lines("M01_Ghost_02"))
P("lights_to_alarm", [ACT[n] for n in ("E_Light_L", "E_Light_R", "E_DirectorKey", "D_Light5") if n in ACT])
P("emergency_lights", alarm_lights)
sm = unreal.NVMover()
sm.set_editor_property("actor", shutter)
sm.set_editor_property("offset", V(0, 0, -640))
P("shutters", [sm])
P("doors_to_seal", [ACT["Door_D_to_E"]] if "Door_D_to_E" in ACT else [])
P("lockdown_drones", drones)
P("emergency_door", em_door)
P("lockdown_troopers", [g for g in troopers_a if g])
P("trooper_door", ACT.get("Door_D_to_E"))
turn = [a for a in EAS.get_all_level_actors() if isinstance(a, unreal.NVGuardCharacter)
        and a.get_actor_label() in ("G2_E_Guard_Sentry", "G2_D_Guard_Gallery")]
for g in turn:
    make_damageable(g)
P("guards_to_turn", turn)
P("flicker_lights", flicker)
P("artery_turret", turret)
P("lift_cab", cab)
gm = unreal.NVMover()
gm.set_editor_property("actor", gate)
gm.set_editor_property("offset", V(0, 0, -300))
P("lift_gate", gm)
P("lift_hatch", hatch)
P("lift_cruise_drop", 1300.0)
P("lift_plunge_drop", 1500.0)
P("lift_lines", lines("M01_AION_04", "M01_Ghost_06"))
if SPARKS:
    P("sparks_fx", SPARKS)
if BOOM:
    P("lift_brake_sound", BOOM)
P("surgical_arms", arms)
P("suite_door", suite_door)
P("suite_lights", suite_lights)
P("agency_tag", tagi)
P("reclamation_lines", lines("M01_AION_05", "M01_AION_06", "M01_AION_07", "M01_AION_08", "M01_AION_09"))
P("recovery_lines", lines("M01_Ghost_08", "M01_AION_10", "M01_Ghost_09"))
P("health_after", 35.0)
P("conduit_mag_ammo", 6)
P("conduit_reserve_ammo", 0)

unreal.SystemLibrary.execute_console_command(UES.get_editor_world(), "RebuildNavigation")
LES.save_current_level()
log("saved")
open(unreal.Paths.project_saved_dir() + "NV_setup_m01.txt", "w", encoding="utf-8").write("\n".join(REPORT))
unreal.log("NV_SETUP_M01 done")
