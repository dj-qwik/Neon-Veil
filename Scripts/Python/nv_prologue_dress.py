"""NEON VEIL - prologue dressing pass (L_M00_Prologue).

  * centre pilaster no longer cuts through the VEYRA CENTRAL lettering
  * hub entrance: door surround light strips, door panels, info + AION notice screens, canopy fascia, planters,
    bin, vending machine
  * street-level lobby: line-map poster and notice by the lift, info kiosk, vending machine, planters, bins,
    wall light strips, a hanging lift sign
  * Crown Line departure board shows an English Veyra line map + departures (screen overlay)
  * easter egg: the lift-cab "system offline" monitor and one street billboard carry the Monkey Business logo
  * crew-pass room: the crate stack in front of the Station Ops terminal is moved aside

Textures come from Art/Signage (Tools/signage_build.py). Idempotent: its actors live in folder P_Dress2 (tag NVDRESS2).
Usage: py nv_prologue_dress.py [noimport]
Report: Saved/NV_prologue_dress.txt"""
import math, os, sys
import unreal

OUT = []
def log(*a):
    OUT.append(" ".join(str(x) for x in a))

EAL = unreal.EditorAssetLibrary
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
LES = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
UES = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
AT = unreal.AssetToolsHelpers.get_asset_tools()
MEL = unreal.MaterialEditingLibrary
V = lambda x, y, z: unreal.Vector(x, y, z)
def R(p=0.0, y=0.0, r=0.0):
    return unreal.Rotator(roll=r, pitch=p, yaw=y)
ARGS = sys.argv[1:]

MAP = "/Game/NeonVeil/Maps/M00/L_M00_Prologue"
if not UES.get_editor_world().get_path_name().startswith(MAP):
    LES.load_level(MAP)
W = UES.get_editor_world()
PROJ = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
TEX_DIR = "/Game/NeonVeil/Textures/Signage"
MAT_DIR = "/Game/NeonVeil/Materials/Signage"
ZS = -12000.0

FOLDER, TAG = "P_Dress2", "NVDRESS2"
for a in list(EAS.get_all_level_actors()):
    if str(a.get_folder_path()) == FOLDER or TAG in [str(t) for t in a.tags]:
        EAS.destroy_actor(a)
ACTORS = list(EAS.get_all_level_actors())

def find(label):
    for a in ACTORS:
        if a.get_actor_label() == label:
            return a
    log("not found:", label)
    return None

def load(p):
    a = unreal.load_asset(p)
    if not a:
        log("MISSING", p)
    return a

def tagit(a, label):
    a.set_actor_label(label); a.set_folder_path(FOLDER); a.tags = [unreal.Name(TAG)]
    return a

# ------------------------------------------------------------------ textures + materials
def imp_tex(name):
    path = f"{TEX_DIR}/{name}"
    if "noimport" not in ARGS or not EAL.does_asset_exist(path):
        t = unreal.AssetImportTask()
        t.filename = os.path.join(PROJ, "Art", "Signage", name + ".png")
        t.destination_path = TEX_DIR; t.destination_name = name
        t.replace_existing = True; t.automated = True; t.save = True
        AT.import_asset_tasks([t])
    tex = load(path)
    if tex:
        tex.set_editor_property("lod_group", unreal.TextureGroup.TEXTUREGROUP_UI)
        tex.set_editor_property("srgb", True)
        EAL.save_loaded_asset(tex)
    return tex

def sign_master():
    path = f"{MAT_DIR}/M_NV_SignScreen"
    if EAL.does_asset_exist(path):
        return load(path)
    m = AT.create_asset("M_NV_SignScreen", MAT_DIR, unreal.Material, unreal.MaterialFactoryNew())
    m.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    white = load("/Engine/EngineResources/WhiteSquareTexture")
    def node(cls, x, y):
        return MEL.create_material_expression(m, cls, x, y)
    def sca(name, val, x, y):
        n = node(unreal.MaterialExpressionScalarParameter, x, y)
        n.set_editor_property("parameter_name", name); n.set_editor_property("default_value", val); return n
    def mul(a, b, x, y, oa="", ob=""):
        n = node(unreal.MaterialExpressionMultiply, x, y)
        MEL.connect_material_expressions(a, oa, n, "A"); MEL.connect_material_expressions(b, ob, n, "B"); return n
    tex = node(unreal.MaterialExpressionTextureSampleParameter2D, -900, -200)
    tex.set_editor_property("parameter_name", "Tex"); tex.set_editor_property("texture", white)
    lit = mul(tex, sca("Glow", 2.0, -900, 50), -600, -150, "RGB", "")
    # gentle screen flicker: 1 + Amt * sin(Time * Speed)
    t = node(unreal.MaterialExpressionTime, -1100, 250)
    ts = mul(t, sca("FlickerSpeed", 23.0, -1100, 350), -900, 250)
    sn = node(unreal.MaterialExpressionSine, -750, 250)
    MEL.connect_material_expressions(ts, "", sn, "")
    amp = mul(sn, sca("FlickerAmt", 0.04, -750, 380), -600, 260)
    one = node(unreal.MaterialExpressionAdd, -450, 250)
    MEL.connect_material_expressions(amp, "", one, "A")
    one.set_editor_property("const_b", 1.0)
    out = mul(lit, one, -300, -50)
    MEL.connect_material_property(out, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    MEL.recompile_material(m)
    EAL.save_loaded_asset(m)
    return m

def mi(name, parent, tex=None, tex_param="Tex", scalars=None):
    path = f"{MAT_DIR}/{name}"
    x = load(path) if EAL.does_asset_exist(path) else AT.create_asset(name, MAT_DIR, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    MEL.set_material_instance_parent(x, parent)
    if tex:
        MEL.set_material_instance_texture_parameter_value(x, tex_param, tex)
    for k, v in (scalars or {}).items():
        MEL.set_material_instance_scalar_parameter_value(x, k, v)
    MEL.update_material_instance(x); EAL.save_loaded_asset(x)
    return x

M_SIGN = sign_master()
TX = {n: imp_tex(n) for n in ("T_NV_CrownLineBoard", "T_NV_CrownLineMap", "T_NV_HubInfo", "T_NV_AIONNotice",
                                "T_NV_MonkeyBiz_Screen", "T_NV_MonkeyBiz_Ad")}
MI_BOARD = mi("MI_NV_Sign_CrownLineBoard", M_SIGN, TX["T_NV_CrownLineBoard"], scalars={"Glow": 1.6, "FlickerAmt": 0.02})
MI_MAP = mi("MI_NV_Sign_CrownLineMap", M_SIGN, TX["T_NV_CrownLineMap"], scalars={"Glow": 1.3})
MI_INFO = mi("MI_NV_Sign_HubInfo", M_SIGN, TX["T_NV_HubInfo"], scalars={"Glow": 1.5})
MI_AION = mi("MI_NV_Sign_AIONNotice", M_SIGN, TX["T_NV_AIONNotice"], scalars={"Glow": 1.5, "FlickerAmt": 0.06})
MI_MONKEY = mi("MI_NV_Sign_MonkeyBizScreen", M_SIGN, TX["T_NV_MonkeyBiz_Screen"], scalars={"Glow": 1.8, "FlickerAmt": 0.12, "FlickerSpeed": 31.0})
SCREEN_PARENT = load("/Game/ModularScifiInterior/Materials/Screens/MI_Screen_Parent")
MI_MONKEY_AD = mi("MI_NV_Screen_MonkeyBizAd", SCREEN_PARENT, TX["T_NV_MonkeyBiz_Ad"], tex_param="Screen") if SCREEN_PARENT else None

PLANE = load("/Engine/BasicShapes/Plane")
CUBE = load("/Engine/BasicShapes/Cube")
def mat_of(label, i=0):
    a = find(label)
    return a.static_mesh_component.get_material(i) if a else None
GL_CYAN = mat_of("Hub_Band_1")
GL_MAG = mat_of("Hub_Band_2")
TRIM = mat_of("Hub_Canopy")
DARK = mat_of("Bollard_6180_0")
M_SIGNTEXT = None
s = find("S_Board")
if s:
    M_SIGNTEXT = s.text_render.get_material(0)

# ------------------------------------------------------------------ helpers
def trace(a, b, ignore=None):
    hit = unreal.SystemLibrary.line_trace_single(W, a, b, unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, ignore or [],
                                                 unreal.DrawDebugTrace.NONE, True)
    if not hit:
        return None
    t = hit.to_tuple()
    return t[5], t[7], t[9]          # impact point, impact normal, actor

def screen(label, mat, center, normal, w, h, flip=False, off=3.0):
    """Emissive plane sign facing `normal`. The plane's texture U runs along its local X and V along local Y, so it is
    oriented with local X horizontal and local Y pointing down; `flip` mirrors it if it reads backwards."""
    n = unreal.Vector(normal.x, normal.y, 0.0); n = n.normal()
    a = EAS.spawn_actor_from_object(PLANE, center + n * off, R())
    down = V(0, 0, -1)
    best = None
    for p in (0.0, 90.0, 180.0, 270.0):
        for yw in range(0, 360, 90):
            for r in (0.0, 90.0, 180.0, 270.0):
                rot = R(p=p, y=yw + math.degrees(math.atan2(n.y, n.x)), r=r)
                a.set_actor_rotation(rot, False)
                if a.get_actor_up_vector().dot(n) > 0.99 and a.get_actor_right_vector().dot(down) > 0.99:
                    best = rot
                    break
            if best: break
        if best: break
    if best:
        a.set_actor_rotation(best, False)
    else:
        log("screen", label, "no rotation found")
    a.set_actor_scale3d(V((-w if flip else w) / 100.0, h / 100.0, 1.0))
    c = a.static_mesh_component
    c.set_material(0, mat)
    c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    c.set_editor_property("cast_shadow", False)
    log("screen", label, "at", center, "rot", best, "fwd", a.get_actor_forward_vector())
    return tagit(a, label)

def box(label, center, size, mat, coll=False):
    a = EAS.spawn_actor_from_object(CUBE, V(*center), R())
    a.set_actor_scale3d(V(size[0] / 100.0, size[1] / 100.0, size[2] / 100.0))
    c = a.static_mesh_component
    c.set_material(0, mat)
    if not coll:
        c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    c.set_editor_property("cast_shadow", False)
    return tagit(a, label)

def text(label, s, loc, yaw, size, color):
    a = EAS.spawn_actor_from_class(unreal.TextRenderActor, V(*loc), R(y=yaw))
    t = a.text_render
    t.set_editor_property("text", unreal.Text(s)); t.set_editor_property("world_size", size)
    t.set_editor_property("horizontal_alignment", unreal.HorizTextAligment.EHTA_CENTER)
    t.set_editor_property("vertical_alignment", unreal.VerticalTextAligment.EVRTA_TEXT_CENTER)
    t.set_editor_property("text_render_color", unreal.Color(int(color[0] * 255), int(color[1] * 255), int(color[2] * 255), 255))
    if M_SIGNTEXT:
        t.set_material(0, M_SIGNTEXT)
    return tagit(a, label)

# per-mesh yaw correction so the prop's front faces the requested direction (local +X assumed otherwise)
FRONT_YAW = {}
def prop(label, path, x, y, zfloor, face_yaw, scale=1.0, against=None):
    """Static mesh prop standing on zfloor. face_yaw = direction its front should face. If `against` is a wall point
    (x,y) the prop backs onto it."""
    m = load(path)
    if not m:
        return None
    yaw = face_yaw + FRONT_YAW.get(m.get_name(), 0.0)
    bb = m.get_bounding_box()
    mn, mx = bb.min, bb.max
    cx, cy = (mn.x + mx.x) / 2.0 * scale, (mn.y + mx.y) / 2.0 * scale
    ry = math.radians(yaw)
    ox, oy = cx * math.cos(ry) - cy * math.sin(ry), cx * math.sin(ry) + cy * math.cos(ry)
    if against is not None:
        # back of the (rotated) footprint touches the wall point: depth = half extent along the facing axis
        depth = (mx.x - mn.x) / 2.0 * scale if FRONT_YAW.get(m.get_name(), 0.0) % 180 == 0 else (mx.y - mn.y) / 2.0 * scale
        fx, fy = math.cos(math.radians(face_yaw)), math.sin(math.radians(face_yaw))
        x, y = against[0] + fx * (depth + 2.0), against[1] + fy * (depth + 2.0)
    a = EAS.spawn_actor_from_object(m, V(x - ox, y - oy, zfloor - mn.z * scale), R(y=yaw))
    a.set_actor_scale3d(V(scale, scale, scale))
    log("prop", label, m.get_name(), "bb", (round(mx.x - mn.x), round(mx.y - mn.y), round(mx.z - mn.z)), "at", a.get_actor_location())
    return tagit(a, label)

for pth in ("SM_FlowerPot_A", "SM_FlowerPot_A_Moss", "SM_FlowerPot_B", "SM_FlowerPot_Fan"):
    m = load("/Game/ModularScifiInterior/Meshes/Props/" + pth)
    if m:
        b = m.get_bounding_box()
        log("bounds", pth, (round(b.min.x), round(b.min.y), round(b.min.z)), (round(b.max.x), round(b.max.y), round(b.max.z)))
for pth in ("SM_CornBush_A", "SM_CornBush_B", "SM_HydroLab_VinePlantB"):
    m = load("/Game/ModularScifiInterior/Meshes/Plants/" + pth)
    if m:
        b = m.get_bounding_box()
        log("bounds", pth, (round(b.min.x), round(b.min.y), round(b.min.z)), (round(b.max.x), round(b.max.y), round(b.max.z)))

def planter(label, x, y, z):
    """Planter box with a fan plant growing out of it."""
    pot = prop(label, "/Game/ModularScifiInterior/Meshes/Props/SM_FlowerPot_B", x, y, z, 0)
    if pot:
        o, e = pot.get_actor_bounds(False)
        for k, dx in enumerate((-28, 28)):
            prop(f"{label}_Plant{k}", "/Game/ModularScifiInterior/Meshes/Plants/SM_CornBush_A", x + dx, y, o.z + e.z - 14, k * 70.0, 0.8)

def wall(start, d, length=1200):
    h = trace(V(*start), V(start[0] + d[0] * length, start[1] + d[1] * length, start[2]))
    if not h:
        log("no wall from", start, d)
        return None
    p, n, act = h
    log("wall hit", start, "->", (round(p.x), round(p.y), round(p.z)), "n", (round(n.x, 2), round(n.y, 2)), act.get_actor_label() if act else None)
    return p, n

# ------------------------------------------------------------------ 1. pilaster off the hub lettering
pil = find("HB_Pilaster_3_0")
if pil:
    top = pil.get_actor_location().z + pil.get_actor_scale3d().z * 50.0
    bottom = ZS + 1175.0
    l = pil.get_actor_location()
    pil.set_actor_location(V(l.x, l.y, (top + bottom) / 2.0), False, False)
    s3 = pil.get_actor_scale3d()
    pil.set_actor_scale3d(V(s3.x, s3.y, (top - bottom) / 100.0))
    log("pilaster now", bottom, "->", top)

# ------------------------------------------------------------------ 2. crew-pass room: clear the line to the terminal
for lab, loc, yaw in (("SM_Crate_B10", (6990, 4120, 400), 5.0), ("SM_Crate_A10", (6995, 4110, 480), -40.0),
                      ("SM_Box_small5", (7010, 4130, 560), 15.0)):
    a = find(lab)
    if a:
        a.set_actor_location(V(*loc), False, False)
        a.set_actor_rotation(R(y=yaw), False)
cyl = find("SM_Cylinder_B10")
if cyl:
    cyl.set_actor_location(V(6640, 4470, 400), False, False)

# ------------------------------------------------------------------ 3. departure board overlay
board = find("I_DepartureBoard")
if board:
    o, e = board.get_actor_bounds(False)
    # the screen faces the concourse (-X); overlay just proud of the glass
    # the holoscreen glass is curved: sit the overlay just in front of its most forward point
    fx = o.x - e.x
    screen("Board_Overlay", MI_BOARD, V(fx, o.y, o.z + 4), V(-1, 0, 0), 2 * e.y * 0.86, 2 * e.y * 0.86 / 0.582, off=1.0)

# ------------------------------------------------------------------ 4. easter egg: lift-cab monitor + one billboard
cab = find("Cab_Screen")
if cab:
    o, e = cab.get_actor_bounds(False)
    thin_x = e.x < e.y
    best = None
    clear = []
    for sgn in (1, -1):
        n = V(sgn, 0, 0) if thin_x else V(0, sgn, 0)
        half = e.x if thin_x else e.y
        out = trace(o + n * (half + 3.0), o + n * 400.0, [cab])
        d = (out[0] - o).length() if out else 400.0
        clear.append((d, n, o + n * half))
    clear.sort(key=lambda t: -t[0])
    log("cab clearances", [(round(c[0]), c[1]) for c in clear])
    best = (clear[0][1], clear[0][2])
    if best:
        n, p = best
        face_w = 2 * (e.y if thin_x else e.x)
        face_h = 2 * e.z
        w = min(face_w * 0.84, face_h * 0.84 * 16.0 / 9.0)
        screen("Cab_Screen_MonkeyBiz", MI_MONKEY, V(p.x, p.y, o.z), n, w, w * 9.0 / 16.0)
        log("cab screen face", face_w, face_h, "normal", n)
    else:
        log("cab screen: no clear face")
ads = []
for a in ACTORS:
    lab = a.get_actor_label()
    if lab.startswith("Facade_") and isinstance(a, unreal.StaticMeshActor):
        o, e = a.get_actor_bounds(False)
        dims = sorted([2 * e.x, 2 * e.y, 2 * e.z])
        aspect = dims[2] / max(dims[1], 1.0)
        hub_d = abs(o.y + 6600.0)
        ads.append((abs(aspect - 1.5), hub_d, lab, a, (round(dims[2]), round(dims[1])), e))
ads.sort(key=lambda t: (round(t[0], 1), t[1]))
for t in ads:
    log("ad candidate", t[2], t[4], "aspect err", round(t[0], 2))
if ads and MI_MONKEY_AD:
    pick = ads[0][3]
    pick.static_mesh_component.set_material(0, MI_MONKEY_AD)
    log("billboard easter egg on", ads[0][2])

# ------------------------------------------------------------------ 5. hub entrance (street side)
DOOR_X = 7046.0
fac = wall((DOOR_X - 600, -7400, -11800), (0, 1))
FY = fac[0].y if fac else -6613.0
FN = V(0, -1, 0)
for side, x in (("L", DOOR_X - 228), ("R", DOOR_X + 228)):
    box(f"HubDoor_Strip_{side}", (x, FY - 4, -11805), (8, 6, 390), GL_CYAN)
box("HubDoor_Lintel", (DOOR_X, FY - 4, -11604), (464, 6, 8), GL_CYAN)
screen("HubSign_Info", MI_INFO, V(DOOR_X - 600, FY, -11790), FN, 130, 182)
screen("HubSign_AION", MI_AION, V(DOOR_X + 600, FY, -11790), FN, 130, 182)
for side, x in (("L", DOOR_X - 600), ("R", DOOR_X + 600)):
    box(f"HubSign_Frame_{side}", (x, FY - 0.8, -11790), (146, 1.5, 198), DARK)
text("HubCanopy_Fascia", "CROWN LINE  ·  CONCOURSE LIFTS  ·  TRANSIT", (DOOR_X, -6876, -11570), -90, 15, (1.0, 0.86, 0.6))
prop("HubDoor_Panel_L", "/Game/ModularScifiInterior/Meshes/Props/SM_DoorPanel_A", 0, 0, -11940, -90, 1.0, (DOOR_X - 300, FY))
prop("HubDoor_Panel_R", "/Game/ModularScifiInterior/Meshes/Props/SM_DoorPanel_A", 0, 0, -11940, -90, 1.0, (DOOR_X + 300, FY))
planter("Hub_Planter_L", DOOR_X - 900, FY - 70, ZS)
planter("Hub_Planter_R", DOOR_X + 900, FY - 70, ZS)
prop("Hub_Bin", "/Game/SciFiTramStation/Meshes/SM_RubbishCan", DOOR_X - 1060, FY - 60, ZS, -90)
prop("Hub_Vending", "/Game/SciFiTramStation/Meshes/SM_Snack_machine_a", 0, 0, ZS, -90, 1.0, (DOOR_X + 1060, FY))

# ------------------------------------------------------------------ 6. street-level lobby
LZ = ZS
north = wall((DOOR_X - 650, -5600, -11800), (0, 1))
west = wall((6500, -6000, -11800), (-1, 0))
east = wall((7600, -6000, -11800), (1, 0))
NY = north[0].y if north else -4930.0
WX = west[0].x if west else 5850.0
EX = east[0].x if east else 8240.0
log("lobby walls N/W/E", NY, WX, EX)
screen("Lobby_LineMap", MI_MAP, V(DOOR_X - 680, NY, -11790), V(0, -1, 0), 150, 188)
screen("Lobby_AION", MI_AION, V(DOOR_X + 680, NY, -11790), V(0, -1, 0), 120, 168)
box("Lobby_LineMap_Frame", (DOOR_X - 680, NY - 0.8, -11790), (164, 1.5, 202), DARK)
box("Lobby_AION_Frame", (DOOR_X + 680, NY - 0.8, -11790), (134, 1.5, 182), DARK)
for side, x, d in (("W", WX + 2, 1), ("E", EX - 2, -1)):
    box(f"Lobby_WallStrip_{side}", (x, -5720, -11650), (4, 1500, 5), GL_CYAN)
    box(f"Lobby_WallStripLow_{side}", (x, -5720, -11975), (4, 1500, 3), GL_MAG)
prop("Lobby_Vending_W", "/Game/SciFiTramStation/Meshes/SM_Snack_machine_a", 0, 0, LZ, 0, 1.0, (WX, -6150))
for i, (x, y) in enumerate(((WX + 90, -6420), (EX - 90, -6420), (WX + 90, NY - 90), (EX - 90, NY - 90))):
    planter(f"Lobby_Planter_{i}", x, y, LZ)
# (kept clear of the lobby citizens' routes: x 6300 / 7850-7950 lanes, y -5420 and -6100..-6200 crossings)
prop("Lobby_Bin_W", "/Game/SciFiTramStation/Meshes/SM_RubbishCan", 6190, -6420, LZ, 0)
prop("Lobby_Bin_E", "/Game/SciFiTramStation/Meshes/SM_RubbishCan", 7720, -6420, LZ, 180)
# colour: big ad screens on the side walls, glow frame around the lift doors
AD_W = mat_of("Blade_W0") or GL_CYAN
AD_E = mat_of("Facade_W0") or GL_MAG
box("Lobby_Ad_W", (WX + 3, -5450, -11800), (4, 340, 190), AD_W)
box("Lobby_Ad_W_Frame", (WX + 1.5, -5450, -11800), (2, 356, 206), DARK)
box("Lobby_Ad_E", (EX - 3, -5450, -11800), (4, 340, 190), AD_E)
box("Lobby_Ad_E_Frame", (EX - 1.5, -5450, -11800), (2, 356, 206), DARK)
for side, x in (("L", DOOR_X - 178), ("R", DOOR_X + 178)):
    box(f"LiftDoor_Strip_{side}", (x, NY - 3, -11850), (6, 6, 300), GL_CYAN)
box("LiftDoor_Lintel", (DOOR_X, NY - 3, -11697), (362, 6, 6), GL_CYAN)
# free-standing wayfinding totems either side of the guide strip (map toward the street, info toward the lift)
for side, x in (("W", DOOR_X - 520), ("E", DOOR_X + 520)):
    box(f"Lobby_Totem_{side}", (x, -5800, -11900), (80, 14, 200), DARK, True)
    box(f"Lobby_Totem_{side}_Cap", (x, -5800, -11799), (84, 18, 4), GL_CYAN)
    screen(f"Lobby_Totem_{side}_Map", MI_MAP, V(x, -5807, -11858), V(0, -1, 0), 72, 90, off=0.6)
    screen(f"Lobby_Totem_{side}_Info", MI_INFO, V(x, -5793, -11858), V(0, 1, 0), 66, 92.4, off=0.6)
# hanging lift sign over the guide strip
box("Lobby_HangSign", (DOOR_X, -5650, -11690), (380, 8, 56), DARK)
box("Lobby_HangSign_GlowF", (DOOR_X, -5655, -11690), (370, 1, 2), GL_CYAN)
for nm, yaw, yy, s, col in (("F", -90, -5655.5, "CROWN LINE  ·  LIFT AHEAD", (0.4, 0.95, 1.0)),
                            ("B", 90, -5644.5, "EXIT  ·  STREET LEVEL", (1.0, 0.86, 0.6))):
    text(f"Lobby_HangSign_Text{nm}", s, (DOOR_X, yy, -11690), yaw, 30, col)
for side, x in (("W", DOOR_X - 150), ("E", DOOR_X + 150)):
    box(f"Lobby_HangRod_{side}", (x, -5650, -11640), (2, 2, 44), DARK)

LES.save_current_level()
open(unreal.Paths.project_saved_dir() + "NV_prologue_dress.txt", "w").write("\n".join(OUT))
