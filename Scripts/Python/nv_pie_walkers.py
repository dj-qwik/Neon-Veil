"""PIE: activate all sim targets, park Ghost in the suite looking down the lanes, and take two shots 3 s apart.
Writes Saved/NV_pie_walkers.txt (figure head height, anim, location) and Saved/NV_shots/pie_walk_{0,1}.png"""
import os
import unreal
SAVED = unreal.Paths.project_saved_dir()
SHOTS = os.path.join(SAVED, "NV_shots")
w = unreal.EditorLevelLibrary.get_game_world()
pc = unreal.GameplayStatics.get_player_controller(w, 0)
pawn = pc.get_controlled_pawn()
targets = list(unreal.GameplayStatics.get_all_actors_of_class(w, unreal.NVTrainingTarget))
for t in targets:
    t.activate()
pawn.teleport(unreal.Vector(7050, -700, 120), unreal.Rotator(0, 0, 0))
pc.set_control_rotation(unreal.Rotator(roll=0, pitch=-4, yaw=-12))
out = []
state = {"t": 0, "h": None, "n": 0}
def report(tag):
    for t in targets:
        f = next((c for c in t.get_components_by_class(unreal.SkeletalMeshComponent) if c.get_name() == "Figure"), None)
        if not f:
            continue
        head = f.get_socket_location("head") - t.get_actor_location()
        out.append("%s %s loc=%s headZ=%.1f figYaw=%.1f anim=%s" % (tag, t.get_actor_label(), t.get_actor_location(), head.z,
                   f.get_relative_rotation().yaw if hasattr(f, "get_relative_rotation") else f.get_editor_property("relative_rotation").yaw,
                   f.get_animation_mode()))
def tick(dt):
    state["t"] += dt
    if state["n"] == 0 and state["t"] > 2.5:
        unreal.SystemLibrary.execute_console_command(w, 'HighResShot 1280x720 filename="%s"' % os.path.join(SHOTS, "pie_walk_0.png").replace("\\", "/"))
        report("t2.5")
        state["n"] = 1
    elif state["n"] == 1 and state["t"] > 5.5:
        unreal.SystemLibrary.execute_console_command(w, 'HighResShot 1280x720 filename="%s"' % os.path.join(SHOTS, "pie_walk_1.png").replace("\\", "/"))
        report("t5.5")
        state["n"] = 2
    elif state["n"] == 2 and state["t"] > 6.5:
        open(os.path.join(SAVED, "NV_pie_walkers.txt"), "w").write("\n".join(out))
        unreal.unregister_slate_post_tick_callback(state["h"])
state["h"] = unreal.register_slate_post_tick_callback(tick)
