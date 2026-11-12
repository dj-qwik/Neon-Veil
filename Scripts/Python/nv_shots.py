"""NEON VEIL - review camera: captures a fixed set of editor viewport shots of M00 for art review.

Moves the level viewport camera through SHOTS, waits for streaming, then takes a high-res
screenshot of each into Saved/Screenshots/NV/<name>.png. Runs over several editor ticks.
Usage: py nv_run.py nv_shots      (optional: set NV_SHOTS env/argv filter later)
"""
import os
import unreal

SHOTS = [
    ("A_skybridge",   (-300, 0, 175),      (0, 0)),
    ("A_view_out",    (1700, -150, 175),   (-4, 70)),
    ("B_hero_glass",  (4900, -700, 175),   (2, 90)),
    ("B_atrium_wide", (3650, -600, 260),   (-4, 40)),
    ("B_arch",        (5200, 0, 175),      (0, 0)),
    ("C_sim_entry",   (6500, -1300, 350),  (-8, 30)),
    ("C_sim_lane",    (6600, 600, 175),    (0, 0)),
    ("D_gallery",     (10500, 0, 175),     (0, 0)),
    ("D_holo",        (12100, -250, 200),  (-12, 25)),
    ("E_antechamber", (14900, 0, 175),     (0, 0)),
]
WAIT_TICKS = 90
OUT = os.path.join(unreal.Paths.project_saved_dir(), "Screenshots", "NV")
os.makedirs(OUT, exist_ok=True)

UES = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
state = {"i": 0, "t": 0, "handle": None}

def tick(dt):
    i = state["i"]
    if i >= len(SHOTS):
        unreal.unregister_slate_post_tick_callback(state["handle"])
        unreal.log("[NV shots] done -> " + OUT)
        with open(os.path.join(OUT, "_done.txt"), "w") as f:
            f.write("\n".join(s[0] for s in SHOTS))
        return
    name, loc, rot = SHOTS[i]
    if state["t"] == 0:
        UES.set_level_viewport_camera_info(unreal.Vector(*loc), unreal.Rotator(pitch=rot[0], yaw=rot[1], roll=0))
    state["t"] += 1
    if state["t"] == WAIT_TICKS:
        unreal.AutomationLibrary.take_high_res_screenshot(1600, 900, os.path.join(OUT, name + ".png"))
    if state["t"] >= WAIT_TICKS + 20:
        state["i"] += 1
        state["t"] = 0

state["handle"] = unreal.register_slate_post_tick_callback(tick)
