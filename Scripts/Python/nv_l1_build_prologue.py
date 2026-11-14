"""NEON VEIL - Level 1 prologue (M00P "Crown Line") built on the Sci-Fi Tram Station map.

Street (Veyra lower city, CitySample facades + Soul City dressing, rain) -> transit hub lobby (tram-station kit)
-> lift (NVElevator) up to the station concourse -> X-ray checkpoint -> departure board (opens the platform gate)
-> stairs -> platform (slide + vault tutorials) -> Platform One -> tram (NVTramService) -> L_M00_GlassCrown.

Re-runnable: everything this script adds lives in outliner folders under "P_"; they are deleted and rebuilt.
Base station actors that the route replaces are removed by label. Report: Saved/NV_l1_build_prologue.txt
"""
import glob, math, os, zipfile
import unreal

OUT = []
def log(*a):
    OUT.append(" ".join(str(x) for x in a))

EAL = unreal.EditorAssetLibrary
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
LES = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
AT = unreal.AssetToolsHelpers.get_asset_tools()
V = lambda x, y, z: unreal.Vector(x, y, z)
def R(p=0.0, y=0.0, r=0.0):
    return unreal.Rotator(roll=r, pitch=p, yaw=y)
def T(s):
    return unreal.Text(s)
def tag(n):
    t = unreal.GameplayTag(); t.import_text(f'(TagName="{n}")'); return t
# voice takes (imported by nv_vo_hook M00P) are attached by matching subtitle text
_proj = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
VOICE = {}
try:
    import json as _json
    for _l in _json.load(open(os.path.join(_proj, "Scripts", "VO", "M00P_lines.json"))):
        _p = "/Game/NeonVeil/Audio/VO/M00P/VO_" + _l["id"]
        if unreal.EditorAssetLibrary.does_asset_exist(_p):
            VOICE[_l["text"].strip()] = unreal.load_asset(_p)
except Exception as _e:
    OUT.append("voice map failed: %s" % _e)
def line(spk, txt, d=4.0):
    l = unreal.NVSubtitleLine(); l.set_editor_property("speaker", T(spk)); l.set_editor_property("text", T(txt)); l.set_editor_property("duration", d)
    v = VOICE.get(txt.strip())
    if v:
        l.set_editor_property("voice", v)
        l.set_editor_property("duration", max(d, v.get_editor_property("duration") + 0.35))
    return l
def load(p):
    a = unreal.load_asset(p)
    if not a:
        log("MISSING", p)
    return a

SRC_MAP = "/Game/SciFiTramStation/Maps/SciFiStation"
MAP = "/Game/NeonVeil/Maps/M00/L_M00_Prologue"
TS = "/Game/SciFiTramStation"
ZS = -12000.0                    # street + lobby floor: the concourse (z 400) is 124 m up, a long lift ride into the sky
LIFT_X, LIFT_Y = 7046.0, -4572.0  # cab centre (between the two door walls)

# ------------------------------------------------------------------ map
# (duplicate_asset on a world keeps the copy alive in memory and crashes the next load_level,
#  so load the source map and "Save As" instead)
if not EAL.does_asset_exist(MAP):
    LES.load_level(SRC_MAP)
    ok = unreal.EditorLoadingAndSavingUtils.save_map(unreal.EditorLevelLibrary.get_editor_world(), MAP)
    log("saved station map as", MAP, ok)
if not unreal.EditorLevelLibrary.get_editor_world().get_path_name().startswith(MAP):
    LES.load_level(MAP)
world = unreal.EditorLevelLibrary.get_editor_world()
log("world:", world.get_path_name())

# wipe our previous build: by outliner folder, by our actor tag, and by the label manifest of the last build
# (some lights lost their folder on earlier runs and survived the folder-only wipe)
import json, re
MANIFEST = unreal.Paths.project_saved_dir() + "NV_l1_prologue_labels.json"
try:
    prev_labels = set(json.load(open(MANIFEST)))
except Exception:
    prev_labels = set()
STRAY = re.compile(r"^(StreetLamp_[EW]_\d+_L|Neon_\d+_Glow|XRay_Spot|Board_Glow|Tut_(Sprint|Slide|Vault)|Hub_Canopy_L)$")
nw = 0
for a in EAS.get_all_level_actors():
    lab = a.get_actor_label()
    folder = str(a.get_folder_path())
    if folder.startswith("P_") or "NVP" in [str(t) for t in a.tags] or \
            (folder in ("None", "") and (lab in prev_labels or STRAY.match(lab))):
        EAS.destroy_actor(a); nw += 1
log("wiped:", nw)
SPAWNED = []

def mesh_of(a):
    if isinstance(a, unreal.StaticMeshActor) and a.static_mesh_component.static_mesh:
        return a.static_mesh_component.static_mesh.get_name()
    return ""

# base actors the route replaces
for a in EAS.get_all_level_actors():
    l = a.get_actor_location()
    m = mesh_of(a)
    kill = False
    if isinstance(a, unreal.PlayerStart) and not isinstance(a, unreal.NVCheckpoint):
        kill = True
    elif a.get_class().get_name() in ("AtmosphericFog", "LevelSequenceActor"):
        kill = True
    elif m == "SM_Wall_Double_A" and abs(l.x - 7046) < 5 and abs(l.y + 4220) < 5:
        kill = True                                   # south concourse end wall -> lift doors
    if kill:
        log("removed", a.get_actor_label(), m)
        EAS.destroy_actor(a)

def spawn(cls, label, loc, rot=None, folder="P_Misc"):
    a = EAS.spawn_actor_from_class(cls, V(*loc), rot or R())
    a.set_actor_label(label)
    a.set_folder_path(folder)
    a.tags = [unreal.Name("NVP")]
    SPAWNED.append(label)
    return a

def sm(mesh, label, loc, rot=None, scale=None, folder="P_Misc", movable=False, mat=None):
    m = load(mesh) if isinstance(mesh, str) else mesh
    a = EAS.spawn_actor_from_object(m, V(*loc), rot or R())
    a.set_actor_label(label)
    a.set_folder_path(folder)
    a.tags = [unreal.Name("NVP")]
    SPAWNED.append(label)
    if scale:
        a.set_actor_scale3d(V(*scale))
    c = a.static_mesh_component
    if movable:
        c.set_mobility(unreal.ComponentMobility.MOVABLE)
    if mat:
        c.set_material(0, load(mat) if isinstance(mat, str) else mat)
    return a

def plight(label, loc, intensity, radius, color=(1, 1, 1), folder="P_Lights", shadows=False, movable=True):
    a = spawn(unreal.PointLight, label, loc, None, folder)
    c = a.point_light_component
    c.set_mobility(unreal.ComponentMobility.MOVABLE if movable else unreal.ComponentMobility.STATIONARY)
    c.set_editor_property("intensity_units", unreal.LightUnits.CANDELAS)
    c.set_editor_property("intensity", intensity)
    c.set_editor_property("attenuation_radius", radius)
    c.set_editor_property("light_color", unreal.Color(int(color[0] * 255), int(color[1] * 255), int(color[2] * 255), 255))
    c.set_editor_property("cast_shadows", shadows)
    return a

def slight(label, loc, rot, intensity, radius, color=(1, 1, 1), outer=50.0, folder="P_Lights", shadows=True):
    a = spawn(unreal.SpotLight, label, loc, rot, folder)
    c = a.spot_light_component
    c.set_mobility(unreal.ComponentMobility.MOVABLE)
    c.set_editor_property("intensity_units", unreal.LightUnits.CANDELAS)
    c.set_editor_property("intensity", intensity)
    c.set_editor_property("attenuation_radius", radius)
    c.set_editor_property("outer_cone_angle", outer)
    c.set_editor_property("light_color", unreal.Color(int(color[0] * 255), int(color[1] * 255), int(color[2] * 255), 255))
    c.set_editor_property("cast_shadows", shadows)
    return a

CUBE = load("/Engine/BasicShapes/Cube")

# ------------------------------------------------------------------ lighting: baked station -> dynamic (Lumen)
nl = 0
for a in EAS.get_all_level_actors():
    if str(a.get_folder_path()).startswith("P_"):
        continue
    for c in a.get_components_by_class(unreal.LightComponent):
        c.set_mobility(unreal.ComponentMobility.MOVABLE)
        if isinstance(c, unreal.PointLightComponent) and not isinstance(c, unreal.SpotLightComponent):
            c.set_editor_property("cast_shadows", False)   # 180 small fill lights: no shadow maps
        nl += 1
    if isinstance(a, unreal.SkyLight):
        c = a.light_component
        c.set_mobility(unreal.ComponentMobility.MOVABLE)
        c.set_editor_property("real_time_capture", True)
        c.set_editor_property("intensity", 0.6)
log("lights made movable:", nl)

# ------------------------------------------------------------------ mission + game mode
f = unreal.DataAssetFactory(); f.set_editor_property("data_asset_class", unreal.NVMissionData)
MPATH = "/Game/NeonVeil/Data/Missions/DA_Mission_M00P"
mission = load(MPATH) if EAL.does_asset_exist(MPATH) else AT.create_asset("DA_Mission_M00P", "/Game/NeonVeil/Data/Missions", unreal.NVMissionData, f)
def obj(oid, text, event, prereq=None, policy=unreal.NVCheckpointPolicy.NONE):
    o = unreal.NVObjectiveDef()
    o.set_editor_property("objective_id", oid); o.set_editor_property("display_text", T(text))
    o.set_editor_property("completion_event_tag", tag(event)); o.set_editor_property("prerequisites", [prereq] if prereq else [])
    o.set_editor_property("checkpoint_policy", policy)
    return o
mission.set_editor_property("mission_id", "M00P")
mission.set_editor_property("mission_title", T("Crown Line"))
mission.set_editor_property("objectives", [
    obj("M00P-O01", "Head to the Veyra Central transit hub", "NV.Event.M00P.EnteredTransitHub"),
    obj("M00P-O02", "Take the lift to the Crown Line concourse", "NV.Event.M00P.LiftArrived", "M00P-O01"),
    obj("M00P-O03", "Check the Crown Line departure board", "NV.Event.M00P.DeparturesChecked", "M00P-O02"),
    obj("M00P-O04", "Go to Platform One", "NV.Event.M00P.PlatformReached", "M00P-O03"),
    obj("M00P-O05", "Board the tram to the Glass Crown", "NV.Event.M00P.TramBoarded", "M00P-O04"),
])
_gc = "/Game/NeonVeil/Maps/M00/L_M00_GlassCrown.L_M00_GlassCrown"
try:
    mission.set_editor_property("next_mission_map", unreal.SystemLibrary.conv_soft_obj_path_to_soft_obj_ref(unreal.SoftObjectPath(_gc)))
    log("next map set via soft ref")
except Exception as e:
    log("next map soft-ref failed:", e)
EAL.save_loaded_asset(mission)

GM = "/Game/NeonVeil/Core/BP_NVGameMode_Prologue"
if not EAL.does_asset_exist(GM):
    bf = unreal.BlueprintFactory(); bf.set_editor_property("parent_class", unreal.NVGameMode)
    AT.create_asset("BP_NVGameMode_Prologue", "/Game/NeonVeil/Core", unreal.Blueprint, bf)
gbp = load(GM)
unreal.BlueprintEditorLibrary.compile_blueprint(gbp)
gcls = EAL.load_blueprint_class(GM)
gcdo = unreal.get_default_object(gcls)
gcdo.set_editor_property("default_pawn_class", EAL.load_blueprint_class("/Game/NeonVeil/Core/BP_NVPlayerCharacter"))
gcdo.set_editor_property("mission", mission)
gcdo.set_editor_property("show_end_card", False)
gcdo.set_editor_property("end_fade_time", 0.0)       # no fade: the tram carries straight on into the Glass Crown map
gcdo.set_editor_property("transition_delay", 0.15)
gcdo.set_editor_property("preload_next_map", True)    # Glass Crown loads in the background while the station plays
EAL.save_loaded_asset(gbp)
ws = world.get_world_settings()
log("old kill_z:", ws.get_editor_property("kill_z"))
ws.set_editor_property("default_game_mode", gcls)
ws.set_editor_property("kill_z", -40000.0)        # the street sits 12400 below the station's original KillZ


def sp(o, name, val):
    """set_editor_property that logs instead of aborting the whole build (tries common UE renames)."""
    for nm in (name, "enable_" + name, "b_" + name):
        try:
            o.set_editor_property(nm, val); return True
        except Exception as e:
            err = e
    log("SET FAIL", type(o).__name__, name, err)
    return False

# ------------------------------------------------------------------ glow materials (signs + neon strips)
MEL = unreal.MaterialEditingLibrary
MATDIR = "/Game/NeonVeil/Materials/Prologue"
def make_unlit(name, use_vertex_color):
    path = f"{MATDIR}/{name}"
    if EAL.does_asset_exist(path):
        return load(path)
    m = AT.create_asset(name, MATDIR, unreal.Material, unreal.MaterialFactoryNew())
    m.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    glow = MEL.create_material_expression(m, unreal.MaterialExpressionScalarParameter, -500, 200)
    glow.set_editor_property("parameter_name", "Glow"); glow.set_editor_property("default_value", 6.0)
    if use_vertex_color:
        col = MEL.create_material_expression(m, unreal.MaterialExpressionVertexColor, -500, 0)
    else:
        col = MEL.create_material_expression(m, unreal.MaterialExpressionVectorParameter, -500, 0)
        col.set_editor_property("parameter_name", "Color"); col.set_editor_property("default_value", unreal.LinearColor(0.2, 0.9, 1.0, 1))
    mul = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -250, 0)
    MEL.connect_material_expressions(col, "", mul, "A")
    MEL.connect_material_expressions(glow, "", mul, "B")
    MEL.connect_material_property(mul, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    MEL.recompile_material(m)
    EAL.save_loaded_asset(m)
    return m
def make_text_mat(name):
    """unlit, masked by the font atlas (TextRender feeds its font into the 'Font' parameter), glow = vertex colour"""
    path = f"{MATDIR}/{name}"
    if EAL.does_asset_exist(path):
        return load(path)
    m = AT.create_asset(name, MATDIR, unreal.Material, unreal.MaterialFactoryNew())
    m.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    m.set_editor_property("blend_mode", unreal.BlendMode.BLEND_MASKED)
    m.set_editor_property("opacity_mask_clip_value", 0.5)
    fnt = MEL.create_material_expression(m, unreal.MaterialExpressionFontSampleParameter, -700, 300)
    fnt.set_editor_property("parameter_name", "Font")
    fnt.set_editor_property("font", load("/Engine/EngineFonts/RobotoDistanceField"))
    glow = MEL.create_material_expression(m, unreal.MaterialExpressionScalarParameter, -700, 150)
    glow.set_editor_property("parameter_name", "Glow"); glow.set_editor_property("default_value", 5.0)
    vc = MEL.create_material_expression(m, unreal.MaterialExpressionVertexColor, -700, 0)
    m1 = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -450, 0)
    m2 = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -250, 0)
    MEL.connect_material_expressions(vc, "", m1, "A")
    MEL.connect_material_expressions(glow, "", m1, "B")
    MEL.connect_material_expressions(m1, "", m2, "A")
    MEL.connect_material_expressions(fnt, "R", m2, "B")
    MEL.connect_material_property(m2, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    MEL.connect_material_property(fnt, "R", unreal.MaterialProperty.MP_OPACITY_MASK)
    MEL.recompile_material(m)
    EAL.save_loaded_asset(m)
    return m
M_SIGNTEXT = make_text_mat("M_NV_SignText_DF")
M_GLOW = make_unlit("M_NV_Glow", False)
def glow_mi(name, color, glow=8.0):
    path = f"{MATDIR}/{name}"
    mi = load(path) if EAL.does_asset_exist(path) else AT.create_asset(name, MATDIR, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    MEL.set_material_instance_parent(mi, M_GLOW)
    MEL.set_material_instance_vector_parameter_value(mi, "Color", unreal.LinearColor(*color, 1))
    MEL.set_material_instance_scalar_parameter_value(mi, "Glow", glow)
    EAL.save_loaded_asset(mi)
    return mi
GL_CYAN = glow_mi("MI_NV_Glow_Cyan", (0.15, 0.85, 1.0))
GL_MAG = glow_mi("MI_NV_Glow_Magenta", (1.0, 0.15, 0.7))
GL_AMBER = glow_mi("MI_NV_Glow_Amber", (1.0, 0.55, 0.1))

# ------------------------------------------------------------------ materials
M_WALL = f"{TS}/Materials/M_Basic_Wall"
M_DARK = f"{TS}/Materials/MI_Trim_B"
M_DOOR = f"{TS}/Materials/MI_Door_A"
M_WET = "/Game/SoulCity/Environment/Materials/Rocks/MI_Generic_Concrete01_Wet"
M_WETTILE = "/Game/SoulCity/Environment/Materials/Building/MI_Slums_Concrete_Tiles02_Wet"

# ------------------------------------------------------------------ lift shaft, cab, landing doors
FL = "P_Lift"
SW = (V(0, 0, 0))
def box(label, center, size, mat=M_WALL, folder=FL, movable=False):
    a = sm(CUBE, label, center, None, (size[0] / 100.0, size[1] / 100.0, size[2] / 100.0), folder, movable, mat)
    return a
# shaft: x 6826..7266, y -4250..-4730, z ZS-50 .. 860. The east side is glass from just above the lobby to just under the
# concourse: the cab rises 124 m past the night city (towers to the east) and light bands stream past on the far wall.
GLASS = None
try:
    _AR = unreal.AssetRegistryHelpers.get_asset_registry()
    _g = [x for x in _AR.get_assets(unreal.ARFilter(package_paths=[TS], recursive_paths=True,
          class_paths=[unreal.TopLevelAssetPath("/Script/Engine", "StaticMesh")])) if str(x.asset_name) == "SM_Tram_Glass"]
    GLASS = unreal.load_asset(str(_g[0].package_name)).get_material(0)
    log("glass material:", GLASS.get_path_name())
except Exception as e:
    log("glass material lookup failed:", e)
ZB, ZT = ZS - 50.0, 860.0
def vbox(label, x, y, z0, z1, sx, sy, mat):
    box(label, (x, y, (z0 + z1) / 2.0), (sx, sy, z1 - z0), mat)
vbox("Shaft_W", 6806, -4572, ZB, ZT, 40, 520, M_DARK)
vbox("Shaft_E_Low", 7286, -4572, ZB, ZS + 450, 40, 520, M_DARK)
vbox("Shaft_E_Glass", 7286, -4572, ZS + 450, -60, 20, 520, GLASS or M_DARK)
vbox("Shaft_E_High", 7286, -4572, -60, ZT, 40, 520, M_DARK)
for k, y in enumerate((-4320, -4572, -4824)):            # mullions so the glass reads as glass
    vbox(f"Shaft_E_Mullion{k}", 7300, y, ZS + 450, -60, 14, 14, M_DARK)
vbox("Shaft_N_Low", 7046, -4357, ZS, 355, 520, 30, M_DARK)         # behind the cab, below the concourse floor
vbox("Shaft_S_High", 7046, -4787, ZS + 400, ZT, 520, 30, M_DARK)   # above the lobby ceiling
box("Shaft_Top", (7046, -4572, 870), (520, 520, 30), M_DARK)
box("Shaft_Pit", (7046, -4572, ZS - 70), (520, 520, 40), M_DARK)
for k, z in enumerate(range(int(ZS + 700), 300, 600)):   # speed bands on the west wall + back wall
    box(f"Shaft_Band_W{k}", (6828, -4572, z), (4, 500, 10), GL_CYAN if k % 3 else GL_MAG)
    box(f"Shaft_Band_N{k}", (7046, -4373, z + 300), (420, 4, 6), GL_CYAN)
# cab (moves): floor top at ZS
cab = [
    sm(f"{TS}/Meshes/SM_Floor", "Cab_Floor", (LIFT_X, LIFT_Y, ZS), None, None, FL, True),
    box("Cab_Wall_W", (LIFT_X - 195, LIFT_Y, ZS + 170), (10, 400, 340), M_DARK, FL, True),
    box("Cab_Wall_E", (LIFT_X + 195, LIFT_Y, ZS + 170), (6, 400, 340), GLASS or M_DARK, FL, True),
    box("Cab_Rail_E", (LIFT_X + 180, LIFT_Y, ZS + 100), (10, 380, 8), M_DARK, FL, True),
    box("Cab_Ceiling", (LIFT_X, LIFT_Y, ZS + 345), (400, 400, 10), M_DARK, FL, True),
    sm(f"{TS}/Meshes/SM_Light_B", "Cab_LightBar", (LIFT_X, LIFT_Y, ZS + 338), R(y=90), None, FL, True),
    sm(f"{TS}/Meshes/SM_Holoscreen_D", "Cab_Screen", (LIFT_X - 188, LIFT_Y, ZS + 190), R(y=90), None, FL, True),
]
cab_light = plight("Cab_Light", (LIFT_X, LIFT_Y, ZS + 300), 40.0, 600, (0.8, 0.95, 1.0), FL)
cab.append(cab_light)
# upper landing (concourse south end, wall line y = -4220, facing north)
UP = (7046, -4220, 400)
sm(f"{TS}/Meshes/SM_Wall_Door_A", "Up_DoorWall", UP, R(y=180), None, FL)
sm(f"{TS}/Meshes/SM_Wall", "Up_Wall_W", (6646, -4220, 400), R(y=180), None, FL)
sm(f"{TS}/Meshes/SM_Wall", "Up_Wall_E", (7446, -4220, 400), R(y=180), None, FL)
up_l = sm(f"{TS}/Meshes/SM_Door_Left", "Up_Door_L", UP, R(y=180), None, FL, True)
up_r = sm(f"{TS}/Meshes/SM_Door_Right", "Up_Door_R", UP, R(y=180), None, FL, True)
# lower landing (lobby north wall, y = -4924, facing south)
LO = (7046, -4924, ZS)
sm(f"{TS}/Meshes/SM_Wall_Door_A", "Lo_DoorWall", LO, R(y=0), None, FL)
lo_l = sm(f"{TS}/Meshes/SM_Door_Left", "Lo_Door_L", LO, R(y=0), None, FL, True)
lo_r = sm(f"{TS}/Meshes/SM_Door_Right", "Lo_Door_R", LO, R(y=0), None, FL, True)

lift = spawn(unreal.NVElevator, "B_Lift", (LIFT_X, LIFT_Y, ZS), None, FL)
sp(lift, "cab_parts", cab)
sp(lift, "travel", V(0, 0, 400 - ZS))
sp(lift, "ride_time", 24.0)
sp(lift, "start_delay", 1.0)
sp(lift, "lower_doors", [lo_l, lo_r])
sp(lift, "lower_door_open_offsets", [V(115, 0, 0), V(-115, 0, 0)])
sp(lift, "upper_doors", [up_l, up_r])
sp(lift, "upper_door_open_offsets", [V(-115, 0, 0), V(115, 0, 0)])
sp(lift, "required_active_objective", "M00P-O02")
sp(lift, "arrived_event_tag", tag("NV.Event.M00P.LiftArrived"))
sp(lift, "door_sound", load("/Game/NeonVeil/Audio/SFX/SFX_Tram_Dock"))
sp(lift, "ride_sound", load("/Game/NeonVeil/Audio/SFX/SFX_Tram_RideLoop"))
lift.get_editor_property("cab_volume").set_box_extent(V(170, 170, 120))

# ------------------------------------------------------------------ transit hub lobby (tram-station kit)
FB = "P_Lobby"
X0, X1, Y0, Y1 = 5846, 8246, -4924, -6524       # interior span
for ix, x in enumerate(range(6046, 8247, 400)):
    for iy, y in enumerate(range(-5124, -6525, -400)):
        sm(f"{TS}/Meshes/SM_Floor", f"Lobby_Floor_{ix}_{iy}", (x, y, ZS), None, None, FB)
        sm(f"{TS}/Meshes/SM_Ceiling_A", f"Lobby_Ceil_{ix}_{iy}", (x, y, ZS + 400), R(r=180), None, FB)
# north wall (lift side) around the door wall at 6846..7246
for i, x in enumerate((6046, 6446, 7646, 8046)):
    sm(f"{TS}/Meshes/SM_Wall", f"Lobby_N_{i}", (x, Y0, ZS), R(y=0), None, FB)
sm(f"{TS}/Meshes/SM_Wall", "Lobby_N_fillW", (6746, Y0, ZS), R(y=0), (0.5, 1, 1), FB)
sm(f"{TS}/Meshes/SM_Wall", "Lobby_N_fillE", (7346, Y0, ZS), R(y=0), (0.5, 1, 1), FB)
# side walls
for i, y in enumerate((-5124, -5524, -5924, -6324)):
    sm(f"{TS}/Meshes/SM_Wall_B", f"Lobby_W_{i}", (X0, y, ZS), R(y=90), None, FB)
    sm(f"{TS}/Meshes/SM_Wall_B", f"Lobby_E_{i}", (X1, y, ZS), R(y=-90), None, FB)
# south wall = street facade with the entrance door (tram-station door BP opens on approach)
for i, x in enumerate((6046, 6446, 7646, 8046)):
    sm(f"{TS}/Meshes/SM_Wall", f"Lobby_S_{i}", (x, Y1, ZS), R(y=180), None, FB)
sm(f"{TS}/Meshes/SM_Wall", "Lobby_S_fillW", (6746, Y1, ZS), R(y=180), (0.5, 1, 1), FB)
sm(f"{TS}/Meshes/SM_Wall", "Lobby_S_fillE", (7346, Y1, ZS), R(y=180), (0.5, 1, 1), FB)
door_bp = EAL.load_blueprint_class(f"{TS}/Blueprints/BP_Door_A")
ent = EAS.spawn_actor_from_class(door_bp, V(7046, Y1, ZS), R(y=180))
ent.set_actor_label("Lobby_EntranceDoor"); ent.set_folder_path(FB); ent.tags = [unreal.Name("NVP")]; SPAWNED.append("Lobby_EntranceDoor")
# lighting + dressing
for i, x in enumerate((6246, 7046, 7846)):
    for j, y in enumerate((-5324, -6124)):
        sm(f"{TS}/Meshes/SM_Light_B", f"Lobby_LightBar_{i}_{j}", (x, y, ZS + 398), None, None, FB)
        plight(f"Lobby_PL_{i}_{j}", (x, y, ZS + 340), 80.0, 900, (0.75, 0.92, 1.0), FB)
sm(f"{TS}/Meshes/SM_Holoscreen_C", "Lobby_Holo_W", (X0 + 20, -5724, ZS + 230), R(y=90), None, FB)
sm(f"{TS}/Meshes/SM_Holoscreen_C", "Lobby_Holo_E", (X1 - 20, -5724, ZS + 230), R(y=-90), None, FB)
for i, x in enumerate((6246, 6546, 7546, 7846)):
    sm(f"{TS}/Meshes/SM_Bench_A", f"Lobby_Bench_{i}", (x, -5724, ZS), R(y=0), None, FB)
sm(f"{TS}/Meshes/SM_Snack_machine_a", "Lobby_Snack", (X1 - 60, -6300, ZS), R(y=-90), None, FB)
sm(f"{TS}/Meshes/SM_Column_A", "Lobby_Col_W", (6446, -5724, ZS), None, None, FB)
sm(f"{TS}/Meshes/SM_Column_A", "Lobby_Col_E", (7646, -5724, ZS), None, None, FB)
for i, (x, y) in enumerate(((X0 + 80, Y0 - 80), (X1 - 80, Y0 - 80), (X0 + 80, Y1 + 80), (X1 - 80, Y1 + 80))):
    sm(f"{TS}/Meshes/SM_Light_C", f"Lobby_Lamp_{i}", (x, y, ZS), R(y=45 + 90 * i), None, FB)
    plight(f"Lobby_Lamp_{i}_L", (x, y, ZS + 200), 25.0, 500, (1.0, 0.7, 0.45), FB)
# cyan guide strip on the floor from the entrance to the lift doors, magenta trims along the side walls
box("Lobby_GuideStrip", (7046, (Y0 + Y1) / 2, ZS + 1), (24, abs(Y1 - Y0) - 120, 2), GL_CYAN, FB)
for side, x in (("W", X0 + 26), ("E", X1 - 26)):
    box(f"Lobby_Trim_{side}", (x, (Y0 + Y1) / 2, ZS + 360), (4, abs(Y1 - Y0) - 40, 8), GL_MAG, FB)
plight("Lobby_LiftGlow", (7046, Y0 - 120, ZS + 280), 60.0, 700, (0.2, 0.85, 1.0), FB)
hub = spawn(unreal.NVObjectiveTrigger, "T_EnteredHub", (7046, -6000, ZS + 120), None, FB)
hub.get_editor_property("volume").set_box_extent(V(500, 250, 150))
sp(hub, "event_tag", tag("NV.Event.M00P.EnteredTransitHub"))
sp(hub, "required_active_objective", "M00P-O01")

# ------------------------------------------------------------------ street (CitySample facades, wet ground, rain)
FS = "P_Street"
SY0, SY1 = Y1 - 30, -16500
def tiled(label, center, size, mat, folder, tile=800.0):
    """cube UVs stretch over big boxes (the wet concrete read as water) - lay the surface as tiles instead"""
    nx, ny = max(1, round(size[0] / tile)), max(1, round(size[1] / tile))
    sx, sy = size[0] / nx, size[1] / ny
    for ix in range(nx):
        for iy in range(ny):
            box(f"{label}_{ix}_{iy}", (center[0] - size[0] / 2 + sx * (ix + 0.5), center[1] - size[1] / 2 + sy * (iy + 0.5), center[2]),
                (sx, sy, size[2]), mat, folder)
tiled("Street_Ground", (7046, (SY0 + SY1) / 2, ZS - 25), (5200, abs(SY1 - SY0), 50), M_WET, FS)
tiled("Sidewalk_W", (6046 - 400, (SY0 + SY1) / 2, ZS + 7), (1000, abs(SY1 - SY0), 14), M_WETTILE, FS, 500)
tiled("Sidewalk_E", (8046 + 400, (SY0 + SY1) / 2, ZS + 7), (1000, abs(SY1 - SY0), 14), M_WETTILE, FS, 500)
for side, x in (("W", 3896), ("E", 10196)):   # outer strips under the building fronts
    tiled(f"Kerb_{side}", (x, (SY0 + SY1) / 2, ZS - 25), (1100, abs(SY1 - SY0), 50), M_WET, FS, 1100)
CS = "/Game/CitySampleBuildings/Building/Library"
def bpp(path_hint, label, loc, yaw, folder=FS):
    AR = unreal.AssetRegistryHelpers.get_asset_registry()
    hits = [a for a in AR.get_assets(unreal.ARFilter(package_paths=["/Game/CitySampleBuildings"], recursive_paths=True,
            class_paths=[unreal.TopLevelAssetPath("/Script/Engine", "Blueprint")])) if str(a.asset_name) == path_hint]
    if not hits:
        log("no BPP", path_hint); return None
    a = EAS.spawn_actor_from_object(unreal.load_asset(str(hits[0].package_name)), V(*loc), R(y=yaw))
    a.set_actor_label(label); a.set_folder_path(folder)
    return a
FRONTS = ["BPP_NYAA_Ref_N1", "BPP_NYAC_Ref_N1", "BPP_NYAE_Ref_N1", "BPP_NYAB_Ref_N1", "BPP_NYAF_Ref_N1", "BPP_NYAD_Ref_N1"]
ys = (-8250, -11670, -15090)
for i, y in enumerate(ys):
    bpp(FRONTS[i], f"Front_W_{i}", (5196 - 450, y, ZS), 90)
    bpp(FRONTS[i + 3], f"Front_E_{i}", (8896 + 450, y, ZS), -90)
bpp("BPP_NYAB_Ref_N1", "Front_S_End", (7046, -17100, ZS), 0)
# skyline mass behind the fronts
for i, (name, loc) in enumerate((("BPP_CHA_Ref_N1", (1500, -9000)), ("BPP_CHE_Ref_A1_N1", (1500, -15000)),
                                  ("BPP_SFE_Ref_N1", (12600, -9500)), ("BPP_CHH_Ref_A1_N1", (12600, -15500)),
                                  ("BPP_NYG_Ref_N1", (7046, -23000)))):
    bpp(name, f"Skyline_{i}", (loc[0], loc[1], ZS), 0, "P_Skyline")
# (the lift-view skyline is built by nv_l1_city_dress.py: low foreground, modern towers + sci-fi spires, Glass Crown)
# hub facade above the lobby entrance (hides the station box behind)
NROWS = int((400 - ZS) / 400) + 1
for row in range(NROWS):
    xs = [4246, 5046, 9046, 9846] + ([6246, 7846] if row > 0 else [])
    for i, x in enumerate(xs):
        sm(f"{TS}/Meshes/SM_Wall_Double_A", f"Hub_Facade_{row}_{i}", (x, Y1 - 40, ZS + row * 400), R(y=180), None, FB)
    if row > 0:
        sm(f"{TS}/Meshes/SM_Wall", f"Hub_Facade_{row}_mid", (7046, Y1 - 40, ZS + row * 400), R(y=180), None, FB)
    if row == 0:
        for i, x in enumerate((5646, 8446)):
            sm(f"{TS}/Meshes/SM_Wall", f"Hub_Facade_0_fill{i}", (x, Y1 - 40, ZS), R(y=180), None, FB)
# neon bands across the hub facade + a canopy glow over the entrance
for a in EAS.get_all_level_actors():
    if a.get_actor_label().startswith("Hub_Facade_"):
        smc = a.static_mesh_component
        for mi in range(smc.get_num_materials()):
            smc.set_material(mi, load(M_DARK))
for row in range(1, NROWS):
    box(f"Hub_Band_{row}", (7046, Y1 - 100, ZS + row * 400 - 10), (6400, 6, 14), GL_CYAN if row % 2 else GL_MAG, FS)
for i, x in enumerate((3870, 10220)):
    box(f"Hub_Edge_{i}", (x, Y1 - 100, ZS + NROWS * 200), (14, 6, NROWS * 400), GL_AMBER, FS)
box("Hub_Canopy", (7046, Y1 - 200, ZS + 430), (1400, 300, 20), M_DARK, FS)
box("Hub_Canopy_Glow", (7046, Y1 - 200, ZS + 418), (1300, 260, 2), GL_CYAN, FS)
slight("Hub_Canopy_L", (7046, Y1 - 260, ZS + 410), R(p=-90), 600, 900, (0.3, 0.9, 1.0), 60, "P_Lights", False)
# street exposure: the station's unbound post volume is tuned for its bright interior; darken the street for night
ppv = spawn(unreal.PostProcessVolume, "Street_PostProcess", (7046, (SY0 + SY1) / 2, ZS + 1500), None, FS)
ppv.set_actor_scale3d(V(8000 / 200.0, abs(SY1 - SY0) / 200.0, 4000 / 200.0))
sp(ppv, "priority", 2.0)
sp(ppv, "blend_radius", 600.0)
st = ppv.settings
st.set_editor_property("override_auto_exposure_bias", True); st.set_editor_property("auto_exposure_bias", 0.2)
st.set_editor_property("override_white_temp", True); st.set_editor_property("white_temp", 7600.0)
st.set_editor_property("override_vignette_intensity", True); st.set_editor_property("vignette_intensity", 0.55)
ppv.set_editor_property("settings", st)
# rain + ambience
rain = spawn(unreal.NVRainField, "Street_Rain", (7046, -11400, ZS + 900), None, FS)
sp(rain, "extent", V(1600, 5200, 900))
sp(rain, "count", 1100)  # halved for GPU headroom
amb = spawn(unreal.AmbientSound, "Street_RainAmb", (7046, -11000, ZS + 300), None, FS)
sp(amb.audio_component, "sound", load("/Game/SoulCity/Sound/Cue/AmbientLooping/Rain_Heavy_Ext_Cue"))
amb2 = spawn(unreal.AmbientSound, "Street_CityAmb", (7046, -13000, ZS + 300), None, FS)
sp(amb2.audio_component, "sound", load("/Game/NeonVeil/Audio/Ambience/SFX_AMB_Crown_CityRain"))
# street lights + neon
for i, y in enumerate(range(-7300, -16001, -1700)):
    for side, x, yaw in (("W", 5746, 0), ("E", 8346, 180)):
        sm("/Game/SoulCity/Environment/Meshes/Building_Slum/SM_Streetlight", f"StreetLamp_{side}_{i}", (x, y, ZS), R(y=yaw), None, FS)
        slight(f"StreetLamp_{side}_{i}_L", (x + (220 if side == "W" else -220), y, ZS + 620), R(p=-90), 1500, 1800,
               (1.0, 0.75, 0.45), 55, "P_Lights", shadows=(i % 2 == 0))
NEON = "/Game/Sci_Fi_Light/Static_Meshes/SM_Sci_Fi_X_Frame_Neon_Sign/Mesh/SM_Sci_Fi_X_Frame_Neon_Sign"
for i, (x, y, yaw, col) in enumerate(((5420, -7400, 90, (1.0, 0.2, 0.8)), (8670, -9300, -90, (0.2, 0.9, 1.0)),
                                       (5420, -12000, 90, (0.3, 1.0, 0.6)), (8670, -13600, -90, (1.0, 0.45, 0.1)))):
    sm(NEON, f"Neon_{i}", (x, y, ZS + 520), R(y=yaw), (2, 2, 2), FS)
    plight(f"Neon_{i}_Glow", (x + (150 if yaw == 90 else -150), y, ZS + 520), 60.0, 900, col, "P_Lights")
# one height fog for the whole map: the station's fog sat at z=100 (warm, 0.05) and turned the street (1700 below it)
# into a bright haze. Move it down to street level and make it a dark, cool night fog.
for a in EAS.get_all_level_actors():
    if isinstance(a, unreal.ExponentialHeightFog):
        a.set_actor_location(V(7046, -6000, ZS - 50), False, False)
        fc = a.component
        sp(fc, "fog_density", 0.018)
        sp(fc, "fog_height_falloff", 0.25)
        sp(fc, "fog_inscattering_luminance", unreal.LinearColor(0.012, 0.018, 0.035, 1))
        sp(fc, "directional_inscattering_luminance", unreal.LinearColor(0, 0, 0, 1))
        sp(fc, "volumetric_fog", True)
        log("fog retuned:", a.get_actor_label())

# player start (south end of the street, facing the hub)
ps = spawn(unreal.PlayerStart, "PlayerStart_Street", (7046, -15800, ZS + 100), R(y=90), FS)
comms = spawn(unreal.NVObjectiveTrigger, "T_RecallComms", (7046, -15500, ZS + 120), None, FS)
comms.get_editor_property("volume").set_box_extent(V(900, 900, 200))
sp(comms, "delay", 1.5)
sp(comms, "lines_on_complete", [
    line("Ops Monitor", "Ghost-7, Directorate Ops. You are recalled to the Glass Crown, effective immediately. Take the Crown Line from Veyra Central. A car is being held for you.", 9.6),
    line("Ghost-7", "Copy. On my way.", 2.6)])

# ------------------------------------------------------------------ concourse: X-ray checkpoint + PA, departure board
FC = "P_Concourse"
XR_LOC = (7046, -3650, 400)
xray_meshes = []
AR = unreal.AssetRegistryHelpers.get_asset_registry()
for a in AR.get_assets(unreal.ARFilter(package_paths=["/Game/NeonVeil/Art/XRay"], recursive_paths=True,
                                       class_paths=[unreal.TopLevelAssetPath("/Script/Engine", "StaticMesh")])):
    xray_meshes.append(str(a.package_name))
for i, p in enumerate(sorted(xray_meshes)):
    sm(p, f"XRay_{i}", XR_LOC, R(y=90), None, FC)
log("xray meshes placed:", len(xray_meshes))
scan = spawn(unreal.NVObjectiveTrigger, "T_XRayScan", (7046, -3650, 520), None, FC)
scan.get_editor_property("volume").set_box_extent(V(160, 120, 150))
sp(scan, "delay", 1.2)
sp(scan, "start_notice", T("Scanning..."))
sp(scan, "lines_on_complete", [
    line("Security", "Directorate clearance confirmed. Ghost-7. Proceed.", 4.3),
    line("Station PA", "Welcome to Veyra Central. Crown Line service to the Glass Crown departs from Platform One. Platform access is restricted to cleared personnel.", 8.8)])
slight("XRay_Spot", (7046, -3650, 780), R(p=-90), 800, 700, (0.4, 1.0, 0.9), 40, "P_Lights", False)

board = spawn(unreal.NVInteractableActor, "I_DepartureBoard", (6950, 1900, 400), R(y=-90), FC)
bm = board.get_editor_property("mesh")
bm.set_static_mesh(load(f"{TS}/Meshes/SM_Holoscreen_A"))
sp(board, "prompt", T("Check Crown Line departures"))
sp(board, "completion_event_tag", tag("NV.Event.M00P.DeparturesChecked"))
sp(board, "required_active_objective", "M00P-O03")
sp(board, "lines_on_use", [line("Ops Monitor", "Departure confirmed. I've unlocked the platform gates for you. Your car is inbound.", 5.6)])
plight("Board_Glow", (6950, 1750, 650), 60.0, 700, (0.3, 0.85, 1.0), "P_Lights")

# platform gates at the top of the stairs (north stairs open on O03; south stays shut)
def gate(label, y, open_when):
    d = spawn(unreal.NVObjectiveDoor, label, (6300, y, 400), None, FC)
    for comp_name, dy in (("panel_left", -105), ("panel_right", 105)):
        c = d.get_editor_property(comp_name)
        c.set_static_mesh(CUBE)
        sp(c, "relative_location", V(0, dy, 175))
        sp(c, "relative_scale3d", V(0.1, 2.1, 3.5))
        c.set_material(0, load(M_DOOR))
    if open_when:
        sp(d, "open_when_complete", open_when)
    sp(d, "slide_distance", 215)
    return d
gate("G_Gate_North", -620, "M00P-O03")
gate("G_Gate_South", -2225, "")

# ------------------------------------------------------------------ wayfinding signs (emissive text over holoscreens)
def sign(label, text, loc, yaw, size=34.0, color=(0.35, 0.95, 1.0), folder="P_Signs"):
    a = spawn(unreal.TextRenderActor, label, loc, R(y=yaw), folder)
    t = a.text_render
    sp(t, "text", T(text))
    sp(t, "world_size", size)
    sp(t, "horizontal_alignment", unreal.HorizTextAligment.EHTA_CENTER)
    sp(t, "vertical_alignment", unreal.VerticalTextAligment.EVRTA_TEXT_CENTER)
    sp(t, "text_render_color", unreal.Color(int(color[0] * 255), int(color[1] * 255), int(color[2] * 255), 255))
    t.set_material(0, M_SIGNTEXT)
    return a
sign("S_Hub", "VEYRA CENTRAL", (7046, Y1 - 120, ZS + 900), -90, 160, (0.4, 0.95, 1.0))
sign("S_Hub2", "CROWN LINE  ·  TRANSIT", (7046, Y1 - 120, ZS + 700), -90, 70, (1.0, 0.85, 0.5))
sign("S_LobbyLift", "LIFT  ·  CROWN LINE CONCOURSE", (7046, Y0 - 50, ZS + 330), -90, 22)
sign("S_ConcourseN", "CROWN LINE  ·  DEPARTURES  >>", (6900, -3200, 700), -90, 40)
sign("S_ConcourseN2", "DEPARTURES  >>", (6900, -1000, 700), -90, 40)
sign("S_Board", "CROWN LINE  ·  DEPARTURES", (6950, 1700, 860), -90, 34)
sign("S_StairsN", "PLATFORM 1  ·  CROWN LINE  >>", (6420, -620, 700), 0, 30)
sign("S_StairsS", "PLATFORM 2  ·  CLOSED FOR MAINTENANCE", (6420, -2225, 700), 0, 26, (1.0, 0.55, 0.15))
sign("S_Plat1", "PLATFORM 1  ·  CROWN LINE TO THE GLASS CROWN  >>", (4800, -300, 330), 0, 26)
sign("S_Plat1b", "CROWN LINE  ·  BOARD HERE  >>", (3100, -300, 330), 0, 26)

# ------------------------------------------------------------------ platform: slide shutter, vault crates, boarding
FPL = "P_Platform"
box("Shutter_Slide", (4200, -615, 115 + 150), (40, 830, 300), M_DOOR, FPL)            # 115 cm gap underneath
sm(f"{TS}/Meshes/SM_Box_B", "Vault_Crate_A", (2950, -450, 0), R(y=0), None, FPL)
sm(f"{TS}/Meshes/SM_Box_B", "Vault_Crate_B", (2950, -840, 0), R(y=0), None, FPL)
def tut(label, action, text, center, ext, notice, objective="M00P-O04"):
    z = spawn(unreal.NVTutorialZone, label, center, None, "P_Tutorial")
    sp(z, "action", action)
    sp(z, "instruction", T(text))
    sp(z, "complete_notice", T(notice))
    sp(z, "required_active_objective", objective)
    z.get_editor_property("volume").set_box_extent(V(*ext))
    return z
tut("Tut_Sprint", unreal.NVTutorialAction.SPRINT, "Hold {Sprint} to sprint", (6900, -1900, 520), (550, 1500, 150), "Sprint", "M00P-O03")
tut("Tut_Slide", unreal.NVTutorialAction.SLIDE, "Sprint, then press {Crouch} to slide under the shutter", (4500, -615, 120), (450, 420, 150), "Slide")
tut("Tut_Vault", unreal.NVTutorialAction.VAULT, "Press {Jump} at the crates to vault", (3250, -615, 120), (350, 420, 150), "Vault")
plat = spawn(unreal.NVObjectiveTrigger, "T_PlatformOne", (1910, -700, 120), None, FPL)
plat.get_editor_property("volume").set_box_extent(V(900, 320, 150))
sp(plat, "event_tag", tag("NV.Event.M00P.PlatformReached"))
sp(plat, "required_active_objective", "M00P-O04")

# ------------------------------------------------------------------ tram service (BP_Tram)
tram = [a for a in EAS.get_all_level_actors() if a.get_class().get_name() == "BP_Tram_C"]
# the station's placed tram is Static; switching mobility at runtime leaves its collision behind at the platform
# (the rider stands on invisible collision while the tram leaves). Make every part Movable in the map itself.
for t in tram:
    for c in t.get_components_by_class(unreal.SceneComponent):
        c.set_mobility(unreal.ComponentMobility.MOVABLE)
    log("tram mobility -> movable:", t.get_actor_label())
svc = spawn(unreal.NVTramService, "B_TramService", (1910, -1420, 10), R(y=0), FPL)
if tram:
    sp(svc, "tram", tram[0])
sp(svc, "arrive_on_objective", "M00P-O05")
sp(svc, "boarded_event_tag", tag("NV.Event.M00P.TramBoarded"))
# hand-off: 6.5 s after pulling out the tram is deep in the west tunnel (~14 m/s); the objective completes, the
# game mode travels with no fade, and the Glass Crown map picks the ride up inside its own tunnel portal at that speed
sp(svc, "boarded_event_delay", 6.5)
sp(svc, "run_sound", load("/Game/NeonVeil/Audio/SFX/SFX_Tram_RideLoop"))
sp(svc, "dock_sound", load("/Game/NeonVeil/Audio/SFX/SFX_Tram_Dock"))
sp(svc, "door_sound", load("/Game/NeonVeil/Audio/SFX/SFX_Tram_Dock"))
if EAL.does_asset_exist("/Game/NeonVeil/Audio/VO/M00P/VO_p06_pa_arriving"):
    sp(svc, "arrival_announcement", load("/Game/NeonVeil/Audio/VO/M00P/VO_p06_pa_arriving"))
log("voice lines available:", len(VOICE))
log("tram found:", bool(tram))

# future-city dressing (street, sky, lift view) - its own script so it can be iterated on its own
import runpy, sys as _sys
_argv = list(_sys.argv)
_sys.argv = ["nv_l1_city_dress.py", "prologue"]
try:
    runpy.run_path(os.path.join(os.path.dirname(os.path.abspath(__file__)), "nv_l1_city_dress.py"), run_name="__main__")
    log("city dressing: ok")
except Exception as _e:
    log("city dressing FAILED:", _e)
_sys.argv = _argv
json.dump(sorted(set(SPAWNED)), open(MANIFEST, "w"))
LES.save_current_level()
open(unreal.Paths.project_saved_dir() + "NV_l1_build_prologue.txt", "w").write("\n".join(OUT))
