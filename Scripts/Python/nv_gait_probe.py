"""Probe the template locomotion cycles: length, sync markers, root speed and the phase where the left foot plants
(most forward along the travel direction). Report: Saved/NV_gait_probe.txt (and NV_gait_probe.json)"""
import unreal, json, math
R = "/Game/Characters/Mannequins/Anims/"
DIRS = ["Fwd", "Fwd_Right", "Right", "Bwd_Right", "Bwd", "Bwd_Left", "Left", "Fwd_Left"]
AL = unreal.AnimationLibrary
OUT, DATA = [], {}
opts = unreal.AnimPoseEvaluationOptions()
try:
    opts.set_editor_property("evaluation_type", unreal.AnimDataEvalType.RAW)
except Exception:
    pass
CS = unreal.AnimPoseSpaces.WORLD
def bone(pose, name):
    return unreal.AnimPoseExtensions.get_bone_pose(pose, name, CS).translation
for kind in ("Unarmed", "Rifle", "Pistol"):
    for gait in ("Walk", "Jog"):
        for d in DIRS:
            p = f"{kind}/{gait}/MF_{kind}_{gait}_{d}"
            a = unreal.load_asset(R + p)
            if not a:
                OUT.append(f"{p}: missing"); continue
            L = a.get_play_length()
            marks = []
            try:
                marks = [(str(m.marker_name), round(m.time, 3)) for m in AL.get_animation_sync_markers(a)]
            except Exception as e:
                marks = [f"err {e}"]
            N = 40
            samples = []
            for i in range(N + 1):
                t = L * i / N
                pose = unreal.AnimPoseExtensions.get_anim_pose_at_time(a, t, opts)
                samples.append((t, bone(pose, "root"), bone(pose, "foot_l"), bone(pose, "foot_r")))
            r0, r1 = samples[0][1], samples[-1][1]
            dx, dy = r1.x - r0.x, r1.y - r0.y
            dist = math.hypot(dx, dy)
            # travel direction: root motion if present, else the axis the feet swing along
            if dist < 5:
                xs = [s[2].x for s in samples]; ys = [s[2].y for s in samples]
                dx, dy = (max(xs) - min(xs)), (max(ys) - min(ys))
                # pick dominant axis, sign unknown -> use the direction from the "Fwd" naming later
            n = math.hypot(dx, dy) or 1
            ux, uy = dx / n, dy / n
            # left foot forward-most relative to root
            best = max(samples, key=lambda s: (s[2].x - s[1].x) * ux + (s[2].y - s[1].y) * uy)
            lead = best[0] / L
            OUT.append(f"{p}: len={L:.3f} speed={dist / L:.0f} dir=({ux:.2f},{uy:.2f}) lfoot_fwd_phase={lead:.3f} markers={marks}")
            DATA[p] = dict(len=L, speed=dist / L, lphase=lead, markers=marks)
open(unreal.Paths.project_saved_dir() + "NV_gait_probe.txt", "w").write("\n".join(OUT))
open(unreal.Paths.project_saved_dir() + "NV_gait_probe.json", "w").write(json.dumps(DATA, indent=1))
