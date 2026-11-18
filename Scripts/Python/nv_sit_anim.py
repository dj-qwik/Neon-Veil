"""Author a seated-on-a-bench idle for the citizens: /Game/NeonVeil/Animations/Citizens/AS_NV_SitBench.

There is no sitting animation in the project, so this builds one from the mannequin idle (MM_Idle):
  * the upper body (spine, neck, head, clavicles) keeps MM_Idle's breathing, with a slight forward lean;
  * pelvis drops so the feet stay planted on the floor;
  * thighs point forward, shins drop to the floor, forearms rest toward the knees, feet and hands keep their
    reference orientation.
Bone targets are directions in component space (mannequin faces +Y), converted to local rotations by FK, so no
per-bone axis guessing is needed. Usage: py nv_sit_anim.py   Report: Saved/NV_sit_anim.txt"""
import math
import unreal

OUT = []
def log(*a):
    OUT.append(" ".join(str(x) for x in a))

EAL = unreal.EditorAssetLibrary
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
SRC = "/Game/Characters/Mannequins/Anims/Unarmed/MM_Idle"
DST_DIR, NAME = "/Game/NeonVeil/Animations/Citizens", "AS_NV_SitBench"
SKM = "/Game/Characters/Mannequins/Meshes/SKM_Manny_Simple"

# ---------------------------------------------------------------- quaternion helpers (x, y, z, w)
def q_of(u):
    return (u.x, u.y, u.z, u.w)
def qmul(a, b):
    ax, ay, az, aw = a; bx, by, bz, bw = b
    return (aw * bx + ax * bw + ay * bz - az * by,
            aw * by - ax * bz + ay * bw + az * bx,
            aw * bz + ax * by - ay * bx + az * bw,
            aw * bw - ax * bx - ay * by - az * bz)
def qinv(a):
    return (-a[0], -a[1], -a[2], a[3])
def qrot(q, v):
    p = qmul(qmul(q, (v[0], v[1], v[2], 0.0)), qinv(q))
    return (p[0], p[1], p[2])
def norm(v):
    l = math.sqrt(sum(c * c for c in v)) or 1.0
    return tuple(c / l for c in v)
def add(a, b): return tuple(x + y for x, y in zip(a, b))
def sub(a, b): return tuple(x - y for x, y in zip(a, b))
def mul(a, k): return tuple(x * k for x in a)
def dot(a, b): return sum(x * y for x, y in zip(a, b))
def cross(a, b): return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])
def between(u, v):
    u, v = norm(u), norm(v)
    c = cross(u, v); d = dot(u, v)
    if d < -0.9999:
        ax = norm(cross(u, (1, 0, 0)) if abs(u[0]) < 0.9 else cross(u, (0, 1, 0)))
        return (ax[0], ax[1], ax[2], 0.0)
    q = (c[0], c[1], c[2], 1.0 + d)
    l = math.sqrt(sum(x * x for x in q))
    return tuple(x / l for x in q)
def axis_angle(ax, deg):
    ax = norm(ax); s = math.sin(math.radians(deg) / 2)
    return (ax[0] * s, ax[1] * s, ax[2] * s, math.cos(math.radians(deg) / 2))

# ---------------------------------------------------------------- reference skeleton (bind pose)
mesh = unreal.load_asset(SKM)
probe = EAS.spawn_actor_from_class(unreal.SkeletalMeshActor, unreal.Vector(0, 0, -60000))
comp = probe.skeletal_mesh_component
comp.set_skinned_asset_and_update(mesh)
BONES = [comp.get_bone_name(i) for i in range(comp.get_num_bones())]
PARENT = {str(b): str(comp.get_parent_bone(b)) for b in BONES}
REF_L = {}
for b in BONES:
    t = comp.get_socket_transform(b, unreal.RelativeTransformSpace.RTS_PARENT_BONE_SPACE)
    REF_L[str(b)] = (q_of(t.rotation), (t.translation.x, t.translation.y, t.translation.z))
EAS.destroy_actor(probe)
NAMES = [str(b) for b in BONES]

def fk(local):
    cs = {}
    for b in NAMES:                       # bones come parent-first
        q, p = local[b]
        par = PARENT.get(b)
        if par in cs:
            pq, pp = cs[par]
            cs[b] = (qmul(pq, q), add(pp, qrot(pq, p)))
        else:
            cs[b] = (q, p)
    return cs

ref_cs = fk(REF_L)
fwd = norm((0.0, ref_cs["ball_l"][1][1] - ref_cs["foot_l"][1][1], 0.0))
side_l = norm((ref_cs["thigh_l"][1][0] - ref_cs["pelvis"][1][0], 0.0, 0.0))
UP = (0.0, 0.0, 1.0)
log("forward", fwd, "left", side_l)

def child_of(b):
    for c in NAMES:
        if PARENT.get(c) == b and "twist" not in c and "ik_" not in c:
            return c
    return None

def aim(local, bone, target_dir):
    """Rotate `bone` (in component space) so its direction toward its main child points at target_dir."""
    cs = fk(local)
    par = PARENT[bone]
    c = {"thigh_l": "calf_l", "thigh_r": "calf_r", "calf_l": "foot_l", "calf_r": "foot_r",
         "upperarm_l": "lowerarm_l", "upperarm_r": "lowerarm_r", "lowerarm_l": "hand_l", "lowerarm_r": "hand_r"}[bone]
    cur = norm(sub(cs[c][1], cs[bone][1]))
    nq = qmul(between(cur, target_dir), cs[bone][0])
    local[bone] = (qmul(qinv(cs[par][0]), nq), local[bone][1])

def keep_cs(local, bone, cs_rot):
    cs = fk(local)
    local[bone] = (qmul(qinv(cs[PARENT[bone]][0]), cs_rot), local[bone][1])

SEAT_H = 56.0          # the station benches' seat pads sit 54..58 cm off the floor
HIP_OVER_SEAT = 10.0   # thigh joints sit this far above the seat surface
def seated(local, slope=0.06):
    L = dict(local)
    for s, sgn in (("l", 1.0), ("r", -1.0)):
        side = mul(side_l, sgn)
        aim(L, "thigh_" + s, norm(add(add(fwd, mul(side, 0.10)), mul(UP, -slope))))
        aim(L, "calf_" + s, norm(add(add(mul(fwd, 0.14), mul(side, 0.03)), mul(UP, -1.0))))
        keep_cs(L, "foot_" + s, ref_cs["foot_" + s][0])
        aim(L, "upperarm_" + s, norm(add(add(mul(fwd, 0.42), mul(side, 0.16)), mul(UP, -0.88))))
        aim(L, "lowerarm_" + s, norm(add(add(mul(fwd, 0.92), mul(side, -0.18)), mul(UP, -0.40))))
    return L

# static legs / arms from the bind pose; thighs slope down just enough that the hips land on the seat pad with the
# feet still flat on the floor
def solve(slope):
    P = seated(REF_L, slope)
    c = fk(P)
    dr = c["foot_l"][1][2] - ref_cs["foot_l"][1][2]
    return P, c, dr, c["thigh_l"][1][2] - dr
lo, hi = 0.0, 0.9
for _ in range(18):
    mid = (lo + hi) / 2
    if solve(mid)[3] < SEAT_H + HIP_OVER_SEAT:
        lo = mid
    else:
        hi = mid
POSE, cs0, drop, hip_z = solve((lo + hi) / 2)
log("thigh slope", round((lo + hi) / 2, 3), "hip z", round(hip_z, 1))
log("pelvis drop", round(drop, 1), "thigh z", round(cs0["thigh_l"][1][2] - drop, 1),
    "knee", tuple(round(v, 1) for v in cs0["calf_l"][1]), "ankle", tuple(round(v, 1) for v in cs0["foot_l"][1]))
LEGS_ARMS = [b for b in NAMES if any(b.startswith(k) for k in ("thigh_", "calf_", "foot_", "upperarm_", "lowerarm_"))
             and "twist" not in b]

# lean the torso forward a little at spine_01 (delta expressed in spine_01's own frame)
lean_cs = axis_angle(cross(UP, fwd), 7.0)
sp_cs = ref_cs["spine_01"][0]
LEAN_LOCAL = qmul(qmul(qinv(sp_cs), lean_cs), sp_cs)

# ---------------------------------------------------------------- build the sequence from MM_Idle
dst = f"{DST_DIR}/{NAME}"
# rewritten in place when it exists (citizens in the level reference it)
anim = unreal.load_asset(dst) if EAL.does_asset_exist(dst) else EAL.duplicate_asset(SRC, dst)
try:
    ctrl = anim.controller
except Exception:
    ctrl = anim.get_editor_property("controller")
try:
    nkeys = ctrl.get_model().get_number_of_keys()
except Exception as e:
    log("model keys failed", e)
    nkeys = unreal.AnimationLibrary.get_num_frames(anim) + 1
log("keys", nkeys)
src = unreal.load_asset(SRC)
AL = unreal.AnimationLibrary
def pose_at(b, f):
    t = AL.get_bone_pose_for_frame(src, b, f, False)
    return t
ctrl.open_bracket(unreal.Text("NV sit"), True)
for b in ["pelvis", "spine_01"] + LEGS_ARMS:
    pos, rot, scl = [], [], []
    for f in range(nkeys):
        t = pose_at(b, f)
        p = t.translation
        q = q_of(t.rotation)
        if b == "pelvis":
            par = PARENT["pelvis"]
            pq = ref_cs[par][0] if par in ref_cs else (0, 0, 0, 1)
            dz = qrot(qinv(pq), (0.0, 0.0, -drop))
            p = unreal.Vector(p.x + dz[0], p.y + dz[1], p.z + dz[2])
        elif b == "spine_01":
            q = qmul(q, LEAN_LOCAL)
        elif b in POSE:
            q = POSE[b][0]
        pos.append(p)
        rot.append(unreal.Quat(q[0], q[1], q[2], q[3]))
        scl.append(t.scale3d)
    ctrl.set_bone_track_keys(b, pos, rot, scl, True)
ctrl.close_bracket(True)
EAL.save_loaded_asset(anim)
log("wrote", dst, "bones", len(LEGS_ARMS) + 2)
open(unreal.Paths.project_saved_dir() + "NV_sit_anim.txt", "w").write("\n".join(OUT))
