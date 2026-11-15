"""Lists actors whose bounds contain the point. args: x y z"""
import sys, unreal
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
x, y, z = [float(v) for v in sys.argv[2:5]]
O = []
for a in EAS.get_all_level_actors():
    try:
        o, e = a.get_actor_bounds(False)
    except Exception:
        continue
    if e.x > 50000 or e.y > 50000:
        continue
    if abs(x - o.x) <= e.x and abs(y - o.y) <= e.y and abs(z - o.z) <= e.z:
        hidden = a.is_hidden_ed()
        O.append(f"{a.get_actor_label()} [{a.get_class().get_name()}] o({o.x:.0f},{o.y:.0f},{o.z:.0f}) e({e.x:.0f},{e.y:.0f},{e.z:.0f}) hiddenEd {hidden} folder {a.get_folder_path()}")
open(unreal.Paths.project_saved_dir() + "NV_point_probe.txt", "w").write("\n".join(O))
