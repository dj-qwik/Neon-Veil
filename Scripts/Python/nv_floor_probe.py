"""Trace down at citizen spawn/route points to find floors. Report: Saved/NV_floor.txt"""
import unreal
UES = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
w = UES.get_game_world() or UES.get_editor_world()
pts = {"Cn1a": (8250, -2800, 400), "Cn1b": (8200, 4500, 400), "Cn2a": (7700, 4400, 400), "Cn2b": (7650, -2600, 400),
       "Cn3": (7250, 2300, 400), "Cn4a": (8000, 3200, 400), "Cn4b": (7000, 3900, 400), "Cn4c": (8200, 4700, 400),
       "mid": (7600, 0, 400), "Pf1": (1200, -1400, 120), "Pf1b": (2600, -1500, 120), "Pf2": (4300, -1700, 120), "Pf2b": (3200, -1600, 120)}
out = []
for k, (x, y, z) in pts.items():
    hit = unreal.SystemLibrary.line_trace_single(w, unreal.Vector(x, y, z + 800), unreal.Vector(x, y, z - 3000),
                                                 unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [], unreal.DrawDebugTrace.NONE, True)
    if hit:
        t = hit.to_tuple()
        out.append(f"{k} hitz={t[4].z:.0f} actor={t[9].get_actor_label() if t[9] else None}")
    else:
        out.append(f"{k} no hit")
open(unreal.Paths.project_saved_dir() + "NV_floor.txt", "w").write("\n".join(out))
