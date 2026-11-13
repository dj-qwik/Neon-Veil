"""Editor-viewport captures of the Crown review cameras. arg: tag (e.g. before/after).
Writes Saved/Screenshots/NV/<tag>_<cam>.png via the automation screenshot API (one per tick)."""
import unreal, sys
tag = sys.argv[1] if len(sys.argv) > 1 else "shot"
CAMS = {"atrium": ((3700, -800, 260), (-8, 25)), "sim": ((6700, 1000, 300), (-10, -25)),
        "gallery": ((10600, -250, 200), (-5, 0)), "drone": ((8700, 560, 400), (-3, 5))}
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
queue = list(CAMS.items())
state = {"i": 0, "wait": 0, "h": None, "phase": "move"}
def tick(dt):
    if state["wait"] > 0:
        state["wait"] -= 1
        return
    i = state["i"]
    if state["phase"] == "shoot":
        unreal.AutomationLibrary.take_high_res_screenshot(1600, 900, unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_saved_dir()) + "Screenshots/NV/%s_%s.png" % (tag, queue[i][0]))
        state["i"] = i + 1; state["phase"] = "move"; state["wait"] = 20
        return
    if i >= len(queue):
        unreal.unregister_slate_post_tick_callback(state["h"])
        unreal.log("[NV] shots done")
        return
    (x, y, z), (p, yw) = queue[i][1]
    ues.set_level_viewport_camera_info(unreal.Vector(x, y, z), unreal.Rotator(roll=0, pitch=p, yaw=yw))
    state["phase"] = "shoot"; state["wait"] = 150   # let exposure/streaming settle
state["h"] = unreal.register_slate_post_tick_callback(tick)
