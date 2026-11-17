"""PIE: Ghost pressed against the atrium west wall with the Kestrel, firing a burst; shots before/during/after.
Saved/NV_shots/wallgun_{0,1,2}.png, Saved/NV_pie_wallgun.txt"""
import os
import unreal
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
pc = unreal.GameplayStatics.get_player_controller(w, 0)
pawn = pc.get_controlled_pawn()
wc = pawn.get_component_by_class(unreal.NVWeaponComponent)
SHOTS = os.path.join(unreal.Paths.project_saved_dir(), "NV_shots")
out = []
k = unreal.load_asset("/Game/NeonVeil/Data/Weapons/DA_Weapon_Kestrel")
wc.give_weapon(k, True)
pawn.teleport(unreal.Vector(3545, -650, 110), unreal.Rotator(0, 0, 180))
pc.set_control_rotation(unreal.Rotator(roll=0, pitch=0, yaw=180))
cam = pawn.get_component_by_class(unreal.CameraComponent)
out.append("fp scale %s weapon %s" % (cam.get_editor_property("first_person_scale"), wc.get_current_weapon().get_name() if wc.get_current_weapon() else None))
st = {"t": 0.0, "n": 0, "h": None}
def shot(i):
    unreal.SystemLibrary.execute_console_command(w, 'HighResShot 1280x720 filename="%s"' % os.path.join(SHOTS, "wallgun_%d.png" % i).replace("\\", "/"))
def tick(dt):
    st["t"] += dt
    t, n = st["t"], st["n"]
    if n == 0 and t > 1.5:
        out.append("pawn %s" % pawn.get_actor_location()); shot(0); wc.start_fire(); st["n"] = 1
    elif n == 1 and t > 1.9:
        shot(1); st["n"] = 2
    elif n == 2 and t > 2.6:
        wc.stop_fire(); st["n"] = 3
    elif n == 3 and t > 3.4:
        shot(2); st["n"] = 4
    elif n == 4 and t > 4.0:
        open(os.path.join(unreal.Paths.project_saved_dir(), "NV_pie_wallgun.txt"), "w").write("\n".join(out))
        unreal.unregister_slate_post_tick_callback(st["h"])
st["h"] = unreal.register_slate_post_tick_callback(tick)
