"""PIE (L_M00_GlassCrown, start of the ride): check the chase gunfire. During the firefight it aims the camera at the
two cars with a narrow FOV, grabs a burst of HighResShots, and every frame measures each visible tracer bolt against
the line between the cars (does it start at one hull and head for the other?).
Report: Saved/NV_pie_ride_gunfire.txt; shots Saved/NV_shots/gun_*.png"""
import os
import unreal
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
pc = unreal.GameplayStatics.get_player_controller(w, 0)
ride = unreal.GameplayStatics.get_all_actors_of_class(w, unreal.NVTramRide)[0]
director = unreal.GameplayStatics.get_all_actors_of_class(w, unreal.NVTramRideDirector)[0]
SHOTS = os.path.join(unreal.Paths.project_saved_dir(), "NV_shots")
chase0 = director.get_editor_property("chase_start")
SHOT_T = [chase0 + x for x in (10.6, 11.4, 12.2, 13.3, 14.4, 15.2)]
out = []
st = {"h": None, "i": 0, "frames": 0, "vis": 0, "bad": 0, "maxoff": 0.0, "fov": False}
def comp(name):
    return next((c for c in director.get_components_by_class(unreal.StaticMeshComponent) if c.get_name() == name), None)
tracers = [c for c in director.get_components_by_class(unreal.StaticMeshComponent)
           if c.static_mesh and c.static_mesh.get_name() == "Cylinder"]
out.append("tracer pool %d" % len(tracers))
def seg_dist(p, a, b):
    ab = b - a
    t = max(0.0, min(1.0, (p - a).dot(ab) / max(ab.dot(ab), 1.0)))
    return (a + ab * t - p).length()
def tick(dt):
    t = ride.get_ride_time()
    c = t - chase0
    s_, p_ = comp("Suspect"), comp("Police")
    if 10.0 <= c <= 15.6 and s_ and p_:
        a, b = s_.get_world_location(), p_.get_world_location()
        st["frames"] += 1
        for tr in tracers:
            if not tr.is_visible():
                continue
            st["vis"] += 1
            ctr = tr.get_world_location()
            up = tr.get_up_vector()
            half = tr.get_world_scale().z * 50.0
            ends = (ctr + up * half, ctr - up * half)
            off = max(seg_dist(e, a, b) for e in ends)
            st["maxoff"] = max(st["maxoff"], off)
            if off > 700:
                st["bad"] += 1
        if not st["fov"]:
            unreal.SystemLibrary.execute_console_command(w, "fov 38")
            st["fov"] = True
        eye = pc.player_camera_manager.get_camera_location()
        pc.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(eye, (a + b) * 0.5))
    if st["i"] < len(SHOT_T) and t >= SHOT_T[st["i"]]:
        unreal.SystemLibrary.execute_console_command(w, 'HighResShot 1280x720 filename="%s"' % os.path.join(SHOTS, "gun_%d.png" % st["i"]).replace("\\", "/"))
        st["i"] += 1
    if c > 16.5:
        unreal.SystemLibrary.execute_console_command(w, "fov 0")
        out.append("frames %d, visible bolt samples %d, off-line (>7 m from the car-to-car line) %d, worst %.0f cm"
                   % (st["frames"], st["vis"], st["bad"], st["maxoff"]))
        open(os.path.join(unreal.Paths.project_saved_dir(), "NV_pie_ride_gunfire.txt"), "w").write("\n".join(out))
        unreal.unregister_slate_post_tick_callback(st["h"])
st["h"] = unreal.register_slate_post_tick_callback(tick)
