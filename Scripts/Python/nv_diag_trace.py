"""Diagnostic: visibility traces at each interactable from 140 cm in front (-X/-Y side) at eye height."""
import unreal
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
out = []
for a in EAS.get_all_level_actors():
    if not isinstance(a, unreal.NVInteractableActor):
        continue
    o, e = a.get_actor_bounds(False)
    hits = []
    for d in (unreal.Vector(-140, 0, 0), unreal.Vector(140, 0, 0), unreal.Vector(0, -140, 0), unreal.Vector(0, 140, 0)):
        start = unreal.Vector(o.x + d.x, o.y + d.y, o.z + 10)
        r = unreal.SystemLibrary.sphere_trace_single(world, start, o, 12.0, unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [], unreal.DrawDebugTrace.NONE, True)
        hit = r.to_tuple()[9].get_actor_label() if r and r.to_tuple()[9] else "none"
        hits.append(f"{int(d.x)},{int(d.y)}->{hit}")
    out.append(f"{a.get_actor_label():24s} size=({2*e.x:.0f},{2*e.y:.0f},{2*e.z:.0f}) " + " | ".join(hits))
open(unreal.Paths.project_saved_dir() + "NV_diag_trace.txt", "w").write("\n".join(out))
