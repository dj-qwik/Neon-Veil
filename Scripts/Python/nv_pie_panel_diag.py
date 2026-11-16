"""PIE: why can't the breaker be used? Saved/NV_pie_panel_diag.txt"""
import unreal
w = unreal.EditorLevelLibrary.get_game_world()
pawn = unreal.GameplayStatics.get_player_pawn(w, 0)
pc = unreal.GameplayStatics.get_player_controller(w, 0)
out = []
for p in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.NVBreakerPanel):
    out.append("panel %s label %s loc %s" % (p.get_name(), p.get_actor_label(), p.get_actor_location()))
    for k in ("enabled", "single_use", "required_active_objective", "completion_event_tag", "prompt"):
        try:
            out.append("  %s = %s" % (k, p.get_editor_property(k)))
        except Exception as e:
            out.append("  %s err %s" % (k, e))
    out.append("  used %s can_interact %s" % (p.has_been_used(), p.can_interact(pawn)))
    m = p.get_editor_property("mesh")
    out.append("  mesh %s coll %s profile %s visible %s bounds %s" % (m.get_name(), m.get_collision_enabled(), m.get_collision_profile_name(), m.is_visible(), m.get_world_location()))
    out.append("  root %s" % p.root_component.get_name())
    obj = unreal.NVObjectiveSubsystem.get(w) if hasattr(unreal.NVObjectiveSubsystem, "get") else None
    try:
        gi = unreal.GameplayStatics.get_game_instance(w)
        sub = gi.get_subsystem(unreal.NVObjectiveSubsystem)
        req = p.get_editor_property("required_active_objective")
        out.append("  objective %s active %s complete %s" % (req, sub.is_objective_active(req), sub.is_objective_complete(req)))
    except Exception as e:
        out.append("  objective err %s" % e)
cam = pc.player_camera_manager
loc = cam.get_camera_location(); rot = cam.get_camera_rotation()
end = loc + rot.get_forward_vector() * 400
hit = unreal.SystemLibrary.line_trace_single(w, loc, end, unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [pawn], unreal.DrawDebugTrace.NONE, True)
t = hit.to_tuple()
out.append("trace blocking=%s actor=%s comp=%s loc=%s" % (t[0], t[9].get_name() if t[9] else None, t[10].get_name() if t[10] else None, t[4]))
for p in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.NVBreakerPanel):
    tag = p.get_editor_property("completion_event_tag")
    out.append("tag name %r" % (tag.get_editor_property("tag_name"),))
ic = pawn.get_component_by_class(unreal.NVInteractionComponent)
out.append("ic range %s radius %s focus %s" % (ic.get_editor_property("interaction_range"), ic.get_editor_property("trace_radius"), ic.get_focused_actor()))
open(unreal.Paths.project_saved_dir() + "NV_pie_panel_diag.txt", "w").write("\n".join(out))
