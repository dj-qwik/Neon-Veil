"""X-ray checkpoint: turn the machine so its walk-through arch faces down the concourse (the passage ran across the
hall and the luggage belt sat in front of the arch), then close the hall either side with glass security partitions
so the only way north is through the arch, and centre the scan trigger in the arch.
Run in the editor (prologue map). Report: Saved/NV_xray_fix.txt"""
import unreal
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
LES = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
w = unreal.EditorLevelLibrary.get_editor_world()
OBJ = [unreal.ObjectTypeQuery.OBJECT_TYPE_QUERY1, unreal.ObjectTypeQuery.OBJECT_TYPE_QUERY2]
V = unreal.Vector
OUT = []
def log(*a): OUT.append(" ".join(str(x) for x in a))
def find(l):
    for a in EAS.get_all_level_actors():
        if a.get_actor_label() == l:
            return a
FOLDER = "P_Concourse"
for a in list(EAS.get_all_level_actors()):
    if a.get_actor_label().startswith("XRay_Partition"):
        EAS.destroy_actor(a)
xr = find("XRay_0")
YAW = 0.0
xr.set_actor_rotation(unreal.Rotator(roll=0, pitch=0, yaw=YAW), False)
o, e = xr.get_actor_bounds(False)
log("machine bounds after turn", o, e)
comp = xr.static_mesh_component
def cblocked(a, b):
    h = comp.line_trace_component(a, b, True, False, False)
    return bool(h[0]) if isinstance(h, tuple) else bool(h)
def hit(a, b, ignore=()):
    h = unreal.SystemLibrary.line_trace_single(w, a, b, unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, list(ignore), unreal.DrawDebugTrace.NONE, True)
    return h.to_tuple() if h else None
# passable columns through the machine itself (component traces: no trigger volumes in the way)
y0, y1 = o.y - e.y - 60, o.y + e.y + 60
free = []
x = o.x - e.x - 40
while x <= o.x + e.x + 40:
    if not any(cblocked(V(x, y0, z), V(x, y1, z)) for z in (430, 480, 540, 580)):
        free.append(x)
    x += 5
runs, cur = [], []
for x in free:
    if cur and x - cur[-1] > 5.5:
        runs.append(cur); cur = []
    cur.append(x)
if cur: runs.append(cur)
runs = [(r[0], r[-1]) for r in runs]
log("free runs:", runs)
inner = [r for r in runs if r[0] > o.x - e.x + 20 and r[1] < o.x + e.x - 20]
gap = max(inner, key=lambda r: r[1] - r[0]) if inner else None
log("arch gap:", gap)
yc = o.y
# hall walls either side of the machine
west = hit(V(o.x, yc, 520), V(o.x - 3000, yc, 520), [xr])
east = hit(V(o.x, yc, 520), V(o.x + 3000, yc, 520), [xr])
wx = west[4].x if west else 6250.0
ex = max(east[4].x if east else 0.0, 7455.0)   # the east hall wall line is at x ~7460 (traces stop on fixtures first)
log("hall walls x:", wx, ex)
glass = None
try:
    glass = unreal.load_asset("/Game/SciFiTramStation/Meshes/SM_Tram_Glass").get_material(0)
except Exception:
    pass
cube = unreal.load_asset("/Engine/BasicShapes/Cube")
def partition(label, xa, xb):
    if xb - xa < 10:
        return
    a = EAS.spawn_actor_from_object(cube, V((xa + xb) / 2, yc, 400 + 120), unreal.Rotator())
    a.set_actor_scale3d(V((xb - xa) / 100.0, 0.06, 2.4))
    a.set_actor_label(label); a.set_folder_path(FOLDER); a.tags = [unreal.Name("NVP")]
    if glass:
        a.static_mesh_component.set_material(0, glass)
    log("partition", label, round(xa), round(xb))
if gap:
    gl, gr = gap
    partition("XRay_Partition_W", wx, o.x - e.x + 5)
    partition("XRay_Partition_E", o.x + e.x - 5, ex)
    t = find("T_XRayScan")
    if t:
        t.set_actor_location(V((gl + gr) / 2, yc, 520), False, False)
        t.get_editor_property("volume").set_box_extent(V(max(40, (gr - gl) / 2), e.y + 40, 150))
    s = find("XRay_Spot")
    if s:
        s.set_actor_location(V((gl + gr) / 2, yc, 780), False, False)
LES.save_current_level()
open(unreal.Paths.project_saved_dir() + "NV_xray_fix.txt", "w").write("\n".join(OUT))
