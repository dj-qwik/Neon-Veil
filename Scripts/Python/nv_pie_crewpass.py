"""PIE: fast-forward the prologue to the crew-pass objective, stand Ghost where a player would, aim at the Station Ops
terminal and report what the interaction component focuses. Saved/NV_pie_crewpass.txt, Saved/NV_shots/crewpass_*.png"""
import os
import unreal
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
pc = unreal.GameplayStatics.get_player_controller(w, 0)
pawn = pc.get_controlled_pawn()

out = []
cp = [a for a in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.NVInteractableActor) if a.get_actor_label() == "I_CrewPass"][0]
cp.set_editor_property("required_active_objective", "")   # test only: skip the objective gate in this PIE session
out.append("crew pass mesh %s" % cp.get_editor_property("mesh").static_mesh.get_name())
ic = pawn.get_component_by_class(unreal.NVInteractionComponent)
SPOTS = [("south", (6760, 4560)), ("east", (6890, 4600)), ("crate", (6900, 4660))]
st = {"i": 0, "t": 0.0, "h": None, "ph": 0}
def tick(dt):
    st["t"] += dt
    if st["i"] >= len(SPOTS):
        open(os.path.join(unreal.Paths.project_saved_dir(), "NV_pie_crewpass.txt"), "w").write("\n".join(out))
        unreal.unregister_slate_post_tick_callback(st["h"])
        return
    nm, xy = SPOTS[st["i"]]
    if st["ph"] == 0:
        pawn.set_actor_location(unreal.Vector(xy[0], xy[1], 500), False, True)
        st["ph"], st["t"] = 1, 0.0
        return
    eye = pc.player_camera_manager.get_camera_location()
    pc.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(eye, cp.get_actor_location() + unreal.Vector(0, 0, 90)))
    if st["ph"] == 1 and st["t"] > 0.6:
        f = ic.get_focused_actor() if ic else None
        out.append("%s pawn %s eye %s focus=%s can=%s" % (nm, pawn.get_actor_location(), eye, f.get_actor_label() if f else None,
                                                        cp.can_interact(pawn) if hasattr(cp, "can_interact") else "?"))
        unreal.SystemLibrary.execute_console_command(w, 'HighResShot 960x540 filename="%s"' % os.path.join(unreal.Paths.project_saved_dir(), "NV_shots", "crewpass_%s.png" % nm).replace("\\", "/"))
        st["ph"], st["t"] = 2, 0.0
    elif st["ph"] == 2 and st["t"] > 0.4:
        st["ph"] = 0; st["i"] += 1
st["h"] = unreal.register_slate_post_tick_callback(tick)
