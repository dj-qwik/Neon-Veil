"""L_M00_Prologue: find the cab-end hand-scanner pedestals of the tram held by NVTramService (traces from the cabin
centre toward both ends at a few heights). Saved/NV_tram_scanner_probe.txt"""
import unreal
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
out = []
try:
    svc = next(a for a in EAS.get_all_level_actors() if isinstance(a, unreal.NVTramService))
    tram = svc.get_editor_property("tram")
    tt = tram.get_actor_transform()
    out.append("service %s tram %s at %s rot %s" % (svc.get_actor_label(), tram.get_actor_label(), tram.get_actor_location(), tram.get_actor_rotation()))
    w = unreal.EditorLevelLibrary.get_editor_world()
    for sx in (1, -1):
        for z in (60, 90, 110, 130, 150, 170):
            for y in (-20, 0, 20):
                s = tt.transform_location(unreal.Vector(0, y, z))
                e = tt.transform_location(unreal.Vector(sx * 1200, y, z))
                hit = unreal.SystemLibrary.line_trace_single(w, s, e, unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [], unreal.DrawDebugTrace.NONE, True)
                if hit:
                    t = hit.to_tuple()
                    vec = [v for v in t if isinstance(v, unreal.Vector)][0]
                    comp = next((v for v in t if isinstance(v, unreal.PrimitiveComponent)), None)
                    loc = tt.inverse_transform_location(vec)
                    out.append("dir %+d z %d y %d -> local x %.1f y %.1f z %.1f comp %s" % (sx, z, y, loc.x, loc.y, loc.z, comp.get_name() if comp else None))
except Exception:
    import traceback; out.append(traceback.format_exc())
open(unreal.Paths.project_saved_dir() + "NV_tram_scanner_probe.txt", "w").write("\n".join(out))
