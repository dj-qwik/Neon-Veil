"""C00: replace the box tram with a car assembled from Dekogon City Subway Train Modular (free Fab, local only).
Car interior X [XR..XF], Y [-150..150], floor z 0. Front (+X) end door is the exit door driven by C00_TramArrival.
Idempotent: removes previous T_* actors. Report: Saved/NV_tram_build.txt"""
import unreal
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
V, R = unreal.Vector, unreal.Rotator
K = "/Game/SubwayTrain/"
XF, XR = -100.0, -1300.0
FOLDER = "Tram"
out = []

def mesh(n):
    return unreal.load_asset(K + "Meshes/Structure/" + n)

def bpc(n):
    return unreal.load_asset(K + "Blueprints/" + n).generated_class()

def put_mesh(label, m, loc, yaw=0.0, movable=False):
    a = EAS.spawn_actor_from_class(unreal.StaticMeshActor, V(*loc), R(roll=0, pitch=0, yaw=yaw))
    c = a.static_mesh_component
    c.set_mobility(unreal.ComponentMobility.MOVABLE if movable else unreal.ComponentMobility.STATIC)
    c.set_static_mesh(m)
    a.set_actor_label(label); a.set_folder_path(FOLDER)
    return a

def put_bp(label, cls, loc, yaw=0.0):
    a = EAS.spawn_actor_from_class(cls, V(*loc), R(roll=0, pitch=0, yaw=yaw))
    a.set_actor_label(label); a.set_folder_path(FOLDER)
    for d in a.get_components_by_class(unreal.DecalComponent):
        d.set_visibility(False)   # NYC signage/graffiti off: Directorate car
    return a

# --- clean up previous build + old box tram
for a in list(EAS.get_all_level_actors()):
    lab = a.get_actor_label()
    if lab.startswith("T_") or lab.startswith(("A_TramRoof", "A_TramSide", "A_TramRear", "A_TramWindow")):
        EAS.destroy_actor(a)

# --- floor (interior + underside)
for i in range(4):
    x = XF - 300 * i
    put_mesh("T_Floor%d" % i, mesh("SM_int_floor_300_01"), (x, 150, 0))
    put_mesh("T_FloorExt%d" % i, mesh("SM_ext_floor_300_01"), (x, -150, 0))

# --- side walls, front to back. far side (Y=+150) unrotated, near side (Y=-150) yaw 180
LAYOUT = [("BP_wall_100_01", 100), ("BP_Window_01", 200), ("BP_Door_double_01", 150), ("BP_Window_01", 200),
          ("BP_Window_01", 200), ("BP_Door_double_01", 150), ("BP_Window_01", 200)]
assert sum(l for _, l in LAYOUT) == XF - XR
cur = XF
for i, (n, L) in enumerate(LAYOUT):
    put_bp("T_WallFar%d" % i, bpc(n), (cur, 150, 0), 0)
    put_bp("T_WallNear%d" % i, bpc(n), (cur - L, -150, 0), 180)
    cur -= L

# --- ends: interior end wall + exterior end shell. front faces +X (yaw -90), rear faces -X (yaw 90)
put_mesh("T_EndIntFront", mesh("SM_int_wall_end_01"), (XF, -150, 0), -90)
put_mesh("T_EndIntRear", mesh("SM_int_wall_end_01"), (XR, 150, 0), 90)
put_bp("T_EndExtFront", bpc("BP_Train_ext_end_01"), (XF, -150, 0), 0)
put_bp("T_EndExtRear", bpc("BP_Train_ext_end_01"), (XR, 150, 0), 180)
door = put_mesh("T_DoorFront", mesh("SM_door_end_01"), (XF + 12, -49.5, 0), -90, movable=True)
put_mesh("T_DoorRear", mesh("SM_door_end_01"), (XR - 12, 49.5, 0), 90)

# --- bench seats under each window bay (4 x 50 cm) + grab poles at the side doors
BAYS = [(-400, -200), (-750, -550), (-950, -750), (-1300, -1100)]
for b, (lo, hi) in enumerate(BAYS):
    for k in range(4):
        chair = mesh("SM_chair_01a" if k in (1, 2) else "SM_chair_01b")
        put_mesh("T_SeatFar%d_%d" % (b, k), chair, (hi - 50 * k, 138, 0))
        put_mesh("T_SeatNear%d_%d" % (b, k), chair, (lo + 50 * k, -138, 0), 180)
for j, x in enumerate((-475, -1025)):
    for side, y in (("F", 95), ("N", -95)):
        put_mesh("T_Pole%s%d" % (side, j), mesh("SM_pole_01"), (x, y, 0))

# --- ceiling halves, centre light strip, roof
for i in range(4):
    x = XF - 300 * i
    put_mesh("T_CeilFar%d" % i, mesh("SM_int_ceiling_300_01"), (x, 138, 250))
    put_mesh("T_CeilNear%d" % i, mesh("SM_int_ceiling_300_01"), (x - 300, -138, 250), 180)
for i in range(10):
    put_mesh("T_LightStrip%d" % i, mesh("SM_overheadlight_01"), (XF - 125 * i, 0, 250))
for i in range(6):
    put_mesh("T_Roof%d" % i, mesh("SM_ext_roof_200_01"), (XR + 200 * i, -150, 0))

# --- underbody + bogies (wheels on rails at y +/-115)
for i in range(5):
    put_mesh("T_Under%d" % i, mesh("SM_underbody_01"), (XR + 35 + 226 * i, 0, -75))
BOG_Z = -148.0
for j, x in enumerate((XR + 60, XF - 60 - 333)):
    put_mesh("T_BogieA%d" % j, mesh("SM_underbody_bogie_01"), (x, 115, BOG_Z))
    put_mesh("T_BogieB%d" % j, mesh("SM_underbody_bogie_01"), (x, -110, BOG_Z))

# --- old floor box becomes the threshold lip between car and bridge; light drops under the new ceiling
for a in EAS.get_all_level_actors():
    lab = a.get_actor_label()
    if lab == "A_TramFloor":
        a.set_actor_location(V(-30, 0, -20), False, False)
        a.set_actor_scale3d(V(0.6, 3.2, 0.4))   # 60 x 320 x 40 cm (engine cube)
    elif lab == "A_TramLight":
        a.set_actor_location(V(-700, 0, 225), False, False)
    elif lab in ("C00_Rail_L", "C00_Rail_R", "C00_RailGlow_L", "C00_RailGlow_R"):
        l = a.get_actor_location()
        y = 115.0 if lab.endswith("R") else -115.0
        z = BOG_Z - 25.0 if "Glow" not in lab else BOG_Z + 2.0
        a.set_actor_location(V(l.x, y, z), False, False)
    elif lab.startswith("C00_Pylon"):
        l = a.get_actor_location()
        a.set_actor_location(V(l.x, l.y, -2700.0), False, False)   # top at -200, under the lowered rails
    elif lab == "C00_TramArrival":
        a.set_editor_property("parts", [])
        a.set_editor_property("door", door)
        a.set_editor_property("door_open_offset", V(0, 92, 0))
        out.append("tram arrival door set")

unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
n = sum(1 for a in EAS.get_all_level_actors() if a.get_actor_label().startswith("T_"))
out.append("tram actors %d" % n)
open(unreal.Paths.project_saved_dir() + "NV_tram_build.txt", "w").write("\n".join(out))
