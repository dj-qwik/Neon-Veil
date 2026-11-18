"""PIE, after the sky car has left: walk Ghost onto the old parking spot (sweep) to prove the blocker is gone and grab
a shot of the kerb to check the lift dust has cleared. Saved/NV_pie_skycar2.txt, Saved/NV_shots/sky_11_spot.png"""
import os
import unreal
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
pc = unreal.GameplayStatics.get_player_controller(w, 0)
pawn = pc.get_controlled_pawn()
car = unreal.GameplayStatics.get_all_actors_of_class(w, unreal.NVSkyCarLiftoff)[0]
ZS = -12000.0
out = []
blk = car.get_editor_property("blocker")
out.append("blocker collision %s" % blk.get_collision_enabled())
pawn.set_actor_location(unreal.Vector(7000, -8180, ZS + 100), False, True)
pawn.set_actor_location(unreal.Vector(6430, -8180, ZS + 100), True, True)
l = pawn.get_actor_location()
out.append("swept to %s (target x 6430)" % l)
fx = [c for c in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.Actor) if c.get_components_by_class(unreal.NiagaraComponent)]
for a in fx:
    for c in a.get_components_by_class(unreal.NiagaraComponent):
        p = c.get_world_location()
        if abs(p.x - 6430) < 400 and abs(p.y + 8180) < 400:
            out.append("niagara near spot: %s %s active=%s" % (a.get_name(), c.get_name(), c.is_active()))
pawn.set_actor_location(unreal.Vector(7300, -9000, ZS + 100), False, True)
eye = pc.player_camera_manager.get_camera_location()
pc.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(eye, unreal.Vector(6430, -8180, ZS + 60)))
st = {"t": 0.0, "h": None}
def tick(dt):
    st["t"] += dt
    eye = pc.player_camera_manager.get_camera_location()
    pc.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(eye, unreal.Vector(6430, -8180, ZS + 60)))
    if st["t"] > 1.0:
        unreal.SystemLibrary.execute_console_command(w, 'HighResShot 1280x720 filename="%s"' % os.path.join(unreal.Paths.project_saved_dir(), "NV_shots", "sky_11_spot.png").replace("\\", "/"))
        open(os.path.join(unreal.Paths.project_saved_dir(), "NV_pie_skycar2.txt"), "w").write("\n".join(out))
        unreal.unregister_slate_post_tick_callback(st["h"])
st["h"] = unreal.register_slate_post_tick_callback(tick)
