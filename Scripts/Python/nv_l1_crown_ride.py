"""Glass Crown (L_M00_GlassCrown): replace the old Dekogon NYC subway arrival with the continuous Crown Line ride.

The prologue tram (Sci-Fi Tram Station BP_Tram) leaves Veyra Central into the west tunnel; the game hands off to this
map inside that tunnel. Here the player starts in the same BP_Tram inside the bore of a dark transit spire ~550 m west
of the Crown, bursts out into the skyline, takes an S-bend (turn 1) between two tower groups, runs the long straight,
sweeps right (turn 2) onto the Crown approach and docks at the arrival platform (doors on the platform side open).
~46 s at 14.5 m/s with music; the Crown's ambient bed fades in once the doors open.

Removes every old subway car piece (T_*), the C00 straight-rail arrival rig and the old rails/pylons, and anything
using /Game/SubwayTrain meshes. Idempotent (R_* actors are rebuilt). Report: Saved/NV_l1_crown_ride.txt"""
import unreal

OUT = []
def log(*a):
    OUT.append(" ".join(str(x) for x in a))

EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
LES = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
EAL = unreal.EditorAssetLibrary
V = unreal.Vector
def R(p=0.0, y=0.0, r=0.0):
    return unreal.Rotator(roll=r, pitch=p, yaw=y)

MAP = "/Game/NeonVeil/Maps/M00/L_M00_GlassCrown"
w = unreal.EditorLevelLibrary.get_editor_world()
if not w.get_path_name().startswith(MAP):
    LES.load_level(MAP)
log("map:", unreal.EditorLevelLibrary.get_editor_world().get_path_name())

TS = "/Game/SciFiTramStation"
MATS = "/Game/NeonVeil/Tests/Materials"
M_DARK = unreal.load_asset(f"{MATS}/TEMP_M_Titanium")
M_CYAN = unreal.load_asset(f"{MATS}/TEMP_M_CyanEmissive")
CUBE = unreal.load_asset("/Engine/BasicShapes/Cube")
FOLDER = "R_CrownLine"

# ---------------------------------------------------------------- remove the NYC subway car + old arrival rig
gone = 0
for a in list(EAS.get_all_level_actors()):
    lab = a.get_actor_label()
    mesh = ""
    if isinstance(a, unreal.StaticMeshActor) and a.static_mesh_component.static_mesh:
        mesh = a.static_mesh_component.static_mesh.get_path_name()
    cls = a.get_class().get_path_name()
    if (lab.startswith(("T_", "C00_", "R_")) or lab in ("A_TramLight",) or "/Game/SubwayTrain" in mesh
            or "/Game/SubwayTrain" in cls or str(a.get_folder_path()) in ("Tram", FOLDER)):
        EAS.destroy_actor(a); gone += 1
# any component anywhere still using the subway kit
left = []
for a in EAS.get_all_level_actors():
    for c in a.get_components_by_class(unreal.StaticMeshComponent):
        m = c.static_mesh
        if m and "/Game/SubwayTrain" in m.get_path_name():
            left.append(a.get_actor_label())
log("removed old tram actors:", gone, "| still using SubwayTrain:", sorted(set(left)))

def put(label, loc, size, mat, folder=FOLDER, rot=None):
    a = EAS.spawn_actor_from_object(CUBE, V(*loc), rot or R())
    a.set_actor_label(label); a.set_folder_path(folder)
    a.set_actor_scale3d(V(size[0] / 100.0, size[1] / 100.0, size[2] / 100.0))
    a.static_mesh_component.set_material(0, mat)
    return a

# ---------------------------------------------------------------- the tram (same BP as the station)
AR = unreal.AssetRegistryHelpers.get_asset_registry()
bp = [x for x in AR.get_assets(unreal.ARFilter(package_paths=[TS], recursive_paths=True,
      class_paths=[unreal.TopLevelAssetPath("/Script/Engine", "Blueprint")])) if str(x.asset_name) == "BP_Tram"]
tram_cls = EAL.load_blueprint_class(str(bp[0].package_name))
START = V(-58000, -8000, 10)
tram = EAS.spawn_actor_from_class(tram_cls, START, R(y=0))
tram.set_actor_label("R_Tram"); tram.set_folder_path(FOLDER)
log("tram:", bp[0].package_name)

# cabin lights ride with the tram (out in the open sky the station lighting is gone)
for k, lx in enumerate((-650, 0, 650)):
    L = EAS.spawn_actor_from_class(unreal.PointLight, V(START.x + lx, START.y, START.z + 230), R())
    L.set_actor_label(f"R_TramCabinLight{k}"); L.set_folder_path(FOLDER)
    c = L.point_light_component
    c.set_mobility(unreal.ComponentMobility.MOVABLE)
    c.set_editor_property("intensity_units", unreal.LightUnits.CANDELAS)
    c.set_editor_property("intensity", 35.0)
    c.set_editor_property("attenuation_radius", 520.0)
    c.set_editor_property("cast_shadows", False)
    c.set_editor_property("light_color", unreal.Color(200, 235, 255, 255))
    L.attach_to_actor(tram, "", unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD, False)

# ---------------------------------------------------------------- the ride path
PTS = [(-58000, -8000), (-50000, -8000), (-44000, -6500), (-38000, 0), (-32000, 6000), (-26000, 7000),
       (-12000, 7000), (-5300, 7000), (-2800, 6330), (-970, 4500), (-300, 2000), (-300, 475)]
ride = EAS.spawn_actor_from_class(unreal.NVTramRide, V(0, 0, 0), R())
ride.set_actor_label("R_CrownLineRide"); ride.set_folder_path(FOLDER)
spl = ride.get_component_by_class(unreal.SplineComponent)
spl.clear_spline_points(False)
for (x, y) in PTS:
    spl.add_spline_point(V(x, y, 10), unreal.SplineCoordinateSpace.WORLD, False)
spl.update_spline()
log("path length %.0f cm" % spl.get_spline_length())
ride.set_editor_property("tram", tram)
ride.set_editor_property("start_speed", 1450.0)
ride.set_editor_property("decel_distance", 6500.0)
ride.set_editor_property("dock_door_side", 1.0)
ride.set_editor_property("rail_mesh", unreal.load_asset(f"{TS}/Meshes/SM_Monorail_A"))
ride.set_editor_property("rail_z", -210.0)
ride.set_editor_property("rail_segment", 800.0)
ride.set_editor_property("pylon_mesh", CUBE)
ride.set_editor_property("pylon_material", M_DARK)
ride.set_editor_property("pylon_spacing", 4000.0)
ride.set_editor_property("pylon_bottom_z", -20000.0)
ride.set_editor_property("pylon_skip_start", 4500.0)
ride.set_editor_property("pylon_skip_end", 2500.0)
ride.set_editor_property("ride_sound", unreal.load_asset("/Game/NeonVeil/Audio/SFX/SFX_Tram_RideLoop"))
ride.set_editor_property("dock_sound", unreal.load_asset("/Game/NeonVeil/Audio/SFX/SFX_Tram_Dock"))
ride.set_editor_property("door_sound", unreal.load_asset("/Game/NeonVeil/Audio/SFX/SFX_Tram_Dock"))
log("ride duration %.1f s" % ride.get_ride_duration())

# music: a driving track from the owned Cyber Punk Music pack (logged so it can be swapped)
tracks = sorted(str(x.package_name) for x in AR.get_assets(unreal.ARFilter(package_paths=["/Game/Cyber_Punk_Music_v11"],
                recursive_paths=True, class_paths=[unreal.TopLevelAssetPath("/Script/Engine", "SoundWave")])))
log("music candidates:", [t.split("/")[-1] for t in tracks])
pick = None
for pref in ("Action", "Drive", "Main", "Theme", "Background_2", "Background_1"):
    pick = next((t for t in tracks if pref.lower() in t.lower()), None)
    if pick:
        break
pick = pick or (tracks[0] if tracks else None)
if pick:
    ride.set_editor_property("music", unreal.load_asset(pick))
    ride.set_editor_property("music_volume", 0.75)
log("ride music:", pick)

# the Crown's ambient bed waits for the doors
for a in EAS.get_all_level_actors():
    if a.get_actor_label() == "MUS_CrownBed":
        a.audio_component.set_editor_property("auto_activate", False)
        ride.set_editor_property("bed_after_dock", a)
        log("bed after dock:", a.get_actor_label())

# ---------------------------------------------------------------- player starts inside the tram, facing the tunnel mouth
for a in EAS.get_all_level_actors():
    if a.get_actor_label() == "PlayerStart_TramExit":
        a.set_actor_location(V(START.x - 250, START.y + 60, 110), False, False)
        a.set_actor_rotation(R(y=0), False)
        log("player start moved into the tram")

# ---------------------------------------------------------------- transit spire the line bursts out of (tunnel bore)
X0, X1 = -64000.0, -54500.0
BY, BH = 450.0, (-260.0, 560.0)                 # bore half-width, bore z range
SY0, SY1 = -13000.0, -3000.0
cx, lx = (X0 + X1) / 2, X1 - X0
put("R_Spire_S", (cx, (SY0 + START.y - BY) / 2, -12000), (lx, (START.y - BY) - SY0, 36000), M_DARK)
put("R_Spire_N", (cx, (START.y + BY + SY1) / 2, -12000), (lx, SY1 - (START.y + BY), 36000), M_DARK)
put("R_Spire_Low", (cx, START.y, (-30000 + BH[0]) / 2), (lx, 2 * BY, BH[0] + 30000), M_DARK)
put("R_Spire_High", (cx, START.y, (BH[1] + 6000) / 2), (lx, 2 * BY, 6000 - BH[1]), M_DARK)
for k in range(9):                                           # tunnel light strips + facade bands
    put(f"R_Bore_Light{k}", (X0 + 600 + k * 1100, START.y, BH[1] - 6), (500, 120, 4), M_CYAN)
for k, z in enumerate(range(1000, 6000, 900)):
    put(f"R_Spire_Band{k}", (X1 + 6, (SY0 + SY1) / 2, z), (4, SY1 - SY0, 40), M_CYAN)
put("R_Portal_Top", (X1 + 8, START.y, BH[1] + 30), (4, 2 * BY + 120, 30), M_CYAN)
for side in (-1, 1):
    put(f"R_Portal_Side{side}", (X1 + 8, START.y + side * (BY + 45), (BH[0] + BH[1]) / 2 + 150), (4, 30, BH[1] - BH[0] - 300), M_CYAN)

# landing beam at the dock (the platform edge glow continues the rail)
put("R_DockRailCap", (-300, -900, -150), (120, 2800, 60), M_DARK)

LES.save_current_level()
open(unreal.Paths.project_saved_dir() + "NV_l1_crown_ride.txt", "w").write("\n".join(OUT))
