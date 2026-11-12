"""C00 tram (Bible C00 arrival), side approach: a subway car built from Dekogon City Subway Train Modular
(free Fab, local only) runs on rails ALONGSIDE the Glass Crown facade (along world Y), glides in over RIDE_S
seconds from DIST cm away and stops with a platform-side double door aligned to the entrance at world Y=0;
the two door leaves then slide open (NVTramArrival Doors/DoorOpenOffsets).
Car-local frame: X along the car (front 0 .. rear -1200), Y across (+150 = platform side), floor z 0.
World = (PIV.x + ly, PIV.y - lx), yaw = local - 90  (car front points -Y, car arrives from +Y).
Idempotent: removes previous T_* actors. Report: Saved/NV_tram_build.txt"""
import math
import unreal
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
V, R = unreal.Vector, unreal.Rotator
K = "/Game/SubwayTrain/"
FOLDER = "Tram"
PIV = (-213.0, -375.0)        # door bay centre (lx -375) lands on world Y 0; platform face at world X -40
DIST, RIDE_S = 10000.0, 18.0
MOV = unreal.ComponentMobility.MOVABLE
out = []

def W(lx, ly, lz=0.0):
    return V(PIV[0] + ly, PIV[1] - lx, lz)

def mesh(n):
    return unreal.load_asset(K + "Meshes/Structure/" + n)

def bpc(n):
    return unreal.load_asset(K + "Blueprints/" + n).generated_class()

root = None
def adopt(a, label):
    a.set_actor_label(label); a.set_folder_path(FOLDER)
    for c in a.get_components_by_class(unreal.SceneComponent):
        c.set_mobility(MOV)
    if root:
        a.attach_to_actor(root, "", unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD, False)
    return a

def put_mesh(label, m, lx, ly, lz=0.0, lyaw=0.0):
    a = EAS.spawn_actor_from_class(unreal.StaticMeshActor, W(lx, ly, lz), R(roll=0, pitch=0, yaw=lyaw - 90))
    a.static_mesh_component.set_mobility(MOV)
    a.static_mesh_component.set_static_mesh(m)
    return adopt(a, label)

def put_bp(label, cls, lx, ly, lz=0.0, lyaw=0.0):
    a = EAS.spawn_actor_from_class(cls, W(lx, ly, lz), R(roll=0, pitch=0, yaw=lyaw - 90))
    for d in a.get_components_by_class(unreal.DecalComponent):
        d.set_visibility(False)   # NYC signage/graffiti off: Directorate car
    return adopt(a, label)

# --- clean previous build + old box tram
for a in list(EAS.get_all_level_actors()):
    lab = a.get_actor_label()
    if lab.startswith("T_") or lab.startswith(("A_TramRoof", "A_TramSide", "A_TramRear", "A_TramWindow")):
        EAS.destroy_actor(a)

root = EAS.spawn_actor_from_class(unreal.StaticMeshActor, W(-600, 0, 0), R(yaw=-90))
root.static_mesh_component.set_mobility(MOV)
root.set_actor_label("T_Root"); root.set_folder_path(FOLDER)

for i in range(4):
    put_mesh("T_Floor%d" % i, mesh("SM_int_floor_300_01"), -300 * i, 150)
    put_mesh("T_FloorExt%d" % i, mesh("SM_ext_floor_300_01"), -300 * i, -150)

# side wall bays, front (lx 0) to rear (-1200). far = platform side (ly +150), near = city side (ly -150, yaw 180)
LAYOUT = [("BP_wall_100_01", 100), ("BP_Window_01", 200), ("DOOR", 150), ("BP_Window_01", 200),
          ("BP_Window_01", 200), ("BP_Door_double_01", 150), ("BP_Window_01", 200)]
doors, offsets = [], []
cur = 0.0
for i, (n, L) in enumerate(LAYOUT):
    if n == "DOOR":
        # platform-side exit: open frame + two movable leaves (kit BP layout: leaf01 at 0, leaf02 at -149)
        f = put_mesh("T_ExitFrame", mesh("SM_wall_doorway_01"), cur, 150)
        f.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
        doors.append(put_mesh("T_ExitLeafA", mesh("SM_door_wall_01"), cur, 151))
        offsets.append(V(0, -76, 0))     # local +X 76 -> world -Y
        doors.append(put_mesh("T_ExitLeafB", mesh("SM_door_wall_02"), cur - 149, 151))
        offsets.append(V(0, 76, 0))
        put_bp("T_WallNear%d" % i, bpc("BP_Door_double_01"), cur - L, -150, 0, 180)
    else:
        put_bp("T_WallFar%d" % i, bpc(n), cur, 150)
        put_bp("T_WallNear%d" % i, bpc(n), cur - L, -150, 0, 180)
    cur -= L
assert abs(cur + 1200) < 1

# ends (closed)
put_mesh("T_EndIntFront", mesh("SM_int_wall_end_01"), 0, -150, 0, -90)
put_mesh("T_EndIntRear", mesh("SM_int_wall_end_01"), -1200, 150, 0, 90)
put_bp("T_EndExtFront", bpc("BP_Train_ext_end_01"), 0, -150)
put_bp("T_EndExtRear", bpc("BP_Train_ext_end_01"), -1200, 150, 0, 180)
put_mesh("T_DoorFront", mesh("SM_door_end_01"), 12, -49.5, 0, -90)
put_mesh("T_DoorRear", mesh("SM_door_end_01"), -1212, 49.5, 0, 90)

# seats under window bays + poles at the side doors
BAYS = [(-300, -100), (-650, -450), (-850, -650), (-1200, -1000)]
for b, (lo, hi) in enumerate(BAYS):
    for k in range(4):
        chair = mesh("SM_chair_01a" if k in (1, 2) else "SM_chair_01b")
        put_mesh("T_SeatFar%d_%d" % (b, k), chair, hi - 50 * k, 138)
        put_mesh("T_SeatNear%d_%d" % (b, k), chair, lo + 50 * k, -138, 0, 180)
for j, x in enumerate((-375, -925)):
    for side, y in (("F", 95), ("N", -95)):
        if j == 0 and side == "F":
            continue   # keep the exit doorway clear
        put_mesh("T_Pole%s%d" % (side, j), mesh("SM_pole_01"), x, y)

# ceiling, light strip, roof
for i in range(4):
    put_mesh("T_CeilFar%d" % i, mesh("SM_int_ceiling_300_01"), -300 * i, 138, 250)
    put_mesh("T_CeilNear%d" % i, mesh("SM_int_ceiling_300_01"), -300 * (i + 1), -138, 250, 180)
for i in range(10):
    put_mesh("T_LightStrip%d" % i, mesh("SM_overheadlight_01"), -125 * i, 0, 250)
for i in range(6):
    put_mesh("T_Roof%d" % i, mesh("SM_ext_roof_200_01"), -1200 + 200 * i, -150)

# underbody + bogies (wheels on rails at local y +/-115)
for i in range(5):
    put_mesh("T_Under%d" % i, mesh("SM_underbody_01"), -1200 + 35 + 226 * i, 0, -75)
BOG_Z = -148.0
for j, x in enumerate((-1200 + 60, -60 - 333)):
    put_mesh("T_BogieA%d" % j, mesh("SM_underbody_bogie_01"), x, 115, BOG_Z)
    put_mesh("T_BogieB%d" % j, mesh("SM_underbody_bogie_01"), x, -110, BOG_Z)

# --- level fixtures: platform lip, cabin light, rails/pylons along Y, player start, arrival actor
RAIL_Y0, RAIL_Y1 = -4000.0, DIST + 4000.0
for a in EAS.get_all_level_actors():
    lab = a.get_actor_label()
    if lab == "A_TramFloor":           # threshold plate between car and entrance
        a.set_actor_location(V(-22, 0, -20), False, False)
        a.set_actor_rotation(R(), False)
        a.set_actor_scale3d(V(0.45, 3.2, 0.4))
    elif lab == "A_TramLight":
        for c in a.get_components_by_class(unreal.SceneComponent):
            c.set_mobility(MOV)
        a.set_actor_location(W(-600, 0, 225), False, False)
        a.attach_to_actor(root, "", unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD, False)
    elif lab in ("C00_Rail_L", "C00_Rail_R", "C00_RailGlow_L", "C00_RailGlow_R"):
        ly = 115.0 if lab.endswith("R") else -115.0
        z = BOG_Z - 25.0 if "Glow" not in lab else BOG_Z + 2.0
        s = a.get_actor_scale3d()
        a.set_actor_rotation(R(yaw=90), False)
        a.set_actor_location(V(PIV[0] + ly, (RAIL_Y0 + RAIL_Y1) / 2.0, z), False, False)
        a.set_actor_scale3d(V((RAIL_Y1 - RAIL_Y0) / 100.0, s.y, s.z))
    elif lab.startswith("C00_Pylon"):
        k = int(lab[len("C00_Pylon"):])
        a.set_actor_rotation(R(yaw=90), False)
        a.set_actor_location(V(PIV[0], -1500.0 + 2000.0 * k, -2700.0), False, False)
    elif lab == "PlayerStart_TramExit":
        # NVTramArrival parks the car DIST out along +Y at BeginPlay, before the pawn spawns: start inside it there
        a.set_actor_location(W(-520, 20, 100) + V(0, DIST, 0), False, False)
        a.set_actor_rotation(R(yaw=0), False)          # facing the platform-side windows / exit door
    elif lab == "C00_TramArrival":
        a.set_actor_location(W(-600, 0, 100), False, False)
        a.set_actor_rotation(R(yaw=-90), False)        # forward = travel direction (-Y)
        a.set_editor_property("parts", [root])
        a.set_editor_property("doors", doors)
        a.set_editor_property("door_open_offsets", offsets)
        a.set_editor_property("distance", DIST)
        a.set_editor_property("duration", RIDE_S)
        a.set_editor_property("door_delay", 1.2)
        a.set_editor_property("door_open_time", 1.4)
        a.set_editor_property("cabin_extent", V(650, 190, 250))
        rs = unreal.load_asset("/Game/NeonVeil/Audio/SFX/SFX_Tram_RideLoop")
        a.set_editor_property("ride_sound", rs)
        a.set_editor_property("door_sound", unreal.load_asset("/Game/NeonVeil/Audio/SFX/SFX_Tram_Dock"))
        out.append("arrival: dist %.0f over %.0fs, doors %d, ride sound %s" % (DIST, RIDE_S, len(doors), bool(rs)))

# --- what else sits in the tram's path (car body sweep from far end to stop)?
x0, x1 = PIV[0] - 190, PIV[0] + 190
for a in EAS.get_all_level_actors():
    lab = a.get_actor_label()
    if lab.startswith(("T_", "C00_", "A_TramFloor", "A_TramLight", "PlayerStart", "Rain", "FX")) or a.get_attach_parent_actor():
        continue
    o, e = a.get_actor_bounds(False)
    if e.x > 20000 or e.y > 20000:
        continue
    if o.x + e.x > x0 and o.x - e.x < x1 and o.y + e.y > -375 and o.y - e.y < 825 + DIST and o.z + e.z > -160 and o.z - e.z < 300:
        out.append("IN PATH: %s (%s) c(%.0f,%.0f,%.0f) e(%.0f,%.0f,%.0f)" % (lab, a.get_class().get_name(), o.x, o.y, o.z, e.x, e.y, e.z))

unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
out.append("tram actors %d" % sum(1 for a in EAS.get_all_level_actors() if a.get_actor_label().startswith("T_")))
open(unreal.Paths.project_saved_dir() + "NV_tram_build.txt", "w").write("\n".join(out))
