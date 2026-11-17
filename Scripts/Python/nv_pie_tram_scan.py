"""PIE (prologue): bring the Crown Line tram in, board it, check it waits for the palm scanner, scan, check it departs.
Saved/NV_pie_tram_scan.txt, Saved/NV_shots/tram_scan_{0,1}.png"""
import os
import unreal
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
pc = unreal.GameplayStatics.get_player_controller(w, 0)
pawn = pc.get_controlled_pawn()
SHOTS = os.path.join(unreal.Paths.project_saved_dir(), "NV_shots")
svc = unreal.GameplayStatics.get_all_actors_of_class(w, unreal.NVTramService)[0]
tram = svc.get_editor_property("tram")
out = []
for i in range(1, 9):
    unreal.SystemLibrary.execute_console_command(w, "NVComplete M00P-O0%d" % i)
st = {"t": 0.0, "n": 0, "h": None, "scan": None}
def scanners():
    return [a for a in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.NVInteractableActor) if a.get_attach_parent_actor() == tram]
def shot(i):
    unreal.SystemLibrary.execute_console_command(w, 'HighResShot 1280x720 filename="%s"' % os.path.join(SHOTS, "tram_scan_%d.png" % i).replace("\\", "/"))
def tick(dt):
    st["t"] += dt
    t, n = st["t"], st["n"]
    tt = tram.get_actor_transform()
    if n == 0 and t > 16.0:
        sc = scanners()
        out.append("t%.0f tram %s scanners %d" % (t, tram.get_actor_location(), len(sc)))
        for s in sc:
            out.append("  scanner local %s prompt '%s' can=%s" % (tt.inverse_transform_location(s.get_actor_location()),
                       s.get_interaction_prompt(pawn), s.can_interact(pawn)))
        pawn.teleport(tt.transform_location(unreal.Vector(650, 0, 100)), unreal.Rotator(0, 0, tram.get_actor_rotation().yaw))
        pc.set_control_rotation(unreal.Rotator(roll=0, pitch=-12, yaw=tram.get_actor_rotation().yaw))
        st["n"] = 1
    elif n == 1 and t > 20.0:
        shot(0); st["n"] = 2
    elif n == 2 and t > 26.0:
        out.append("t%.0f aboard 6 s without scanning: tram %s" % (t, tram.get_actor_location()))
        sc = scanners()
        if sc:
            sc[0].interact(pawn)
            out.append("scanned")
        st["n"] = 3
    elif n == 3 and t > 33.0:
        out.append("t%.0f after scan: tram %s pawn %s" % (t, tram.get_actor_location(), pawn.get_actor_location()))
        shot(1)
        open(os.path.join(unreal.Paths.project_saved_dir(), "NV_pie_tram_scan.txt"), "w").write("\n".join(out))
        unreal.unregister_slate_post_tick_callback(st["h"])
st["h"] = unreal.register_slate_post_tick_callback(tick)
