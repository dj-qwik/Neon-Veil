import unreal
w = unreal.EditorLevelLibrary.get_pie_worlds(False)[0]
O = []
for dy in (0, 100, 200, 300, 370, 450, 600):
    s = unreal.Vector(7046, -15800 + dy, -11700); e = unreal.Vector(7046, -15800 + dy, -12300)
    hits = unreal.SystemLibrary.line_trace_multi(w, s, e, unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [], unreal.DrawDebugTrace.NONE, True) or []
    O.append(f"dy {dy}: " + ", ".join(f"{(h.to_tuple()[9].get_actor_label() if h.to_tuple()[9] else '?')}@{h.to_tuple()[4].z:.1f}" for h in hits[:4]))
open(unreal.Paths.project_saved_dir() + "NV_floor_probe.txt", "w").write("\n".join(O))
