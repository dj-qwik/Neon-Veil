"""PIE: replay the M01 reclamation from the shaft-bottom checkpoint, then try to take the agency tag."""
import os
import unreal
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
pc = unreal.GameplayStatics.get_player_controller(w, 0)
p = pc.get_controlled_pawn()
tag = [a for a in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.NVInteractableActor) if a.get_actor_label() == "D_AgencyTag"][0]
inter = p.get_component_by_class(unreal.NVInteractionComponent)
out = []
st = {"t": 0.0, "i": 0, "h": None}
def look():
    cam = pc.player_camera_manager.get_camera_location()
    pc.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(cam, tag.get_actor_location()))
def focus(label):
    f = inter.get_focused_actor()
    out.append("%s: focus=%s" % (label, f.get_name() if f else None))
STEPS = [
    (0.5, lambda: p.teleport(unreal.Vector(16650, 7000, -4400), unreal.Rotator(0, 0, 0))),
    (21.0, lambda: (p.teleport(unreal.Vector(17150, 7000, -4400), unreal.Rotator(0, 0, 0)), look())),
    (22.0, lambda: (look(), focus("before use"))),
    (22.5, lambda: unreal.SystemLibrary.execute_console_command(w, "NVUse", pc)),
    (24.0, lambda: focus("after use")),
]
def tick(dt):
    st["t"] += dt
    while st["i"] < len(STEPS) and st["t"] >= STEPS[st["i"]][0]:
        STEPS[st["i"]][1]()
        st["i"] += 1
    if st["i"] >= len(STEPS):
        open(os.path.join(unreal.Paths.project_saved_dir(), "NV_pie_tagtest.txt"), "w").write("\n".join(out))
        unreal.unregister_slate_post_tick_callback(st["h"])
st["h"] = unreal.register_slate_post_tick_callback(tick)
