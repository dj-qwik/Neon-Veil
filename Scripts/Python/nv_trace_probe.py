"""Line traces from a point in several yaw directions; reports first hits. args: x y z [yaw...]"""
import sys, math, unreal
x, y, z = [float(v) for v in sys.argv[2:5]]
yaws = [float(v) for v in sys.argv[5:]] or [0, 20, 40, -20, -40, 60, -60]
w = unreal.EditorLevelLibrary.get_editor_world()
O = []
for zz in (z, z + 3000, z - 3000, z + 6000):
    for yw in yaws:
        s = unreal.Vector(x, y, zz)
        e = unreal.Vector(x + math.cos(math.radians(yw)) * 60000, y + math.sin(math.radians(yw)) * 60000, zz)
        hits = unreal.SystemLibrary.line_trace_multi(w, s, e, unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [], unreal.DrawDebugTrace.NONE, True)
        hs = []
        for h in (hits or [])[:4]:
            t = h.to_tuple()
            a = t[9] if len(t) > 9 else None
            hs.append(f"{a.get_actor_label() if a else '?'}@{t[3]:.0f}")
        O.append(f"z {zz:.0f} yaw {yw:.0f}: " + ", ".join(hs))
open(unreal.Paths.project_saved_dir() + "NV_trace_probe.txt", "w").write("\n".join(O))
