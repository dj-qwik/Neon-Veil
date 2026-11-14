"""Glass Crown interior rebuild with the Etherion "Modular Scifi Interior" kit.
Gameplay geometry (the A_/B_/C_/D_/E_ cubes) is kept as-is for collision; Etherion floor, ceiling and wall panels
are laid over the visible faces (no collision), plus a few props. Idempotent: wipes folder R_Ether / tag NVE first.
Report: Saved/NV_l1_crown_etherion.txt"""
import math, random
import unreal

EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
LES = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
OUT = []
def log(*a):
    OUT.append(" ".join(str(x) for x in a))
V = unreal.Vector

MAP = "/Game/NeonVeil/Maps/M00/L_M00_GlassCrown"
if not unreal.EditorLevelLibrary.get_editor_world().get_path_name().startswith(MAP):
    LES.load_level(MAP)

FOLDER, TAG = "R_Ether", "NVE"
nw = 0
for a in list(EAS.get_all_level_actors()):
    if str(a.get_folder_path()) == FOLDER or TAG in a.tags:
        EAS.destroy_actor(a); nw += 1
log("wiped:", nw)

K = "/Game/ModularScifiInterior/Meshes"
def M(p):
    m = unreal.load_asset(p)
    if not m:
        log("MISSING", p)
    return m
WALLS = [m for m in (M(f"{K}/Walls/SM_Wall_D_A"), M(f"{K}/Walls/SM_Wall_D_B")) if m]
FLOORS = [m for m in (M(f"{K}/FloorsAndCeilings/SM_Floor_A"), M(f"{K}/FloorsAndCeilings/SM_Floor_B")) if m]
CEILS = [m for m in (M(f"{K}/FloorsAndCeilings/SM_Ceiling_A"), M(f"{K}/FloorsAndCeilings/SM_Ceiling_B")) if m]
PLANT = M(f"{K}/Props/SM_FlowerPot_A")
CONSOLE = M(f"{K}/Props/SM_Console")
HOLO = M(f"{K}/Props/SM_HoloTable")
LIGHTSTRIP = M(f"{K}/Props/SM_Light_A")
WALL_FRONT = 1   # +1: the panel's detailed face looks down local +Y; flip to -1 if shots show the back
rng = random.Random(7)
count = [0]

def fit(label, mesh, lo, hi, yaw=0.0, shadows=True):
    """Place `mesh` so its (yawed) local bounds exactly fill the world AABB lo..hi. yaw in multiples of 90."""
    bb = mesh.get_bounding_box()
    lmin, lmax = bb.min, bb.max
    lsize = [lmax.x - lmin.x, lmax.y - lmin.y, lmax.z - lmin.z]
    lc = [(lmax.x + lmin.x) / 2, (lmax.y + lmin.y) / 2, (lmax.z + lmin.z) / 2]
    tsize = [hi[i] - lo[i] for i in range(3)]
    tc = [(hi[i] + lo[i]) / 2 for i in range(3)]
    swap = int(round(yaw / 90.0)) % 2 == 1
    sx = tsize[1 if swap else 0] / max(lsize[0], 1e-3)
    sy = tsize[0 if swap else 1] / max(lsize[1], 1e-3)
    sz = tsize[2] / max(lsize[2], 1e-3)
    ox, oy, oz = lc[0] * sx, lc[1] * sy, lc[2] * sz
    r = math.radians(yaw)
    wx, wy = ox * math.cos(r) - oy * math.sin(r), ox * math.sin(r) + oy * math.cos(r)
    a = EAS.spawn_actor_from_class(unreal.StaticMeshActor, V(tc[0] - wx, tc[1] - wy, tc[2] - oz),
                                   unreal.Rotator(roll=0, pitch=0, yaw=yaw))
    c = a.static_mesh_component
    c.set_static_mesh(mesh)
    a.set_actor_scale3d(V(sx, sy, sz))
    c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    c.set_editor_property("cast_shadow", shadows)
    a.set_actor_label(label); a.set_folder_path(FOLDER); a.tags = [TAG]
    count[0] += 1
    return a

def bounds(label):
    for a in EAS.get_all_level_actors():
        if a.get_actor_label() == label:
            o, e = a.get_actor_bounds(False)
            return (o.x - e.x, o.y - e.y, o.z - e.z), (o.x + e.x, o.y + e.y, o.z + e.z)
    return None

ROOMS = {}
for r in ("B", "C", "D", "E"):
    f, c = bounds(f"{r}_Floor"), bounds(f"{r}_Ceiling")
    if f and c:
        ROOMS[r] = (f, c)
log("rooms:", sorted(ROOMS))

def inside_room(x, y):
    for r, (f, c) in ROOMS.items():
        if f[0][0] < x < f[1][0] and f[0][1] < y < f[1][1]:
            return r
    return None

# ---- floors and ceilings: big tiles (1.5x kit size) to keep the actor and triangle count sane
TW, TL = 450.0, 600.0
for r, (f, c) in ROOMS.items():
    (x0, y0, _), (x1, y1, ftop) = f
    cbot = c[0][2]
    nx, ny = max(1, round((x1 - x0) / TW)), max(1, round((y1 - y0) / TL))
    dx, dy = (x1 - x0) / nx, (y1 - y0) / ny
    for i in range(nx):
        for j in range(ny):
            ax, ay = x0 + i * dx, y0 + j * dy
            fit(f"{r}_EtherFloor_{i}_{j}", FLOORS[(i + j) % len(FLOORS)], (ax, ay, ftop - 10), (ax + dx, ay + dy, ftop + 2), 0.0, False)
            fit(f"{r}_EtherCeil_{i}_{j}", CEILS[(i * 3 + j) % len(CEILS)], (ax, ay, cbot - 30), (ax + dx, ay + dy, cbot + 4), 0.0, False)

# ---- walls: panel every room-facing face of every wall cube
SKIP = ("Glazing", "DarkGlass", "D_Wall_South")
DEPTH = 16.0
walls = [a for a in EAS.get_all_level_actors()
         if a.get_actor_label()[:2] in ("B_", "C_", "D_", "E_") and "_Wall" in a.get_actor_label()
         and not any(s in a.get_actor_label() for s in SKIP) and isinstance(a, unreal.StaticMeshActor)
         and str(a.get_folder_path()) != FOLDER]
nwall = 0
for a in walls:
    lab = a.get_actor_label()
    o, e = a.get_actor_bounds(False)
    zlo, zhi = o.z - e.z, o.z + e.z
    along_x = e.x > e.y
    for s in (-1, 1):
        if along_x:
            face = o.y + s * e.y
            room = inside_room(o.x, face + s * 60)
        else:
            face = o.x + s * e.x
            room = inside_room(face + s * 60, o.y)
        if not room:
            continue
        cb = ROOMS[room][1][0][2]
        top = min(zhi, cb)
        bot = max(zlo, ROOMS[room][0][1][2])
        if top - bot < 60:
            continue
        L0, L1 = (o.x - e.x, o.x + e.x) if along_x else (o.y - e.y, o.y + e.y)
        n = max(1, round((L1 - L0) / 300.0))
        seg = (L1 - L0) / n
        if along_x:
            yaw = 0.0 if (s * WALL_FRONT) > 0 else 180.0
        else:
            yaw = -90.0 if (s * WALL_FRONT) > 0 else 90.0
        d0, d1 = sorted((face, face + s * DEPTH))
        for k in range(n):
            u0, u1 = L0 + k * seg, L0 + (k + 1) * seg
            lo = (u0, d0, bot) if along_x else (d0, u0, bot)
            hi = (u1, d1, top) if along_x else (d1, u1, top)
            fit(f"{lab}_Ether{'P' if s > 0 else 'N'}{k}", WALLS[(k + nwall) % len(WALLS)], lo, hi, yaw)
        nwall += 1
log("wall faces panelled:", nwall)

# ---- a few props: atrium planters along the glazing, holo table in the antechamber approach, consoles in the sim suite
if PLANT and "B" in ROOMS:
    for k, x in enumerate((3900, 4700, 5500)):
        fit(f"B_EtherPlanter_{k}", PLANT, (x - 112, 960, 0), (x + 112, 1050, 75), 0.0)
if CONSOLE and "C" in ROOMS:
    for k, (x, y, yaw) in enumerate(((6450, -800, -90.0), (6450, 800, -90.0))):
        fit(f"C_EtherConsole_{k}", CONSOLE, (x - 30, y - 39, 0), (x + 30, y + 39, 155), yaw)
if LIGHTSTRIP and "D" in ROOMS:
    (x0, y0, _), (x1, y1, _) = ROOMS["D"][0]
    cb = ROOMS["D"][1][0][2]
    for k in range(int((x1 - x0) // 600)):
        x = x0 + 300 + k * 600
        fit(f"D_EtherStrip_{k}", LIGHTSTRIP, (x - 113, -11, cb - 34), (x + 113, 11, cb - 31), 0.0, False)

log("ether actors:", count[0])
LES.save_current_level()
open(unreal.Paths.project_saved_dir() + "NV_l1_crown_etherion.txt", "w").write("\n".join(OUT))
