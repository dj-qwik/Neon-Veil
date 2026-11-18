"""PIE diagnostic: stand in front of the M01 agency tag, trace from the camera to it, log what is hit."""
import os
import unreal
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
pc = unreal.GameplayStatics.get_player_controller(w, 0)
p = pc.get_controlled_pawn()
tag = [a for a in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.NVInteractableActor) if a.get_actor_label() == "D_AgencyTag"][0]
p.teleport(unreal.Vector(17150, 7000, -4400), unreal.Rotator(0, 0, 0))
out = []
st = {"n": 0, "h": None}
def tick(dt):
    st["n"] += 1
    if st["n"] == 5:
        cam = pc.player_camera_manager.get_camera_location()
        r = unreal.MathLibrary.find_look_at_rotation(cam, tag.get_actor_location())
        pc.set_control_rotation(r)
        hit = unreal.SystemLibrary.line_trace_single(w, cam, tag.get_actor_location() + (tag.get_actor_location() - cam) * 0.2,
                                                     unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [p], unreal.DrawDebugTrace.NONE, True)
        out.append("cam %s tag %s bounds %s" % (cam, tag.get_actor_location(), tag.get_actor_bounds(False)))
        out.append("hit: %s" % (hit.to_tuple()[9] if hit else None))
        out.append("blocking=%s actor=%s comp=%s" % (hit.to_tuple()[0], hit.to_tuple()[9], hit.to_tuple()[10]))
        open(os.path.join(unreal.Paths.project_saved_dir(), "NV_pie_tagtrace.txt"), "w").write("\n".join(str(x) for x in out))
        unreal.unregister_slate_post_tick_callback(st["h"])
st["h"] = unreal.register_slate_post_tick_callback(tick)
