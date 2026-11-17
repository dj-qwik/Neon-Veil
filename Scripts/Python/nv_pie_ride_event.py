"""PIE (L_M00_GlassCrown): watch the Crown Line ride event. Turns Ghost to the left windows at the spotlight /
firefight / crash and grabs HighResShots. Saved/NV_pie_ride_event.txt, Saved/NV_shots/ride_*.png"""
import os
import unreal
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
pc = unreal.GameplayStatics.get_player_controller(w, 0)
pawn = pc.get_controlled_pawn()
ride = unreal.GameplayStatics.get_all_actors_of_class(w, unreal.NVTramRide)[0]
SHOTS = os.path.join(unreal.Paths.project_saved_dir(), "NV_shots")
out = []
PLAN = [(15.0, "ride_a_overtake", -60, 0), (18.6, "ride_b_spotlight", -85, 0), (21.0, "ride_c_spotlight2", -80, -5),
        (25.0, "ride_d_firefight", -50, 5), (28.9, "ride_e_hit", -50, 0), (31.6, "ride_f_crash", -40, -5),
        (33.5, "ride_g_after", -40, -5)]
st = {"i": 0, "h": None, "prev": None, "yaw": None}
director = [a for a in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.NVTramRideDirector)][0]
def car(name):
    return next((c for c in director.get_components_by_class(unreal.StaticMeshComponent) if c.get_name() == name), None)
def tick(dt):
    t = ride.get_ride_time()
    tram = ride.get_editor_property("tram")
    loc = tram.get_actor_location()
    if st["prev"] is not None and (loc - st["prev"]).length() > 1:
        d = loc - st["prev"]
        st["yaw"] = unreal.MathLibrary.make_rot_from_x(d).yaw
    st["prev"] = loc
    if st["i"] < len(PLAN) and t >= PLAN[st["i"]][0] - 0.25 and st["yaw"] is not None:
        tt, name, dyaw, pitch = PLAN[st["i"]]
        rot = unreal.Rotator(roll=0, pitch=pitch, yaw=st["yaw"] + dyaw)
        if name in ("ride_d_firefight", "ride_e_hit"):
            s_, p_ = car("Suspect"), car("Police")
            if s_ and p_:
                mid = (s_.get_world_location() + p_.get_world_location()) * 0.5
                eye = pc.player_camera_manager.get_camera_location()
                rot = unreal.MathLibrary.find_look_at_rotation(eye, mid)
                out.append("  %s: action %.0f cm away, bearing %.0f vs travel" % (name, (mid - eye).length(), rot.yaw - st["yaw"]))
        pc.set_control_rotation(rot)
        if t >= tt:
            unreal.SystemLibrary.execute_console_command(w, 'HighResShot 1280x720 filename="%s"' % os.path.join(SHOTS, name + ".png").replace("\\", "/"))
            out.append("%s at ride %.1f" % (name, t))
            st["i"] += 1
    if st["i"] >= len(PLAN) or t > 45:
        out.append("ride time %.1f" % t)
        open(os.path.join(unreal.Paths.project_saved_dir(), "NV_pie_ride_event.txt"), "w").write("\n".join(out))
        unreal.unregister_slate_post_tick_callback(st["h"])
out.append("start ride time %.1f" % ride.get_ride_time())
st["h"] = unreal.register_slate_post_tick_callback(tick)
