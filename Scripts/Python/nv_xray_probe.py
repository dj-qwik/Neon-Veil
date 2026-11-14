"""Which way does the X-ray arch open? For the machine at yaw 0, scan straight lines along X and along Y through it.
Report: Saved/NV_xray_probe.txt"""
import unreal
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
w = unreal.EditorLevelLibrary.get_editor_world()
V = unreal.Vector
xr = [a for a in EAS.get_all_level_actors() if a.get_actor_label() == "XRay_0"][0]
comp = xr.static_mesh_component
out = []
o, e = xr.get_actor_bounds(False)
out.append(f"yaw {xr.get_actor_rotation().yaw} o {o} e {e}")
def blocked(a, b):
    h = comp.line_trace_component(a, b, True, False, False)
    return bool(h[0]) if isinstance(h, tuple) else bool(h)
for z in (430, 480, 560, 640):
    row = ""
    x = o.x - e.x
    while x <= o.x + e.x:
        row += "#" if blocked(V(x, o.y - e.y - 50, z), V(x, o.y + e.y + 50, z)) else "."
        x += 8
    out.append(f"alongY z{z} x{o.x-e.x:.0f}.. {row}")
    row = ""
    y = o.y - e.y
    while y <= o.y + e.y:
        row += "#" if blocked(V(o.x - e.x - 50, y, z), V(o.x + e.x + 50, y, z)) else "."
        y += 8
    out.append(f"alongX z{z} y{o.y-e.y:.0f}.. {row}")
open(unreal.Paths.project_saved_dir() + "NV_xray_probe.txt", "w").write("\n".join(out))
