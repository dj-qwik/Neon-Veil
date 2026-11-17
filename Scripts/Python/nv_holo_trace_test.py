"""Editor line traces (Visibility, complex) from the player side at each holo target: head height and chest height."""
import unreal
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
W = unreal.EditorLevelLibrary.get_editor_world()
out = []
def run():
  for a in EAS.get_all_level_actors():
      lbl = a.get_actor_label()
      if not lbl.startswith("C_Target_") or lbl == "C_Target_Drone":
          continue
      c = {x.get_name(): x for x in a.get_components_by_class(unreal.SceneComponent)}
      head = c["WeakPoint"].get_world_location()
      for name, z in (("head", head.z), ("chest", 110.0)):
          tgt = unreal.Vector(head.x, head.y, z) if name == "head" else a.get_actor_location() + unreal.Vector(0, 0, z)
          start = tgt + a.get_actor_forward_vector() * 600.0
          hit = unreal.SystemLibrary.line_trace_single(W, start, tgt - a.get_actor_forward_vector() * 100.0,
                                                       unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [], unreal.DrawDebugTrace.NONE, True)
          if hit:
              b = hit.to_tuple()
              comp = next((x for x in b if isinstance(x, unreal.PrimitiveComponent)), None)
              act = comp.get_owner() if comp else None
              out.append("%s %s -> %s / %s weak=%s" % (lbl, name, act.get_actor_label() if act else None,
                         comp.get_name() if comp else None, comp.component_has_tag("WeakPoint") if comp else None))
          else:
              out.append("%s %s -> no hit" % (lbl, name))
try:
    run()
except Exception as e:
    import traceback; out.append(traceback.format_exc())
open(unreal.Paths.project_saved_dir() + "NV_holo_trace_test.txt", "w").write("\n".join(out))
