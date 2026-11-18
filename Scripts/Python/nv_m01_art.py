"""M01 Black Protocol art pass over the graybox (run after nv_setup_m01.py; nv_vo_hook.py M01 is not affected).

Gameplay geometry stays as it is (collision, triggers, navmesh); kit meshes are laid over the visible faces with no
collision and no shadow casting (the 8 GB GPU is at its video-memory limit in this map: see Scripts/BUILD_NOTES.md).
  B artery + lift lobby  Etherion (ModularScifiInterior) floor/ceiling/wall panels, Clinic server stacks for the racks,
                         Etherion crates for cover, a console for the reroute terminal, ceiling light strips
  C shaft                Etherion panels stacked up the 51 m walls, safety rails on the ledges, red work lights
  D medical              Clinic kit: tiled floor, steel walls, ceiling, medical machines, ceiling lights
  E conduit              Etherion shell, SciFI_Lite pipe runs along walls and ceiling, pipe banks, gas tanks, crates
  F spillway             wet concrete, rails, outflow pipes, rain
Idempotent: wipes folder M01_Art / tag NVM01ART first. Report: Saved/NV_m01_art.txt"""
import math
import unreal

EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
LES = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
UES = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
OUT = []
def log(*a): OUT.append(" ".join(str(x) for x in a))
V = unreal.Vector
MAP = "/Game/NeonVeil/Maps/M00/L_M00_GlassCrown"
if not UES.get_editor_world().get_path_name().startswith(MAP):
    LES.load_level(MAP)

FOLDER, TAG = "M01_Art", "NVM01ART"
for a in list(EAS.get_all_level_actors()):
    if TAG in [str(t) for t in a.tags]:
        EAS.destroy_actor(a)
ACT = {a.get_actor_label(): a for a in EAS.get_all_level_actors()}

def M(p):
    m = unreal.load_asset(p)
    if not m:
        log("MISSING", p)
    return m
K = "/Game/ModularScifiInterior/Meshes"
WALLS = [M(f"{K}/Walls/SM_Wall_D_A"), M(f"{K}/Walls/SM_Wall_D_B")]
FLOORS = [M(f"{K}/FloorsAndCeilings/SM_Floor_A"), M(f"{K}/FloorsAndCeilings/SM_Floor_B")]
CEILS = [M(f"{K}/FloorsAndCeilings/SM_Ceiling_A"), M(f"{K}/FloorsAndCeilings/SM_Ceiling_B")]
DOORFRAME = M(f"{K}/Doors/SM_DoorFrame_A")
CONSOLE = M(f"{K}/Props/SM_Console")
CRATE_A = M(f"{K}/Props/SM_Crate_A")
CRATE_B = M(f"{K}/Props/SM_Crate_B")
LIGHTSTRIP = M(f"{K}/Props/SM_Light_A")
CL = "/Game/Clinic/Meshes"
STACKS = M(f"{CL}/SM_Stacks")
TILEGROUND = M(f"{CL}/SM_Room_TileGround")
STEELWALL = M(f"{CL}/SM_Room_SteelWall01")
CLCEIL = M(f"{CL}/Modular/SM_Room_Ceiling")
MEDMACHINE = M(f"{CL}/Props/SM_RoomMedicalMachine_Machine")
MEDCONTROL = M(f"{CL}/Props/SM_RoomMedicalMachine_Control")
CLLIGHT = M(f"{CL}/Props/SM_Room_CelingLight01")
WORKTABLE = M(f"{CL}/Props/SM_RoomWorkTable_Table")
MAPMACHINE = M(f"{CL}/Props/SM_RoomMapMachine_Machine")
MAPCONTROL = M(f"{CL}/Props/SM_RoomMapMachine_Control")
OFFICETABLE = M(f"{CL}/Props/SM_Room_OfficeTable")
CTRLMONITOR = M(f"{CL}/Props/SM_RoomWorkTable_ControlMonitor01")
POWERCOL = M(f"{CL}/Props/SM_RoomWorkTable_MiddlePower")
WALLDECOR = M(f"{CL}/Modular/SM_RoomWall_Decor_5")
SL = "/Game/SciFI_Lite_Assets/StaticMeshes"
PIPE80 = M(f"{SL}/SM_Pipe_Straight_3m_01")
PIPE60 = M(f"{SL}/SM_Pipe_Straight_3m_02")
FENCE = M(f"{SL}/SM_Fence_01")
GASTANK = M(f"{SL}/SM_GasTankHolder_01")
BEACON = M("/Game/Sci_Fi_Light/Static_Meshes/SM_Sci_Fi_Heavy_Duty_Linear_Beacon/Mesh/SM_Sci_Fi_Heavy_Duty_Linear_Beacon")
CSTRIP = M("/Game/Sci_Fi_Light/Static_Meshes/SM_Sci_Fi_Corridor_Ceiling_Strip/Mesh/SM_Sci_Fi_Corridor_Ceiling_Strip")
WALL_FRONT = 1   # the Etherion panel's detailed face looks down local +Y (as in nv_l1_crown_etherion.py)
count = [0]

def fit(label, mesh, lo, hi, yaw=0.0, mat=None):
    """Place `mesh` so its (yawed) local bounds fill the world AABB lo..hi. yaw in multiples of 90."""
    if not mesh:
        return None
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
    a = EAS.spawn_actor_from_class(unreal.StaticMeshActor, V(tc[0] - wx, tc[1] - wy, tc[2] - oz), unreal.Rotator(roll=0, pitch=0, yaw=yaw))
    c = a.static_mesh_component
    c.set_static_mesh(mesh)
    a.set_actor_scale3d(V(sx, sy, sz))
    c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    c.set_cast_shadow(False)
    if mat:
        for i in range(c.get_num_materials()):
            c.set_material(i, mat)
    a.set_actor_label(label)
    a.set_folder_path(FOLDER)
    a.tags = [unreal.Name(TAG)]
    count[0] += 1
    return a

def hide_visual(label):
    a = ACT.get(label)
    if a and isinstance(a, unreal.StaticMeshActor):
        a.static_mesh_component.set_visibility(False)
        return a
    return None

def aabb(label):
    a = ACT.get(label)
    if not a:
        return None
    o, e = a.get_actor_bounds(False)
    return (o.x - e.x, o.y - e.y, o.z - e.z), (o.x + e.x, o.y + e.y, o.z + e.z)

# rooms: interior AABB (x0, x1, y0, y1, floor top, ceiling bottom), kit
ROOMS = {
    "B": (15320, 15880, 720, 5600, 0, 430, "ether"),
    "BL": (15020, 16180, 5620, 6580, 0, 430, "ether"),
    "C": (15220, 16380, 6620, 7380, -4500, 600, "ether"),
    "D": (16420, 18780, 6120, 7880, -4500, -3900, "clinic"),
    "E": (18820, 27800, 6520, 7480, -4500, -4000, "ether"),
}
def room_at(x, y, z):
    for r, (x0, x1, y0, y1, zf, zc, _) in ROOMS.items():
        if x0 < x < x1 and y0 < y < y1 and zf - 50 < z < zc + 50:
            return r
    return None

# ---------------------------------------------------------------- floors and ceilings
for r, (x0, x1, y0, y1, zf, zc, kit) in ROOMS.items():
    if kit == "clinic":
        nx, ny = max(1, round((x1 - x0) / 1000)), max(1, round((y1 - y0) / 1800))
        dx, dy = (x1 - x0) / nx, (y1 - y0) / ny
        for i in range(nx):
            for j in range(ny):
                fit(f"{r}_ClinicFloor_{i}_{j}", TILEGROUND, (x0 + i * dx, y0 + j * dy, zf), (x0 + (i + 1) * dx, y0 + (j + 1) * dy, zf + 2))
        nx, ny = max(1, round((x1 - x0) / 300)), max(1, round((y1 - y0) / 300))
        dx, dy = (x1 - x0) / nx, (y1 - y0) / ny
        for i in range(nx):
            for j in range(ny):
                fit(f"{r}_ClinicCeil_{i}_{j}", CLCEIL, (x0 + i * dx, y0 + j * dy, zc - 45), (x0 + (i + 1) * dx, y0 + (j + 1) * dy, zc))
        continue
    TW, TL = 300.0, 400.0
    nx, ny = max(1, round((x1 - x0) / TW)), max(1, round((y1 - y0) / TL))
    dx, dy = (x1 - x0) / nx, (y1 - y0) / ny
    for i in range(nx):
        for j in range(ny):
            ax, ay = x0 + i * dx, y0 + j * dy
            fit(f"{r}_Floor_{i}_{j}", FLOORS[(i + j) % 2], (ax, ay, zf - 10), (ax + dx, ay + dy, zf + 2))
            if r != "C":
                fit(f"{r}_Ceil_{i}_{j}", CEILS[(i * 3 + j) % 2], (ax, ay, zc - 30), (ax + dx, ay + dy, zc + 4))
log("floors/ceilings done", count[0])

# ---------------------------------------------------------------- walls (every M01 graybox wall face that looks into a room)
DEPTH = 16.0
nwall = 0
for a in list(ACT.values()):
    if not isinstance(a, unreal.StaticMeshActor) or not str(a.get_folder_path()).startswith("M01_"):
        continue
    lab = a.get_actor_label()
    if not any(k in lab for k in ("Wall", "_North", "_South", "_East", "_West", "Lobby_", "C_South", "C_North", "D_Bay")):
        continue
    o, e = a.get_actor_bounds(False)
    if min(e.x, e.y) > 40:      # not a wall
        continue
    zlo, zhi = o.z - e.z, o.z + e.z
    along_x = e.x > e.y
    for s in (-1, 1):
        if along_x:
            face = o.y + s * e.y
            room = room_at(o.x, face + s * 60, o.z)
        else:
            face = o.x + s * e.x
            room = room_at(face + s * 60, o.y, o.z)
        if not room:
            continue
        x0, x1, y0, y1, zf, zc, kit = ROOMS[room]
        top, bot = min(zhi, zc), max(zlo, zf)
        if top - bot < 60:
            continue
        L0, L1 = (max(o.x - e.x, x0), min(o.x + e.x, x1)) if along_x else (max(o.y - e.y, y0), min(o.y + e.y, y1))
        if L1 - L0 < 40:
            continue
        seg_len = 409.0 if kit == "clinic" else 300.0
        mesh_list = [STEELWALL] if kit == "clinic" else WALLS
        n = max(1, round((L1 - L0) / seg_len))
        seg = (L1 - L0) / n
        rows = max(1, round((top - bot) / 450.0))
        rh = (top - bot) / rows
        if along_x:
            yaw = 0.0 if (s * WALL_FRONT) > 0 else 180.0
        else:
            yaw = -90.0 if (s * WALL_FRONT) > 0 else 90.0
        d0, d1 = sorted((face, face + s * (6.0 if kit == "clinic" else DEPTH)))
        for k in range(n):
            u0, u1 = L0 + k * seg, L0 + (k + 1) * seg
            for q in range(rows):
                b0, b1 = bot + q * rh, bot + (q + 1) * rh
                lo = (u0, d0, b0) if along_x else (d0, u0, b0)
                hi = (u1, d1, b1) if along_x else (d1, u1, b1)
                fit(f"{lab}_Art{'P' if s > 0 else 'N'}{k}_{q}", mesh_list[(k + q + nwall) % len(mesh_list)], lo, hi, yaw)
        nwall += 1
log("wall faces panelled:", nwall, "actors so far", count[0])

# ---------------------------------------------------------------- B artery props
for side in ("W", "E"):
    for j in range(5):
        bb = aabb(f"B_Rack_{side}{j}")
        if bb and STACKS:
            hide_visual(f"B_Rack_{side}{j}")
            (lx, ly, lz), (hx, hy, hz) = bb
            # SM_Stacks runs along its local -Y, like the rack (world Y): no swap; the east row is turned to face the aisle
            fit(f"B_Stacks_{side}{j}", STACKS, (lx, ly, 0), (hx, hy, 300), 0.0 if side == "W" else 180.0)
for j in range(3):
    bb = aabb(f"B_Cover_{j}")
    if bb:
        hide_visual(f"B_Cover_{j}")
        (lx, ly, lz), (hx, hy, hz) = bb
        fit(f"B_CoverCrate_{j}", CRATE_A, (lx, ly, 0), (hx, hy, hz))
term = ACT.get("B_Terminal_Reroute")
if term and CONSOLE:
    m = term.get_editor_property("mesh")
    m.set_static_mesh(CONSOLE)
    m.set_editor_property("relative_scale3d", V(1, 1, 1))
    m.set_editor_property("relative_location", V(0, 0, -120))
    for i in range(m.get_num_materials()):
        m.set_material(i, None)
for k, y in enumerate(range(1100, 5600, 1100)):
    fit(f"B_CeilStrip_{k}", LIGHTSTRIP, (15600 - 113, y - 11, 425), (15600 + 113, y + 11, 428))
if DOORFRAME:
    fit("BL_LiftFrame", DOORFRAME, (15210, 6560, 0), (15790, 6600, 470), 90.0)
    fit("A_EmergencyFrame", DOORFRAME, (15440, 690, 0), (15760, 730, 340), 90.0)
for k, x in enumerate((15200, 16000)):
    fit(f"BL_Crate_{k}", CRATE_B, (x - 25, 6450, 0), (x + 25, 6500, 71))

# emergency beacons on the A lockdown lights, ceiling strips over the lift lobby
for i in range(8):
    em = ACT.get(f"A_Emergency_{i}")
    if em:
        p = em.get_actor_location()
        fit(f"A_Beacon_{i}", BEACON, (p.x - 51, p.y - 3, p.z - 18), (p.x + 51, p.y + 3, p.z + 18))
for k, x in enumerate((15300, 15600, 15900)):
    fit(f"BL_CeilStrip_{k}", CSTRIP, (x - 45, 6100 - 25, 411), (x + 45, 6100 + 12, 430), 180.0)

# ---------------------------------------------------------------- C shaft
for k, (label, y0, y1) in enumerate((("C_Ledge_P1", 6620, 7040), ("C_Ledge_P2", 7080, 7380))):
    bb = aabb(label)
    if bb and FENCE:
        (lx, ly, lz), (hx, hy, hz) = bb
        fit(f"C_Rail_{k}", FENCE, (hx - 280, hy - 14, hz), (hx, hy + 14, hz + 110), 0.0)
# ledges: Etherion deck plates over the hazard-orange graybox (collision stays on the hidden box)
for label in ("C_Ledge_P1", "C_Ledge_P2", "C_Ledge_P3"):
    bb = aabb(label)
    if bb:
        hide_visual(label)
        (lx, ly, lz), (hx, hy, hz) = bb
        fit(f"{label}_Deck", FLOORS[0], (lx, ly, lz), (hx, hy, hz))
for k, z in enumerate((-600, -1700, -2600, -3500, -4300)):
    fit(f"C_WorkLamp_{k}", BEACON, (16330 - 51, 7375, z - 18), (16330 + 51, 7381, z + 18), 180.0)

# ---------------------------------------------------------------- D medical (Clinic)
for k, (label) in enumerate(("D_Gurney_0", "D_Gurney_1", "D_Gurney_2", "D_Gurney_3")):
    bb = aabb(label)
    if bb:
        hide_visual(label)
        (lx, ly, lz), (hx, hy, hz) = bb
        cx, cy = (lx + hx) / 2, (ly + hy) / 2
        fit(f"D_MedMachine_{k}", MEDMACHINE, (cx - 51, cy - 109, -4500), (cx + 51, cy + 109, -4500 + 239), 90.0)
        fit(f"D_MedControl_{k}", MEDCONTROL, (cx - 95, cy + (140 if cy < 7000 else -205), -4500),
            (cx + 95, cy + (205 if cy < 7000 else -140), -4500 + 95), 0.0 if cy < 7000 else 180.0)
bb = aabb("D_TagTray")
if bb and WORKTABLE:
    hide_visual("D_TagTray")
    (lx, ly, lz), (hx, hy, hz) = bb
    fit("D_TagTable", WORKTABLE, (lx - 30, ly - 20, -4500), (hx + 30, hy + 20, hz), 0.0)
for i, (x, y) in enumerate(((16650, 7000), (17600, 6600), (17600, 7400), (18400, 7000), (17200, 7000))):
    fit(f"D_CeilLight_{i}", CLLIGHT, (x - 31, y - 31, -3912 - 12), (x + 31, y + 31, -3912))

# clutter: a holo-map station, a records desk, monitors at the tag table, power columns, wall panels, accent light
fit("D_MapMachine", MAPMACHINE, (16850, 6250, -4500), (17162, 6562, -4417))
fit("D_MapControl", MAPCONTROL, (17180, 6260, -4500), (17244, 6352, -4400), 90.0)
fit("D_RecordsDesk", OFFICETABLE, (18500, 6150, -4500), (18766, 6559, -4385))
fit("D_TagMonitor", CTRLMONITOR, (17270, 7080, -4500), (17333, 7204, -4373))
for i, (x, y) in enumerate(((16960, 7840), (18740, 7840), (18740, 6160), (16960, 6160))):
    fit(f"D_PowerCol_{i}", POWERCOL, (x - 26, y - 26, -4500), (x + 26, y + 26, -4360))
for i, (y0, y1) in enumerate(((6300, 6500), (6600, 6800), (7200, 7400), (7500, 7700))):
    fit(f"D_WallDecor_{i}", WALLDECOR, (18740, y0, -4500), (18780, y1, -4100), 180.0)
for i, (x, y) in enumerate(((17000, 7840), (18000, 6160))):
    pl = EAS.spawn_actor_from_class(unreal.PointLight, V(x, y, -4200))
    lc = pl.point_light_component
    lc.set_intensity(1000)
    lc.set_attenuation_radius(700)
    lc.set_light_color(unreal.LinearColor(0.1, 0.85, 1.0, 1))
    lc.set_cast_shadows(False)
    pl.set_actor_label(f"D_Accent_{i}")
    pl.set_folder_path(FOLDER)
    pl.tags = [unreal.Name(TAG)]

# ---------------------------------------------------------------- E conduit
for j in range(4):
    bb = aabb(f"E_PipeBank_{j}")
    if bb and PIPE80:
        hide_visual(f"E_PipeBank_{j}")
        (lx, ly, lz), (hx, hy, hz) = bb
        # junction boxes cap both ends so the open pipe mouths never face the player
        fit(f"E_BankCapW_{j}", CRATE_A, (lx, ly, lz), (lx + 60, hy, hz), 90.0)
        fit(f"E_BankCapE_{j}", CRATE_A, (hx - 60, ly, lz), (hx, hy, hz), 90.0)
        px0, px1 = lx + 50, hx - 50
        n = max(1, round((px1 - px0) / 300))
        dx = (px1 - px0) / n
        for i in range(n):
            for r, (yy, zz) in enumerate(((ly + 35, lz + 40), (hy - 35, lz + 40), ((ly + hy) / 2, lz + 115))):
                fit(f"E_Bank{j}_{i}_{r}", PIPE80, (px0 + i * dx, yy - 35, zz - 35), (px0 + (i + 1) * dx, yy + 35, zz + 35))
for j in range(6):
    bb = aabb(f"E_Crate_{j}")
    if bb:
        hide_visual(f"E_Crate_{j}")
        (lx, ly, lz), (hx, hy, hz) = bb
        fit(f"E_Tank_{j}", GASTANK if j % 2 == 0 else CRATE_A, (lx, ly, lz), (hx, hy, hz))
# pipe runs high on both walls and along the ceiling
n = int((27800 - 18800) // 300)
for i in range(n):
    x0 = 18800 + i * 300
    fit(f"E_WallPipeN_{i}", PIPE60, (x0, 7380, -4140), (x0 + 300, 7440, -4080))
    fit(f"E_WallPipeS_{i}", PIPE60, (x0, 6560, -4140), (x0 + 300, 6620, -4080))
    if i % 2 == 0:
        fit(f"E_CeilPipe_{i}", PIPE80, (x0, 6880, -4085), (x0 + 300, 6960, -4005))

# ---------------------------------------------------------------- F spillway
for k, y in enumerate((6560, 7440)):
    for i in range(int((31600 - 29000) // 280)):
        x0 = 29000 + i * 280
        fit(f"F_Rail_{k}_{i}", FENCE, (x0, y - 14, -5000), (x0 + 280, y + 14, -4884), 0.0)
for k, y in enumerate((6800, 7200)):
    fit(f"F_OutflowCap_{k}", CRATE_B, (27860, y - 45, -4710), (27900, y + 45, -4610))
    fit(f"F_Outflow_{k}", PIPE80, (27900, y - 40, -4700), (28200, y + 40, -4620))
src = ACT.get("RainNear_TramS")
if src:
    rain = EAS.duplicate_actor(src)
    rain.set_actor_location(V(30000, 7000, -4300), False, False)
    rain.set_actor_label("F_Rain")
    rain.set_folder_path(FOLDER)
    rain.tags = [unreal.Name(TAG)]
    try:
        rain.set_editor_property("extent", V(1900, 520, 800))
        rain.set_editor_property("count", 1600)
    except Exception as e:
        log("rain props", e)
    log("rain placed")

# ---------------------------------------------------------------- B crawlway (Underground Sci-Fi, GeorgeShachnev, Fab)
# interior x 15100..15280, y 1520..5600, z 0..150; entered through the cut in the artery's west wall at y 1520..1680
U = "/Game/UndergroundSciFi/Meshes"
PANELS = [M(f"{U}/SM_Cube_1m")]
UFLOOR = M(f"{U}/SM_Bunker_Floor02_1m")
WIRES = M(f"{U}/SM_Wires01")
FAN = M(f"{U}/SM_Bunker_Fan")
FANFRAME = M(f"{U}/SM_Bunker_FanFrame")
LAMP = M(f"{U}/SM_Lamp01")
BORDER = M(f"{U}/SM_FloorWall_Border")
CX0, CX1, CY0, CY1, CZ1 = 15100.0, 15280.0, 1520.0, 5600.0, 150.0
PANEL_FRONT = 1          # flip to -1 if the panels show their backs
n = int((CY1 - CY0) // 100)
dy = (CY1 - CY0) / n
for i in range(n):
    y0 = CY0 + i * dy
    fit(f"BC_Floor_{i}", UFLOOR, (CX0, y0, -1), (CX1, y0 + dy, 1))
    fit(f"BC_Ceil_{i}", CEILS[i % 2], (CX0, y0, CZ1 - 24), (CX1, y0 + dy, CZ1 + 4))
    entrance = y0 < 1690          # keep the cut into the artery clear
    if i % 3 == 0:
        # Etherion wall panels (same family as the artery), three tiles wide, squashed to crawl height
        w0, w1 = y0, min(CY1, y0 + 3 * dy)
        fit(f"BC_PanelW_{i}", WALLS[(i // 3) % 2], (CX0, w0, 0), (CX0 + 12, w1, CZ1), 90.0 * WALL_FRONT)
        if w0 > 1690:
            fit(f"BC_PanelE_{i}", WALLS[(i // 3 + 1) % 2], (CX1 - 12, w0, 0), (CX1, w1, CZ1), -90.0 * WALL_FRONT)
fit("BC_PanelS", WALLS[0], (CX0, CY0, 0), (CX1, CY0 + 12, CZ1), 180.0 if WALL_FRONT > 0 else 0.0)
# floor trim both sides, cable looms along the top corners, a low pipe on the west side
for i in range(int((CY1 - CY0) // 300)):
    y0 = CY0 + i * 300
    fit(f"BC_TrimW_{i}", BORDER, (CX0 + 6, y0, 0), (CX0 + 22, y0 + 300, 14), 90.0)
    if y0 > 1690:
        fit(f"BC_TrimE_{i}", BORDER, (CX1 - 22, y0, 0), (CX1 - 6, y0 + 300, 14), -90.0)
    fit(f"BC_PipeW_{i}", PIPE60, (CX0 + 8, y0, 24), (CX0 + 38, y0 + 300, 54), 90.0)
for i in range(int((CY1 - CY0) // 200)):
    y0 = CY0 + i * 200
    for k, x in enumerate((CX0 + 14, CX1 - 14)):
        w = EAS.spawn_actor_from_class(unreal.StaticMeshActor, V(x, y0, CZ1 - 34), unreal.Rotator(roll=-90.0, pitch=0.0, yaw=0.0))
        w.static_mesh_component.set_static_mesh(WIRES)
        w.set_actor_scale3d(V(1.0, 1.0, 2.0))
        w.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
        w.static_mesh_component.set_cast_shadow(False)
        w.set_actor_label(f"BC_Wires_{k}_{i}")
        w.set_folder_path(FOLDER)
        w.tags = [unreal.Name(TAG)]
        count[0] += 1
# extraction fans set into the west wall, each with an amber light and a caged lamp above
for k, y in enumerate((2600, 3800, 5000)):
    fit(f"BC_FanFrame_{k}", FANFRAME, (CX0, y - 60, 15), (CX0 + 8, y + 60, 135), 90.0)
    fit(f"BC_Fan_{k}", FAN, (CX0 + 1, y - 55, 20), (CX0 + 3, y + 55, 130), 90.0)
    fit(f"BC_Lamp_{k}", LAMP, (15190 - 15, y + 300 - 15, CZ1 - 40), (15190 + 15, y + 300 + 15, CZ1 - 1))
    pl = EAS.spawn_actor_from_class(unreal.PointLight, V(15190, y + 300, CZ1 - 45))
    lc = pl.point_light_component
    lc.set_intensity(260)
    lc.set_attenuation_radius(420)
    lc.set_light_color(unreal.LinearColor(1.0, 0.55, 0.18, 1))
    lc.set_cast_shadows(False)
    pl.set_actor_label(f"BC_LampLight_{k}")
    pl.set_folder_path(FOLDER)
    pl.tags = [unreal.Name(TAG)]
for lab, a in ACT.items():
    if lab.startswith(("B_Crawl_Ceil", "B_Crawl_W", "B_Crawl_S")) and isinstance(a, unreal.StaticMeshActor):
        a.static_mesh_component.set_visibility(False)

log("art actors:", count[0])
LES.save_current_level()
open(unreal.Paths.project_saved_dir() + "NV_m01_art.txt", "w", encoding="utf-8").write("\n".join(OUT))
unreal.log("NV_M01_ART done")
