"""Editor viewport shots for review. Usage: py nv_ed_shots.py <set>
Each shot moves the level viewport camera, waits for streaming/lighting to settle, then takes a HighResShot.
Output: Saved/NV_shots/ed_<name>.png"""
import os, sys
import unreal

SETS = {
    "dress": [
        ("crew_top", (6840, 4480, 790), (-89.9, 90)),
        ("crew_view", (6800, 3950, 590), (-14, 90)),
        ("hub_far", (7046, -8600, -11820), (14, 90)),
        ("hub_door", (7046, -7350, -11840), (4, 90)),
        ("lobby", (7046, -6380, -11830), (-4, 90)),
        ("conc_s", (7046, -3300, 580), (-6, 90)),
        ("conc_mid", (7600, -400, 580), (-6, 90)),
        ("conc_n", (7400, 3000, 580), (-6, -90)),
        ("board", (6560, 1900, 590), (0, 0)),
        ("warn_cab", (6858, -4380, -11790), (0, -90)),
    ],
    "dress2": [
        ("hub_far", (7046, -8600, -11820), (14, 90)),
        ("hub_door", (7046, -7600, -11830), (2, 90)),
        ("hub_left", (6500, -7200, -11830), (0, 75)),
        ("hub_right", (7600, -7200, -11830), (0, 105)),
        ("lobby", (7046, -6380, -11830), (-4, 90)),
        ("lobby_back", (7046, -5100, -11800), (-6, -90)),
        ("board", (6560, 1900, 590), (0, 0)),
        ("cab", (7010, -4572, -11800), (0, 180)),
        ("crew_view", (6800, 3950, 590), (-14, 90)),
        ("billboard", (7046, -9800, -11800), (28, 33)),
    ],
}
name = sys.argv[1] if len(sys.argv) > 1 else "dress"
only = sys.argv[2].split(",") if len(sys.argv) > 2 else None
plan = [s for s in SETS[name] if not only or s[0] in only]
UES = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
SHOTS = os.path.join(unreal.Paths.project_saved_dir(), "NV_shots")
unreal.EditorLevelLibrary.editor_set_game_view(True)
st = {"i": 0, "t": 0.0, "h": None, "phase": 0}

def tick(dt):
    st["t"] += dt
    if st["i"] >= len(plan):
        unreal.unregister_slate_post_tick_callback(st["h"])
        return
    nm, loc, rot = plan[st["i"]]
    if st["phase"] == 0:
        UES.set_level_viewport_camera_info(unreal.Vector(*loc), unreal.Rotator(pitch=rot[0], yaw=rot[1], roll=0))
        st["phase"], st["t"] = 1, 0.0
    elif st["phase"] == 1 and st["t"] > 1.6:
        unreal.SystemLibrary.execute_console_command(None, 'HighResShot 1280x720 filename="%s"' % os.path.join(SHOTS, "ed_" + nm + ".png").replace("\\", "/"))
        st["phase"], st["t"] = 2, 0.0
    elif st["phase"] == 2 and st["t"] > 0.8:
        st["phase"] = 0
        st["i"] += 1

st["h"] = unreal.register_slate_post_tick_callback(tick)
