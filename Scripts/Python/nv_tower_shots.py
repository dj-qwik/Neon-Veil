"""Frame one instance of each skyline tower design (viewport capture) to spot spiral window patterns.
Writes Saved/Screenshots/NV/tower_<design>.png"""
import unreal
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
seen = {}
for a in EAS.get_all_level_actors():
    c = a.get_class().get_name()
    if "Tower" in c and c not in seen:
        seen[c] = a
queue = list(seen.items())
state = {"i": 0, "wait": 0, "phase": "move", "h": None}
def tick(dt):
    if state["wait"] > 0:
        state["wait"] -= 1; return
    i = state["i"]
    if state["phase"] == "shoot":
        unreal.AutomationLibrary.take_high_res_screenshot(1280, 720, unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_saved_dir()) + "Screenshots/NV/tower_%s.png" % queue[i][0][20:28])
        state["i"] = i + 1; state["phase"] = "move"; state["wait"] = 15; return
    if i >= len(queue):
        unreal.unregister_slate_post_tick_callback(state["h"]); unreal.log("[NV] tower shots done"); return
    a = queue[i][1]
    o, e = a.get_actor_bounds(False)
    d = max(e.x, e.y) * 3.2
    cam = unreal.Vector(o.x - d, o.y, o.z + e.z * 0.2)
    ues.set_level_viewport_camera_info(cam, unreal.Rotator(roll=0, pitch=0, yaw=0))
    state["phase"] = "shoot"; state["wait"] = 120
state["h"] = unreal.register_slate_post_tick_callback(tick)
