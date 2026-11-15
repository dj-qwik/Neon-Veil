"""Veyra Central as a building, not a panel; street traffic that docks instead of flying through towers; full lift doors.

- Hub mass: the facade was one flat 64 x 128 m wall of panels. Add side returns and a roof (shallow, 16 m, so the
  lift's east glass still looks out over the city), structural pilasters standing proud of the face, slab ledges every
  three floors, a lit/unlit window grid, and a stepped crown with a beacon mast.
- Traffic: the two street lanes (Sky_Street_A/B) ran 2.2 km straight through the hub facade and the NYG tower at the
  south end. They now run between the two buildings and dock into lit skyport gates cut into each face (dark recess +
  glowing frame), so cars fly in and out of the buildings. Neon bands that crossed a gate are split around it.
- Lift doors: the landing doors only slid 115 cm; open them by their measured panel width.
Idempotent (folder P_HubBuilding / tag NVHB). Saves the level. Report: Saved/NV_hub_building.txt"""
import random
import unreal
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
LES = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
EAL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary
AT = unreal.AssetToolsHelpers.get_asset_tools()
V = unreal.Vector
OUT = []
def log(*a):
    OUT.append(" ".join(str(x) for x in a))

ZS = -12000.0
FRONT_Y = -6614.0          # front face of the hub facade panels (actor plane -6564, 50 cm thick); street side is -Y
X_W, X_E = 3870.0, 10220.0 # facade edges
NROWS = int((400 - ZS) / 400) + 1
Z_TOP = ZS + NROWS * 400.0
DEPTH = 1600.0             # depth of the west part (keeps clear of the lift shaft at y -4730..-4250)
FOLDER, TAG = "P_HubBuilding", "NVHB"
CUBE = unreal.load_asset("/Engine/BasicShapes/Cube")
MATDIR = "/Game/NeonVeil/Materials/Prologue"
DARK = unreal.load_asset(f"{MATDIR}/MI_NV_HubFacade_Night") or unreal.load_asset("/Game/SciFiTramStation/Materials/MI_Trim_B")
TRIM = unreal.load_asset("/Game/SciFiTramStation/Materials/MI_Trim_B")
GL_CYAN = unreal.load_asset(f"{MATDIR}/MI_NV_Glow_Cyan")
GL_MAG = unreal.load_asset(f"{MATDIR}/MI_NV_Glow_Magenta")
GL_AMBER = unreal.load_asset(f"{MATDIR}/MI_NV_Glow_Amber")
M_GLOW = unreal.load_asset(f"{MATDIR}/M_NV_Glow")

def glow_mi(name, color, glow):
    path = f"{MATDIR}/{name}"
    mi = unreal.load_asset(path) if EAL.does_asset_exist(path) else AT.create_asset(name, MATDIR, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    MEL.set_material_instance_parent(mi, M_GLOW)
    MEL.set_material_instance_vector_parameter_value(mi, "Color", unreal.LinearColor(*color, 1))
    MEL.set_material_instance_scalar_parameter_value(mi, "Glow", glow)
    EAL.save_loaded_asset(mi)
    return mi
WIN_WARM = glow_mi("MI_NV_Glow_WindowWarm", (1.0, 0.62, 0.32), 1.6)
WIN_COOL = glow_mi("MI_NV_Glow_WindowCool", (0.45, 0.75, 1.0), 1.3)
WIN_DIM = glow_mi("MI_NV_Glow_WindowDim", (0.25, 0.35, 0.5), 0.35)
VOID = glow_mi("MI_NV_Glow_Void", (0.05, 0.25, 0.4), 0.6)   # dim cyan skyport membrane
BEACON = glow_mi("MI_NV_Glow_Beacon", (1.0, 0.05, 0.04), 14.0)

# ------------------------------------------------------------------ clean previous run
for a in list(EAS.get_all_level_actors()):
    if TAG in [str(t) for t in a.tags]:
        EAS.destroy_actor(a)

def box(label, center, size, mat):
    a = EAS.spawn_actor_from_object(CUBE, V(*center), unreal.Rotator())
    a.set_actor_label(label); a.set_folder_path(FOLDER); a.tags = [unreal.Name(TAG)]
    a.set_actor_scale3d(V(size[0] / 100.0, size[1] / 100.0, size[2] / 100.0))
    c = a.static_mesh_component
    c.set_material(0, mat)
    c.set_editor_property("cast_shadow", size[2] > 2000 or size[0] > 2000)
    return a

# ------------------------------------------------------------------ traffic: two one-way tubes per lane
# Each street lane is split into two one-way streams that run through real tunnels, one either side of the lift shaft
# line (shaft x 6806..7286): northbound in the east tube, southbound in the west tube. The hub tunnels run back into
# the building and end at lit dock walls (cars slide into / out of the dock), so nothing passes the lift. The east part
# of the building is shallow (EAST_DEPTH) and the east tube ends with it, so the lift's glass (facing east) looks out
# past the building instead of at it. At the tower end the tubes stand proud of the tower face as lit shrouds.
SOUTH_FACE = -23000 + 2806 + 40     # NYG tower north face (+ a hair)
EAST_DEPTH = 700.0                  # building depth east of the shaft (west part keeps DEPTH)
SHAFT_X0, SHAFT_X1 = 6806.0, 7286.0
TUBE_W, TUBE_H = 1300.0, 950.0      # inner opening
TUBES = {"W": 6046.0, "E": 8046.0}  # tube centre x
BACK = {"W": FRONT_Y + DEPTH - 60, "E": FRONT_Y + EAST_DEPTH - 60}   # dock wall plane inside the hub
GATES = []                          # (x, z, half width, half height) incl. frame, for splitting facade dressing
OPENINGS = []                       # inner openings (x0, x1, z0, z1) on the hub face
streams = {a.get_actor_label(): a for a in EAS.get_all_level_actors() if isinstance(a, unreal.NVTrafficStream)}
for lane, z, sy, seed in (("A", ZS + 4200, 260.0, 21), ("B", ZS + 7600, 320.0, 22)):
    src = streams.get(f"Sky_Street_{lane}")
    if not src:
        log("missing", lane); continue
    north = src
    south = streams.get(f"Sky_Street_{lane}_S")
    if not south:
        south = EAS.spawn_actor_from_class(unreal.NVTrafficStream, V(0, 0, z), unreal.Rotator())
        south.set_actor_label(f"Sky_Street_{lane}_S"); south.set_folder_path(str(src.get_folder_path())); south.tags = list(src.tags)
        for prop in ("vehicle_mesh", "speed_range", "vehicle_scale"):
            south.set_editor_property(prop, src.get_editor_property(prop))
        south.set_editor_property("forward_material", src.get_editor_property("reverse_material"))
        south.set_editor_property("seed", seed + 100)
    for st, tube, yaw in ((north, "E", 90.0), (south, "W", -90.0)):
        st.set_editor_property("two_way", False)
        st.set_editor_property("lane_spread", unreal.Vector2D(320.0, sy * 0.8))
        st.set_editor_property("vehicles_per_direction", 9 if lane == "A" else 7)
        y_in, y_out = BACK[tube] + 150, SOUTH_FACE - 300           # dock (inside the hub) / inside the tower
        if yaw > 0:
            st.set_actor_location_and_rotation(V(TUBES[tube], y_out, z), unreal.Rotator(roll=0, pitch=0, yaw=yaw), False, False)
        else:
            st.set_actor_location_and_rotation(V(TUBES[tube], y_in, z), unreal.Rotator(roll=0, pitch=0, yaw=yaw), False, False)
        st.set_editor_property("lane_length", y_in - y_out)
        log(f"{st.get_actor_label()}: tube {tube} x {TUBES[tube]:.0f} z {z:.0f} {'north' if yaw > 0 else 'south'}bound, {(y_in - y_out) / 100:.0f} m")
    for tube, x in TUBES.items():
        GATES.append((x, z, TUBE_W / 2 + 60, TUBE_H / 2 + 60))
        OPENINGS.append((x - TUBE_W / 2, x + TUBE_W / 2, z - TUBE_H / 2, z + TUBE_H / 2))

def in_gate(x, z, pad=0.0):
    return any(abs(x - gx) < hw + pad and abs(z - gz) < hh + pad for (gx, gz, hw, hh) in GATES)

TUNNEL = glow_mi("MI_NV_Glow_TunnelDark", (0.02, 0.025, 0.035), 0.4)   # faintly self-lit lining, reads in the dark
k = 0
for (x0, x1, z0, z1), (gx, gz, _, _) in zip(OPENINGS, GATES):
    tube = "W" if gx < SHAFT_X0 else "E"
    yb = BACK[tube]
    L = yb - FRONT_Y
    yc = (FRONT_Y + yb) / 2
    w, h, t = x1 - x0, z1 - z0, 40.0
    # hub tunnel: lining, ribs every 3.5 m, guide lights, lit dock wall at the back
    box(f"Tun_{k}_Floor", (gx, yc, z0 - t / 2), (w + 2 * t, L, t), TUNNEL)
    box(f"Tun_{k}_Ceil", (gx, yc, z1 + t / 2), (w + 2 * t, L, t), TUNNEL)
    box(f"Tun_{k}_WallL", (x0 - t / 2, yc, gz), (t, L, h), TUNNEL)
    box(f"Tun_{k}_WallR", (x1 + t / 2, yc, gz), (t, L, h), TUNNEL)
    box(f"Tun_{k}_Dock", (gx, yb + t / 2, gz), (w, t, h), TRIM)
    box(f"Tun_{k}_DockGlow", (gx, yb - 2, gz), (w * 0.86, 4, h * 0.8), VOID)
    for j, yr in enumerate(range(int(FRONT_Y + 250), int(yb - 100), 350)):
        g = GL_CYAN if j % 2 == 0 else GL_MAG
        box(f"Tun_{k}_RibT{j}", (gx, yr, z1 - 4), (w, 30, 8), g)
        box(f"Tun_{k}_RibB{j}", (gx, yr, z0 + 4), (w, 30, 8), g)
        box(f"Tun_{k}_RibL{j}", (x0 + 4, yr, gz), (8, 30, h), g)
        box(f"Tun_{k}_RibR{j}", (x1 - 4, yr, gz), (8, 30, h), g)
    box(f"Tun_{k}_Guide", (gx, yc, z0 + 2), (24, L, 4), GL_AMBER)
    # portal frame on the facade
    fr = 50
    box(f"Tun_{k}_FrT", (gx, FRONT_Y - 30, z1 + fr / 2), (w + 2 * fr, 60, fr), GL_CYAN)
    box(f"Tun_{k}_FrB", (gx, FRONT_Y - 30, z0 - fr / 2), (w + 2 * fr, 60, fr), GL_CYAN)
    box(f"Tun_{k}_FrL", (x0 - fr / 2, FRONT_Y - 30, gz), (fr, 60, h), GL_AMBER)
    box(f"Tun_{k}_FrR", (x1 + fr / 2, FRONT_Y - 30, gz), (fr, 60, h), GL_AMBER)
    # tower end: a lit shroud standing 9 m proud of the tower face, membrane where it meets the face
    ty0, ty1 = SOUTH_FACE - 40, SOUTH_FACE + 860
    tyc = (ty0 + ty1) / 2
    box(f"TunT_{k}_Floor", (gx, tyc, z0 - t / 2), (w + 2 * t, ty1 - ty0, t), TUNNEL)
    box(f"TunT_{k}_Ceil", (gx, tyc, z1 + t / 2), (w + 2 * t, ty1 - ty0, t), TUNNEL)
    box(f"TunT_{k}_WallL", (x0 - t / 2, tyc, gz), (t, ty1 - ty0, h), TUNNEL)
    box(f"TunT_{k}_WallR", (x1 + t / 2, tyc, gz), (t, ty1 - ty0, h), TUNNEL)
    box(f"TunT_{k}_Membrane", (gx, ty0 + 10, gz), (w, 6, h), VOID)
    for j, yr in enumerate((ty0 + 200, ty0 + 520, ty1 - 20)):
        g = GL_CYAN if j % 2 == 0 else GL_MAG
        box(f"TunT_{k}_RibT{j}", (gx, yr, z1 + t + 6), (w + 2 * t + 20, 30, 12), g)
        box(f"TunT_{k}_RibB{j}", (gx, yr, z0 - t - 6), (w + 2 * t + 20, 30, 12), g)
        box(f"TunT_{k}_RibL{j}", (x0 - t - 6, yr, gz), (12, 30, h + 2 * t), g)
        box(f"TunT_{k}_RibR{j}", (x1 + t + 6, yr, gz), (12, 30, h + 2 * t), g)
    k += 1

# cut the openings out of the facade: hide every panel an opening touches, rebuild the rest of it as blocks
def overlaps(r, o):
    return r[0] < o[1] and o[0] < r[1] and r[2] < o[3] and o[2] < r[3]
cut = 0
for a in list(EAS.get_all_level_actors()):
    lab = a.get_actor_label()
    if not lab.startswith("Hub_Facade_"):
        continue
    o, e = a.get_actor_bounds(False)
    r = (o.x - e.x, o.x + e.x, o.z - e.z, o.z + e.z)
    hits = [op for op in OPENINGS if overlaps(r, op)]
    if not hits:
        a.set_actor_hidden_in_game(False); a.static_mesh_component.set_visibility(True)
        continue
    a.set_actor_hidden_in_game(True); a.static_mesh_component.set_visibility(False)
    a.set_actor_enable_collision(False)
    mat = a.static_mesh_component.get_material(0)
    xs = sorted({r[0], r[1]} | {v for op in hits for v in (op[0], op[1]) if r[0] < v < r[1]})
    zs = sorted({r[2], r[3]} | {v for op in hits for v in (op[2], op[3]) if r[2] < v < r[3]})
    for i in range(len(xs) - 1):
        for j in range(len(zs) - 1):
            cx, cz = (xs[i] + xs[i + 1]) / 2, (zs[j] + zs[j + 1]) / 2
            if any(op[0] < cx < op[1] and op[2] < cz < op[3] for op in hits):
                continue
            box(f"{lab}_cut{i}{j}", (cx, o.y, cz), (xs[i + 1] - xs[i], e.y * 2, zs[j + 1] - zs[j]), mat)
    cut += 1
log("facade panels cut:", cut)

# split the hub's neon bands around the openings
for a in list(EAS.get_all_level_actors()):
    lab = a.get_actor_label()
    if not lab.startswith("Hub_Band_"):
        continue
    loc = a.get_actor_location()
    hit = sorted([g for g in GATES if abs(loc.z - g[1]) < g[3] + 30])
    if not hit:
        continue
    mat = a.static_mesh_component.get_material(0)
    s = a.get_actor_scale3d()
    segs = [(loc.x - s.x * 50, loc.x + s.x * 50)]
    for gx, gz, hw, hh in hit:
        segs = [(p0, min(p1, gx - hw - 30)) for (p0, p1) in segs] + [(max(p0, gx + hw + 30), p1) for (p0, p1) in segs]
    a.set_actor_hidden_in_game(True)
    a.static_mesh_component.set_visibility(False)
    for j, (p0, p1) in enumerate(segs):
        if p1 - p0 > 50:
            box(f"{lab}_{j}", ((p0 + p1) / 2, loc.y, loc.z), (p1 - p0, s.y * 100, s.z * 100), mat)
    log("split", lab)

# ------------------------------------------------------------------ hub mass
W = X_E - X_W
H = Z_TOP - ZS
XS = SHAFT_X0 - 40                         # step in the plan: deep west part / shallow east part
box("HB_Side_W", (X_W - 20, FRONT_Y + DEPTH / 2, ZS + H / 2), (40, DEPTH, H), DARK)
box("HB_Side_E", (X_E + 20, FRONT_Y + EAST_DEPTH / 2, ZS + H / 2), (40, EAST_DEPTH, H), DARK)
box("HB_Back_W", ((X_W + XS) / 2, FRONT_Y + DEPTH, ZS + H / 2), (XS - X_W, 40, H), DARK)
box("HB_Back_E", ((XS + X_E) / 2, FRONT_Y + EAST_DEPTH, ZS + H / 2), (X_E - XS, 40, H), DARK)
box("HB_Step", (XS, FRONT_Y + (DEPTH + EAST_DEPTH) / 2, ZS + H / 2), (40, DEPTH - EAST_DEPTH, H), DARK)
box("HB_Step_Edge", (XS + 24, FRONT_Y + EAST_DEPTH + 6, ZS + H / 2), (8, 8, H), GL_AMBER)
box("HB_Roof_W", ((X_W + XS) / 2, FRONT_Y + DEPTH / 2, Z_TOP + 30), (XS - X_W + 40, DEPTH, 60), DARK)
box("HB_Roof_E", ((XS + X_E) / 2, FRONT_Y + EAST_DEPTH / 2, Z_TOP + 30), (X_E - XS + 40, EAST_DEPTH, 60), DARK)
box("HB_Parapet", ((X_W + X_E) / 2, FRONT_Y - 60, Z_TOP + 120), (W + 240, 120, 240), DARK)
box("HB_Parapet_Glow", ((X_W + X_E) / 2, FRONT_Y - 124, Z_TOP + 30), (W + 240, 6, 14), GL_CYAN)
# corner fins: deep, full height, catch the light on the edges so the block reads as a volume
for side, x in (("W", X_W - 60), ("E", X_E + 60)):
    box(f"HB_Fin_{side}", (x, FRONT_Y - 120, ZS + H / 2 + 150), (120, 360, H + 300), DARK)
    box(f"HB_Fin_{side}_Edge", (x, FRONT_Y - 304, ZS + H / 2 + 150), (14, 8, H + 300), GL_AMBER)
# pilasters every bay, proud of the face; skip the entrance canopy zone at the bottom
BAY = 800.0
cols = [X_W + BAY * i for i in range(1, int(W / BAY))]
for i, x in enumerate(cols):
    z0 = ZS + (700 if 6200 < x < 7900 else 0)
    segs = [(z0, Z_TOP)]
    for (gx, gz, hw, hh) in GATES:
        if abs(x - gx) < hw + 80:
            segs = [(a0, min(a1, gz - hh - 80)) for (a0, a1) in segs] + [(max(a0, gz + hh + 80), a1) for (a0, a1) in segs]
    for j, (a0, a1) in enumerate(segs):
        if a1 - a0 > 50:
            box(f"HB_Pilaster_{i}_{j}", (x, FRONT_Y - 70, (a0 + a1) / 2), (70, 140, a1 - a0), DARK)
# slab ledges every 3 floors (12 m)
for f in range(3, NROWS, 3):
    z = ZS + f * 400 - 40
    for part, (p0, p1) in (("", (X_W, X_E)),):
        segs = [(p0, p1)]
        for (gx, gz, hw, hh) in GATES:
            if abs(z - gz) < hh + 60:
                segs = [(a0, min(a1, gx - hw - 80)) for (a0, a1) in segs] + [(max(a0, gx + hw + 80), a1) for (a0, a1) in segs]
        for j, (a0, a1) in enumerate(segs):
            if a1 - a0 > 50:
                box(f"HB_Ledge_{f}_{j}", ((a0 + a1) / 2, FRONT_Y - 90, z), (a1 - a0, 180, 26), DARK)
# window grid: two panes per bay per floor, lit warm/cool, dim, or dark; nothing in the gates or the lobby canopy zone
rng = random.Random(9)
nw = 0
edges = [X_W] + cols + [X_E]
for f in range(2, NROWS):
    zc = ZS + f * 400 + 190
    for b in range(len(edges) - 1):
        bx0, bx1 = edges[b] + 45, edges[b + 1] - 45
        for p in range(2):
            px0 = bx0 + (bx1 - bx0) * p / 2 + 15
            px1 = bx0 + (bx1 - bx0) * (p + 1) / 2 - 15
            cx = (px0 + px1) / 2
            if in_gate(cx, zc, 180):
                continue
            r = rng.random()
            mat = WIN_WARM if r < 0.16 else WIN_COOL if r < 0.27 else WIN_DIM if r < 0.62 else None
            if mat is None:
                continue
            box(f"HB_Win_{f}_{b}_{p}", (cx, FRONT_Y - 6, zc), (px1 - px0, 4, 210), mat)
            nw += 1
log("windows:", nw, "pilasters:", len(cols), "floors:", NROWS, "top z:", Z_TOP)
# crown: stepped setbacks, a lit band per step and a beacon mast
for s, (inset, hgt) in enumerate(((500, 1200), (1400, 1000), (2300, 900))):
    zb = Z_TOP + 60 + sum(h for (_, h) in ((500, 1200), (1400, 1000), (2300, 900))[:s])
    box(f"HB_Crown_{s}", ((X_W + X_E) / 2, FRONT_Y + 100 * (s + 1) + (1100 - 200 * s) / 2, zb + hgt / 2), (W - inset * 2, 1100 - 200 * s, hgt), DARK)
    box(f"HB_Crown_{s}_Band", ((X_W + X_E) / 2, FRONT_Y + 100 * (s + 1) - 6, zb + hgt - 60), (W - inset * 2, 8, 20), GL_CYAN if s % 2 == 0 else GL_MAG)
z_mast = Z_TOP + 60 + 1200 + 1000 + 900
box("HB_Mast", ((X_W + X_E) / 2, FRONT_Y + 600, z_mast + 1800), (60, 60, 3600), TRIM)
box("HB_Beacon", ((X_W + X_E) / 2, FRONT_Y + 600, z_mast + 3620), (90, 90, 90), BEACON)

# ------------------------------------------------------------------ lift doors: open fully
# The kit's pair is asymmetric: SM_Door_Left spans local x 55..159, SM_Door_Right spans -159..92 (it overlaps the left
# leaf). Each leaf has to clear the 318 cm opening (-159..159), so they slide by different amounts.
bl = unreal.load_asset("/Game/SciFiTramStation/Meshes/SM_Door_Left").get_bounding_box()
br = unreal.load_asset("/Game/SciFiTramStation/Meshes/SM_Door_Right").get_bounding_box()
edge = max(bl.max.x, -br.min.x)
slide_l = (edge - bl.min.x) + 6.0
slide_r = (br.max.x + edge) + 6.0
for a in EAS.get_all_level_actors():
    if a.get_actor_label() == "B_Lift":
        a.set_editor_property("lower_door_open_offsets", [V(slide_l, 0, 0), V(-slide_r, 0, 0)])
        a.set_editor_property("upper_door_open_offsets", [V(-slide_l, 0, 0), V(slide_r, 0, 0)])
        log(f"lift door slide L {slide_l:.0f} / R {slide_r:.0f} cm (was 115 / 115)")

LES.save_current_level()
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
open(unreal.Paths.project_saved_dir() + "NV_hub_building.txt", "w").write("\n".join(OUT))
