"""Probe the KINEMATION Sci-fi FPS pack: arms/weapon bones, sockets, and component-space poses in the idle anims.
Report: Saved/NV_fps_probe.txt"""
import unreal
AL = unreal.AnimationLibrary
OUT = []
def log(*a):
    OUT.append(" ".join(str(x) for x in a))
K = "/Game/KINEMATION/Sci-fi_FPS_Pack"

def cs(anim, bone, frame=0):
    """Component-space transform of `bone` in `anim` at `frame` by composing the local chain to the root."""
    path = AL.find_bone_path_to_root(anim, bone)
    t = unreal.Transform()
    for b in reversed(list(path)):
        lt = AL.get_bone_pose_for_frame(anim, b, frame, False)
        t = lt.multiply(t) if hasattr(lt, "multiply") else unreal.MathLibrary.compose_transforms(lt, t)
    return t

def fmt(t):
    l, r = t.translation, t.rotation.rotator()
    return "loc(%.1f %.1f %.1f) rot(p%.1f y%.1f r%.1f)" % (l.x, l.y, l.z, r.pitch, r.yaw, r.roll)

arms = unreal.load_asset(f"{K}/Gloves/Meshes/SKM_SciFi_Arms")
log("arms", arms, "skeleton", arms.skeleton.get_path_name())
try:
    for s in arms.get_editor_property("sockets") or []:
        log("  arms socket", s.socket_name, s.bone_name, s.relative_location, s.relative_rotation)
except Exception as e:
    log("  sockets err", e)
try:
    for s in arms.skeleton.get_editor_property("sockets") or []:
        log("  skel socket", s.socket_name, s.bone_name, s.relative_location, s.relative_rotation)
except Exception as e:
    log("  skel sockets err", e)

for W, folder in (("ARX", "ARX_Mk1"), ("Gepard", "Gepard"), ("Onyx", "Onyx_Revolver"), ("TP12", "TP12")):
    a = unreal.load_asset(f"{K}/Animations/Character/UE5/{folder}/A_FP_{W}_Idle")
    if not a:
        log("no idle", W); continue
    names = [str(n) for n in AL.get_animation_track_names(a)]
    if W == "ARX":
        log("tracks:", ", ".join(names))
    log(f"== {W} idle frames {AL.get_num_frames(a)}")
    for b in ("root", "pelvis", "spine_05", "neck_01", "head", "Camera", "camera", "CameraBone", "VB Camera", "hand_r", "hand_l",
              "ik_hand_root", "ik_hand_gun", "ik_hand_r", "ik_hand_l", "VB ik_hand_gun", "weapon", "Weapon", "weapon_r"):
        if b in names:
            log(f"  {b:14s}", fmt(cs(a, b)))

for W, path in (("ARX", "ARX_Mk2_Rifle/SKM_ARX_Mk2"), ("Gepard", "Gepard/SKM_Gepard"), ("Onyx", "Onyx_Revolver/SKM_Onyx")):
    m = unreal.load_asset(f"{K}/Weapons/{path}")
    if not m:
        log("no weapon", W); continue
    bb = m.get_bounds()
    log(f"weapon {W} bounds origin {bb.origin} extent {bb.box_extent}")
    try:
        for s in m.get_editor_property("sockets") or []:
            log("  socket", s.socket_name, s.bone_name, s.relative_location, s.relative_rotation)
    except Exception as e:
        log("  sockets err", e)
    wa = unreal.EditorAssetLibrary.list_assets(f"{K}/Animations/Weapons", recursive=True)
    for p in wa:
        if f"/A_W_{W}_Idle" in p or (W == "ARX" and "A_W_ARX_Idle" in p):
            an = unreal.load_asset(p.split(".")[0])
            tn = [str(n) for n in AL.get_animation_track_names(an)]
            log("  weapon tracks:", ", ".join(tn[:30]))
            break
# KINEMATION weapon blueprints / data assets that may hold attach info
for p in unreal.EditorAssetLibrary.list_assets(f"{K}/Blueprints", recursive=True)[:60]:
    log("bp", p)
open(unreal.Paths.project_saved_dir() + "NV_fps_probe.txt", "w").write("\n".join(OUT))
