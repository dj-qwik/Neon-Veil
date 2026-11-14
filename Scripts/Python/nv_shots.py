"""Editor viewport photo tool. Reads Saved/NV_shots_in.json: [{"name":..,"loc":[x,y,z],"rot":[pitch,yaw]}...]
and, one per few frames, moves the level viewport camera there and writes Saved/NV_shots/<name>.png (1280x720).
Runs asynchronously on slate ticks; writes Saved/NV_shots/_done.txt when finished."""
import json, os
import unreal
SAVED = unreal.Paths.project_saved_dir()
OUT = os.path.join(SAVED, "NV_shots")
os.makedirs(OUT, exist_ok=True)
shots = json.load(open(os.path.join(SAVED, "NV_shots_in.json")))
for f in os.listdir(OUT):
    if f.endswith(".png") or f == "_done.txt":
        os.remove(os.path.join(OUT, f))
UES = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
state = {"i": 0, "t": 0, "h": None}
def tick(dt):
    i = state["i"]
    if i >= len(shots):
        if state["t"] > 40:
            open(os.path.join(OUT, "_done.txt"), "w").write(str(len(shots)))
            unreal.unregister_slate_post_tick_callback(state["h"])
        state["t"] += 1
        return
    s = shots[i]
    if state["t"] == 0:
        p, y = s["rot"][0], s["rot"][1]
        UES.set_level_viewport_camera_info(unreal.Vector(*s["loc"]), unreal.Rotator(roll=0, pitch=p, yaw=y))
    if state["t"] == 25:
        path = os.path.join(OUT, s["name"] + ".png").replace("\\", "/")
        unreal.SystemLibrary.execute_console_command(None, f'HighResShot 1280x720 filename="{path}"')
    state["t"] += 1
    if state["t"] > 45:
        state["i"] += 1
        state["t"] = 0
state["h"] = unreal.register_slate_post_tick_callback(tick)
