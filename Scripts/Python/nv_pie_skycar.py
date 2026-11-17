"""PIE (L_M00_Prologue): stage the sky car sequence. Keeps Ghost back while the driver boards, then walks him in to
trigger lights-on and liftoff, aiming the view at the car and grabbing HighResShots.
Saved/NV_pie_skycar.txt, Saved/NV_shots/sky_*.png"""
import os
import unreal
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
pc = unreal.GameplayStatics.get_player_controller(w, 0)
pawn = pc.get_controlled_pawn()
car = unreal.GameplayStatics.get_all_actors_of_class(w, unreal.NVSkyCarLiftoff)[0]
root = car.get_editor_property("car_root")
SHOTS = os.path.join(unreal.Paths.project_saved_dir(), "NV_shots")
ZS = -12000.0
out = []
# (time, action, arg)
PLAN = [(0.2, "tp", (7046, -9600)), (3.5, "shot", "sky_1_driver_walk"), (6.0, "shot", "sky_2_driver_board"),
        (8.4, "shot", "sky_3_canopy"), (13.0, "tp", (7180, -9300)), (14.2, "shot", "sky_4_lights"),
        (16.5, "tp", (7040, -8120)), (17.6, "shot", "sky_5_spool"), (19.6, "shot", "sky_6_rise"),
        (22.0, "shot", "sky_7_rise_high"), (24.6, "shot", "sky_8_depart"), (27.0, "shot", "sky_9_overhead"),
        (30.0, "shot", "sky_10_lane")]
st = {"i": 0, "t": 0.0, "h": None}
def look():
    eye = pc.player_camera_manager.get_camera_location()
    pc.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(eye, root.get_world_location() + unreal.Vector(0, 0, 60)))
def tick(dt):
    st["t"] += dt
    t = st["t"]
    look()
    while st["i"] < len(PLAN) and t >= PLAN[st["i"]][0]:
        tt, act, arg = PLAN[st["i"]]
        if act == "tp":
            pawn.set_actor_location(unreal.Vector(arg[0], arg[1], ZS + 100), False, True)
            out.append("t %.1f tp %s dist %.0f" % (t, arg, (pawn.get_actor_location() - car.get_actor_location()).length()))
        else:
            unreal.SystemLibrary.execute_console_command(w, 'HighResShot 1280x720 filename="%s"' % os.path.join(SHOTS, arg + ".png").replace("\\", "/"))
            out.append("t %.1f %s car at %s" % (t, arg, root.get_world_location()))
        st["i"] += 1
    if st["i"] >= len(PLAN) or t > 40:
        open(os.path.join(unreal.Paths.project_saved_dir(), "NV_pie_skycar.txt"), "w").write("\n".join(out))
        unreal.unregister_slate_post_tick_callback(st["h"])
st["h"] = unreal.register_slate_post_tick_callback(tick)
