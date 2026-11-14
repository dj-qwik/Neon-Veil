"""Trace from the editor viewport camera through a grid of screen directions; report what is hit. Report: Saved/NV_view_trace.txt"""
import unreal, math
UES = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
loc, rot = UES.get_level_viewport_camera_info()
world = UES.get_editor_world()
OUT = [f"cam {loc} {rot}"]
seen = {}
for dy in (-25, -12, 0, 12, 25):
    for dp in (-5, 5, 15, 25):
        r = unreal.Rotator(0, rot.pitch + dp, rot.yaw + dy)
        fwd = r.get_forward_vector()
        end = loc + fwd * 200000
        hit = unreal.SystemLibrary.line_trace_single(world, loc, end, unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [], unreal.DrawDebugTrace.NONE, True)
        if hit:
            t = hit.to_tuple()
            act, comp = t[9], t[10]
            mat = ""
            try:
                if comp and hasattr(comp, "get_material"):
                    m = comp.get_material(max(0, t[11] if isinstance(t[11], int) else 0))
                    mat = m.get_path_name() if m else ""
            except Exception as e:
                mat = str(e)
            key = (act.get_actor_label() if act else None, comp.get_name() if comp else None)
            OUT.append(f"dy={dy} dp={dp} -> {key} dist={t[3]:.0f} at {t[4]} sm={comp.static_mesh.get_name() if comp and hasattr(comp,'static_mesh') and comp.static_mesh else ''} mat={mat} folder={act.get_folder_path() if act else ''}")
open(unreal.Paths.project_saved_dir() + "NV_view_trace.txt", "w").write("\n".join(str(x) for x in OUT))
