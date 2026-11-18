"""PIE: track every character for ~25 s and log where they end up (catches anything falling through floors).
Saved/NV_pie_npcs.txt"""
import os
import unreal
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
out = []
st = {"t": 0.0, "h": None, "start": {}, "n": 0}

def snap(tag):
    for c in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.Character):
        l = c.get_actor_location()
        k = c.get_name()
        if k not in st["start"]:
            st["start"][k] = l
        s0 = st["start"][k]
        mesh = c.mesh.get_skeletal_mesh_asset() if hasattr(c.mesh, "get_skeletal_mesh_asset") else None
        cm = c.get_component_by_class(unreal.CharacterMovementComponent)
        mode = cm.movement_mode if cm else None
        flag = " FELL" if l.z < s0.z - 150 else ""
        out.append("%s %s label=%s loc=(%d,%d,%d) start_z=%d mode=%s mesh=%s hidden=%s%s" % (
            tag, k, c.get_actor_label(), l.x, l.y, l.z, s0.z, mode, mesh.get_name() if mesh else None, c.is_hidden_ed() if False else c.get_editor_property("hidden"), flag))

def tick(dt):
    st["t"] += dt
    if st["n"] == 0 or st["t"] > st["n"] * 8.0:
        snap("t%.0f" % st["t"])
        st["n"] += 1
    if st["t"] > 26:
        open(os.path.join(unreal.Paths.project_saved_dir(), "NV_pie_npcs.txt"), "w").write("\n".join(out))
        unreal.unregister_slate_post_tick_callback(st["h"])
st["h"] = unreal.register_slate_post_tick_callback(tick)
