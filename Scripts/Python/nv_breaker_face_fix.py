"""Platform Two breaker box: the painted face plane (Breaker_Face) sat 1.3 cm in front of the interactable housing with
BlockAll collision, so the use-trace stopped on the plane and the prompt never showed. Make every Breaker_* dressing
piece non-colliding, then check a use-trace from 1.2 m in front reaches the NVBreakerPanel. Report: Saved/NV_breaker_face_fix.txt"""
import unreal
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
out = []
for a in EAS.get_all_level_actors():
    if a.get_actor_label().startswith("Breaker_"):
        for c in a.get_components_by_class(unreal.PrimitiveComponent):
            if c.get_collision_profile_name() != "NoCollision":
                c.modify()
                c.set_collision_profile_name("NoCollision")
                out.append("no collision: %s (%s)" % (a.get_actor_label(), c.get_name()))
pan = unreal.GameplayStatics.get_all_actors_of_class(w, unreal.NVBreakerPanel)[0]
T = pan.get_actor_transform()
for z in (120, 140, 165):
    s = T.transform_location(unreal.Vector(120, 0, 165)); e = T.transform_location(unreal.Vector(0, 0, z))
    hit = unreal.SystemLibrary.sphere_trace_single(w, s, e, 12.0, unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [], unreal.DrawDebugTrace.NONE, True)
    t = hit.to_tuple() if hit else None
    out.append("use-trace to z%d hits %s" % (z, t[9].get_actor_label() if t and t[9] else None))
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
open(unreal.Paths.project_saved_dir() + "NV_breaker_face_fix.txt", "w").write("\n".join(out))
