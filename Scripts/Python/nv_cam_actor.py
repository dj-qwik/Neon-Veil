"""Point the (ejected PIE) viewport camera at an actor in the PIE world. args: label [dist] [angle_deg] [height] [z_aim]"""
import sys, math, unreal
UES = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
lab = sys.argv[2]; dist = float(sys.argv[3]) if len(sys.argv) > 3 else 220
ang = float(sys.argv[4]) if len(sys.argv) > 4 else 0; h = float(sys.argv[5]) if len(sys.argv) > 5 else 40
aimz = float(sys.argv[6]) if len(sys.argv) > 6 else 20
pie = unreal.EditorLevelLibrary.get_pie_worlds(False) if hasattr(unreal.EditorLevelLibrary, "get_pie_worlds") else []
w = (pie[0] if pie else None) or UES.get_game_world() or UES.get_editor_world()
rep = [f"world {w.get_path_name()} pie {len(pie)}"]
for a in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.Actor):
    if a.get_actor_label() == lab:
        l = a.get_actor_location(); yaw = a.get_actor_rotation().yaw + ang
        c = unreal.Vector(l.x + math.cos(math.radians(yaw)) * dist, l.y + math.sin(math.radians(yaw)) * dist, l.z + h)
        d = unreal.Vector(l.x - c.x, l.y - c.y, l.z + aimz - c.z)
        rot = unreal.MathLibrary.make_rot_from_x(d)
        UES.set_level_viewport_camera_info(c, rot)
        rep.append(f'{lab} at {l} cam {c}')
        break
open(unreal.Paths.project_saved_dir() + 'NV_cam_actor.txt', 'w').write(chr(10).join(rep))
