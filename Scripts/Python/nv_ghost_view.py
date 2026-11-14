"""Point the (ejected, F8) PIE viewport camera at Ghost-7. Args: [angle_deg relative to his facing: 0=front, 90=his right]
[distance cm] [height cm above capsule centre]. Report: Saved/NV_ghost_view.txt"""
import unreal, sys, math
args = sys.argv[2:]
ang = float(args[0]) if len(args) > 0 else 90.0
dist = float(args[1]) if len(args) > 1 else 220.0
h = float(args[2]) if len(args) > 2 else 40.0
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
world = ues.get_game_world()
OUT = []
p = None
if world:
    for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.NVPlayerCharacter):
        p = a
        break
if p:
    loc = p.get_actor_location()
    yaw = p.get_actor_rotation().yaw + ang
    r = math.radians(yaw)
    cam = unreal.Vector(loc.x + math.cos(r) * dist, loc.y + math.sin(r) * dist, loc.z + h)
    rot = unreal.MathLibrary.find_look_at_rotation(cam, unreal.Vector(loc.x, loc.y, loc.z + 30))
    ues.set_level_viewport_camera_info(cam, rot)
    OUT.append(f"player {loc} yaw {p.get_actor_rotation().yaw:.1f} cam {cam} rot {rot}")
else:
    OUT.append("no player")
open(unreal.Paths.project_saved_dir() + "NV_ghost_view.txt", "w").write("\n".join(str(x) for x in OUT))
