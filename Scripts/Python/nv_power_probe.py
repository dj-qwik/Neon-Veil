"""Finds walls around the power panel and stair stub: traces in 8 directions. Report: Saved/NV_power_probe.txt"""
import math, unreal
w = unreal.EditorLevelLibrary.get_editor_world()
O = []
def probe(name, x, y, z):
    O.append(name)
    for yw in range(0, 360, 45):
        s = unreal.Vector(x, y, z)
        e = unreal.Vector(x + math.cos(math.radians(yw)) * 1500, y + math.sin(math.radians(yw)) * 1500, z)
        h = unreal.SystemLibrary.line_trace_single(w, s, e, unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [], unreal.DrawDebugTrace.NONE, True)
        if h:
            t = h.to_tuple()
            a = t[9]
            O.append(f"  yaw {yw}: {a.get_actor_label() if a else '?'} d {t[3]:.0f} at ({t[4].x:.0f},{t[4].y:.0f}) n ({t[7].x:.2f},{t[7].y:.2f})")
        else:
            O.append(f"  yaw {yw}: none")
probe("power panel", 650, -3050, 120)
for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
    lab = a.get_actor_label()
    if lab in ("I_PowerPanel", "G_Gate_North", "G_Gate_South", "Stair_Block_S_Edge", "Stair_Block_N_Edge") or lab.startswith("Stair_"):
        o, e = a.get_actor_bounds(False)
        O.append(f"{lab}: o({o.x:.0f},{o.y:.0f},{o.z:.0f}) e({e.x:.0f},{e.y:.0f},{e.z:.0f}) yaw {a.get_actor_rotation().yaw:.0f}")
# what is around the stub between the stairwells: sample floor heights along x at y -1420
for x in range(5000, 7000, 100):
    s = unreal.Vector(x, -1420, 1200); e = unreal.Vector(x, -1420, -200)
    h = unreal.SystemLibrary.line_trace_single(w, s, e, unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [], unreal.DrawDebugTrace.NONE, True)
    if h:
        t = h.to_tuple(); a = t[9]
        O.append(f"floor x {x}: z {t[4].z:.0f} {a.get_actor_label() if a else '?'}")
open(unreal.Paths.project_saved_dir() + "NV_power_probe.txt", "w").write("\n".join(O))
