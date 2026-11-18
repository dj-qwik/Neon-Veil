"""PIE: look at each NPC from 4 m away and take a HighResShot; also dump their components.
Saved/NV_pie_npcshots.txt, Saved/NV_shots/npc_<label>.png"""
import os
import unreal
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
pc = unreal.GameplayStatics.get_player_controller(w, 0)
pawn = pc.get_controlled_pawn()
SHOTS = os.path.join(unreal.Paths.project_saved_dir(), "NV_shots")
out = []
npcs = [c for c in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.NVGuardCharacter)]
for c in npcs:
    out.append("== %s %s" % (c.get_actor_label(), c.get_actor_location()))
    for comp in c.get_components_by_class(unreal.SceneComponent):
        extra = ""
        if isinstance(comp, unreal.SkinnedMeshComponent):
            a = comp.get_skinned_asset() if hasattr(comp, "get_skinned_asset") else None
            extra = " asset=%s vis=%s" % (a.get_name() if a else None, comp.is_visible())
        out.append("   %s %s rel=%s world=%s%s" % (comp.get_name(), comp.get_class().get_name(), comp.get_editor_property("relative_location"), comp.get_world_location(), extra))
st = {"i": 0, "t": 0.0, "h": None, "ph": 0}
def tick(dt):
    st["t"] += dt
    if st["i"] >= len(npcs):
        open(os.path.join(unreal.Paths.project_saved_dir(), "NV_pie_npcshots.txt"), "w").write("\n".join(out))
        unreal.unregister_slate_post_tick_callback(st["h"])
        return
    c = npcs[st["i"]]
    l = c.get_actor_location()
    if st["ph"] == 0:
        fwd = c.get_actor_forward_vector()
        eye = l + fwd * 380 + unreal.Vector(0, 0, 40)
        pawn.set_actor_location(eye, False, True)
        st["ph"], st["t"] = 1, 0.0
    else:
        eye = pc.player_camera_manager.get_camera_location()
        pc.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(eye, l - unreal.Vector(0, 0, 40)))
        if st["ph"] == 1 and st["t"] > 1.0:
            unreal.SystemLibrary.execute_console_command(w, 'HighResShot 960x540 filename="%s"' % os.path.join(SHOTS, "npc_%s.png" % c.get_actor_label()).replace("\\", "/"))
            st["ph"], st["t"] = 2, 0.0
        elif st["ph"] == 2 and st["t"] > 0.5:
            st["ph"] = 0
            st["i"] += 1
st["h"] = unreal.register_slate_post_tick_callback(tick)
