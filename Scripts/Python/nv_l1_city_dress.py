"""Future-city dressing ("tasteful Blade Runner": the good side of Veyra, clean and glowing, not run-down).
arg: prologue | crown   (run on the open map; the prologue build calls this itself at the end)

prologue: street (shopfront canopies, blade signs with holo ads, facade billboards, rooftop brand signs, sleek light
          poles, bollards, crosswalk light bars), sky (flying traffic, searchlights, moon, high haze, low ambient), and
          the LIFT VIEW - a megatower cluster east of the glass shaft with giant holo ads at the heights you rise
          through, traffic lanes threading between them at several altitudes and the Glass Crown on the horizon.
crown:    holo ads + edge neon + searchlights on the towers along the Crown Line ride.
Everything lives in outliner folder P_Dress / R_Dress (rebuilt each run). Report: Saved/NV_l1_city_dress.txt"""
import math, random, sys
import unreal

MODE = sys.argv[-1] if sys.argv[-1] in ("prologue", "crown") else "prologue"
OUT = []
def log(*a):
    OUT.append(" ".join(str(x) for x in a))

EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
EAL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary
AT = unreal.AssetToolsHelpers.get_asset_tools()
V = unreal.Vector
def R(p=0.0, y=0.0, r=0.0):
    return unreal.Rotator(roll=r, pitch=p, yaw=y)
FOLDER = "P_Dress" if MODE == "prologue" else "R_Dress"
rng = random.Random(42)

# wipe: by folder, by our tag, and (one-time cleanup) untagged leftovers of earlier runs whose folder got lost
TAG = unreal.Name("NVD_" + MODE)
PREFIX = ("Canopy", "Shop_", "Facade_", "Blade", "Roof_", "RoofFrame_", "Bollard", "Crosswalk_", "Sky_Street", "Sky_View",
          "Sky_Far", "Low_", "Mega_", "Spire_", "Skybridge_", "GlassCrown_Landmark", "Crown_", "Search_", "Moon",
          "Lift_PostProcess", "Street_Night_PP", "Belly_")
SUFFIX = ("_Pole", "_Arm", "_Head", "_Ring", "_Beacon")
DRESS_KEYS = ("_Ad", "_Edge", "_Ring", "_Beacon", "_Brand")
nw = 0
for a in list(EAS.get_all_level_actors()):
    lab = a.get_actor_label()
    folder = str(a.get_folder_path())
    stray = False
    if folder in ("None", ""):
        if MODE == "prologue":
            stray = lab.startswith(PREFIX) or (lab.startswith(("StreetLamp_", "Skyline_")) and lab.endswith(SUFFIX))
        else:
            stray = (lab.startswith("CS_") and any(k in lab for k in DRESS_KEYS)) or lab.startswith(("Search_", "Spire_Band", "Spire_Brand"))
    if folder == FOLDER or TAG in a.tags or stray:
        EAS.destroy_actor(a); nw += 1
log("wiped:", nw)

CUBE = unreal.load_asset("/Engine/BasicShapes/Cube")
MATDIR = "/Game/NeonVeil/Materials/Prologue"
M_GLOW = unreal.load_asset(f"{MATDIR}/M_NV_Glow")
M_TEXT = unreal.load_asset(f"{MATDIR}/M_NV_SignText_DF")
M_DARK = unreal.load_asset("/Game/SciFiTramStation/Materials/MI_Trim_B")
DARKMETAL = unreal.load_asset("/Game/NeonVeil/Tests/Materials/TEMP_M_Titanium") or M_DARK

def glow(name, color, g=8.0):
    path = f"{MATDIR}/{name}"
    mi = unreal.load_asset(path) if EAL.does_asset_exist(path) else AT.create_asset(name, MATDIR, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    MEL.set_material_instance_parent(mi, M_GLOW)
    MEL.set_material_instance_vector_parameter_value(mi, "Color", unreal.LinearColor(*color, 1))
    MEL.set_material_instance_scalar_parameter_value(mi, "Glow", g)
    EAL.save_loaded_asset(mi)
    return mi
G = {
    "cyan": glow("MI_NV_Glow_Cyan", (0.15, 0.85, 1.0)),
    "magenta": glow("MI_NV_Glow_Magenta", (1.0, 0.15, 0.7)),
    "amber": glow("MI_NV_Glow_Amber", (1.0, 0.55, 0.1)),
    "violet": glow("MI_NV_Glow_Violet", (0.55, 0.25, 1.0)),
    "white": glow("MI_NV_Glow_White", (0.85, 0.92, 1.0), 6.0),
    "red": glow("MI_NV_Glow_Red", (1.0, 0.06, 0.04), 12.0),
    "teal": glow("MI_NV_Glow_Teal", (0.1, 1.0, 0.7)),
}
NEONS = ["cyan", "magenta", "violet", "amber", "teal"]
SCREENS = [unreal.load_asset(f"/Game/ModularScifiInterior/Materials/Screens/MI_Screen_{n}") for n in
           ("Blue_A", "Blue_C", "Blue_E", "Cryo_B", "Dark_C")]     # few distinct screens: VRAM on a 6 GB card
SCREENS = [s for s in SCREENS if s]
log("screens:", len(SCREENS))
BRANDS = ["AION", "VEYRA DYNAMICS", "KESTREL", "NOVA//LINE", "SYNTHE", "ORBITAL", "HALCYON", "CROWN LINE",
          "MERIDIAN", "LUMEN", "AXIOM", "SERAPH", "VANTA", "ECHO-9", "NEOGEN", "PRISM"]

def box(label, c, size, mat, rot=None):
    a = EAS.spawn_actor_from_object(CUBE, V(*c), rot or R())
    a.set_actor_label(label); a.set_folder_path(FOLDER); a.tags = [TAG]
    a.set_actor_scale3d(V(size[0] / 100.0, size[1] / 100.0, size[2] / 100.0))
    smc = a.static_mesh_component
    smc.set_material(0, mat)
    smc.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    smc.set_editor_property("cast_shadow", False)
    return a

def text(label, s, c, yaw, size, color, roll=0.0):
    a = EAS.spawn_actor_from_class(unreal.TextRenderActor, V(*c), R(y=yaw, r=roll))
    a.set_actor_label(label); a.set_folder_path(FOLDER); a.tags = [TAG]
    t = a.text_render
    t.set_editor_property("text", unreal.Text(s))
    t.set_editor_property("world_size", size)
    t.set_editor_property("horizontal_alignment", unreal.HorizTextAligment.EHTA_CENTER)
    t.set_editor_property("vertical_alignment", unreal.VerticalTextAligment.EVRTA_TEXT_CENTER)
    t.set_editor_property("text_render_color", unreal.Color(int(color[0] * 255), int(color[1] * 255), int(color[2] * 255), 255))
    t.set_material(0, M_TEXT)
    return a

COLRGB = {"cyan": (0.3, 0.95, 1.0), "magenta": (1.0, 0.35, 0.85), "violet": (0.7, 0.5, 1.0),
          "amber": (1.0, 0.7, 0.3), "teal": (0.3, 1.0, 0.8), "white": (0.9, 0.95, 1.0), "red": (1.0, 0.2, 0.15)}

def spot(label, c, rot, intensity, radius, color, cone, volumetric=3.0, shadows=False):
    radius = min(radius, 45000.0)          # long volumetric beams were part of the GPU budget problem
    volumetric = min(volumetric, 2.0)
    a = EAS.spawn_actor_from_class(unreal.SpotLight, V(*c), rot)
    a.set_actor_label(label); a.set_folder_path(FOLDER); a.tags = [TAG]
    l = a.spot_light_component
    l.set_mobility(unreal.ComponentMobility.MOVABLE)
    l.set_editor_property("intensity_units", unreal.LightUnits.CANDELAS)
    l.set_editor_property("intensity", intensity)
    l.set_editor_property("attenuation_radius", radius)
    l.set_editor_property("outer_cone_angle", cone)
    l.set_editor_property("inner_cone_angle", cone * 0.6)
    l.set_editor_property("light_color", unreal.Color(int(color[0] * 255), int(color[1] * 255), int(color[2] * 255), 255))
    l.set_editor_property("cast_shadows", shadows)
    l.set_editor_property("volumetric_scattering_intensity", volumetric)
    return a

def billboard(label, center, normal_yaw, w, h, depth=40.0, frame=None):
    """Holo ad: screen panel facing normal_yaw (degrees, direction the face looks), thin glowing frame."""
    yaw = math.radians(normal_yaw)
    nx, ny = math.cos(yaw), math.sin(yaw)
    rot = R(y=normal_yaw)
    box(label, center, (depth, w, h), rng.choice(SCREENS), rot)
    col = G[frame or rng.choice(NEONS)]
    off = depth / 2 + 4
    cx, cy, cz = center
    for k, dz in (("T", h / 2), ("B", -h / 2)):
        box(f"{label}_F{k}", (cx + nx * off, cy + ny * off, cz + dz), (6, w + 40, 18), col, rot)
    for k, s in (("L", -1), ("R", 1)):
        # perpendicular to the face: offset along the panel width axis (yaw + 90)
        px, py = math.cos(yaw + math.pi / 2), math.sin(yaw + math.pi / 2)
        box(f"{label}_F{k}", (cx + nx * off + px * s * (w / 2 + 10), cy + ny * off + py * s * (w / 2 + 10), cz), (6, 18, h), col, rot)

def traffic(label, start, yaw, length, per_dir, spread, speed, scale, seed, cyan_fwd=True):
    a = EAS.spawn_actor_from_class(unreal.NVTrafficStream, V(*start), R(y=yaw))
    a.set_actor_label(label); a.set_folder_path(FOLDER); a.tags = [TAG]
    a.set_editor_property("lane_length", length)
    a.set_editor_property("lane_spread", unreal.Vector2D(*spread))
    a.set_editor_property("vehicles_per_direction", per_dir)
    a.set_editor_property("speed_range", unreal.Vector2D(*speed))
    a.set_editor_property("vehicle_scale", V(*scale))
    a.set_editor_property("two_way", True)
    a.set_editor_property("seed", seed)
    a.set_editor_property("vehicle_mesh", CUBE)
    F = "/Game/NeonVeil/Materials/FX/MI_NV_TrafficCar_"
    a.set_editor_property("forward_material", unreal.load_asset(F + ("Cyan_Fwd" if cyan_fwd else "White_Fwd")))
    a.set_editor_property("reverse_material", unreal.load_asset(F + ("White_Rev" if cyan_fwd else "Cyan_Rev")))
    return a

# footprint (x, y, height) from Saved/NV_l1_bpp_catalog.json: freshly spawned packed-level actors report bogus
# (huge) bounds in the editor, which turned neon rings into giant slabs across the sky
BPP_SIZE = {"BPP_Bldg_Hero_Tower_CHC_CHD_Modern_A01_N1": (12687, 7624, 34528), "BPP_Bldg_Hero_Mid_SFE_C01_N1": (7792, 5422, 24778),
            "BPP_SFD_RoundSplitTower_N1": (4543, 9345, 12851), "BPP_Bldg_Hero_Mid_NYG_Modern_A01_N1": (5845, 6723, 15353),
            "BPP_SFD_Ref_N1": (7390, 6490, 25801), "BPP_SFA_Ref_N1": (3719, 9884, 5578), "BPP_CHI_Ref_A1_N1": (5862, 4538, 6515),
            "BPP_Bldg_Hero_NYG_Modern_Square_A01_N1": (6362, 5562, 6201), "BPP_SFJ_Ref_N1": (4643, 6143, 7479),
            "BPP_NYH_Ref_N1": (4191, 2616, 5012), "BPP_CHA_Ref_N1": (3908, 4358, 13689), "BPP_CHE_Ref_A1_N1": (5851, 4442, 13979),
            "BPP_SFE_Ref_N1": (5731, 5528, 16930), "BPP_CHH_Ref_A1_N1": (5134, 5134, 23728), "BPP_NYG_Ref_N1": (7992, 5612, 27049)}
class _B:
    def __init__(self, x, y, z):
        self.x, self.y, self.z = x, y, z
def bounds_of(actor):
    """(origin, extent) - from the catalog for spawned BPPs (tag 'nvsize:'), else the actor's own bounds."""
    for t in actor.tags:
        t = str(t)
        if t.startswith("nvsize:"):
            sx, sy, sz, bz = (float(v) for v in t[7:].split(","))
            loc = actor.get_actor_location()
            return _B(loc.x, loc.y, bz + sz / 2), _B(sx / 2, sy / 2, sz / 2)
    o, e = actor.get_actor_bounds(False)
    return o, e

def bpp(name, label, loc, yaw=0.0):
    AR = unreal.AssetRegistryHelpers.get_asset_registry()
    hits = [x for x in AR.get_assets(unreal.ARFilter(package_paths=["/Game/CitySampleBuildings"], recursive_paths=True,
            class_paths=[unreal.TopLevelAssetPath("/Script/Engine", "Blueprint")])) if str(x.asset_name) == name]
    if not hits:
        log("no BPP", name); return None
    a = EAS.spawn_actor_from_object(unreal.load_asset(str(hits[0].package_name)), V(*loc), R(y=yaw))
    a.set_actor_label(label); a.set_folder_path(FOLDER); a.tags = [TAG]
    if name in BPP_SIZE:
        sx, sy, sz = BPP_SIZE[name]
        if abs(((yaw % 180) + 180) % 180 - 90) < 1:
            sx, sy = sy, sx
        a.tags = [TAG, unreal.Name("nvsize:%g,%g,%g,%g" % (sx, sy, sz, loc[2]))]
    return a

def dress_tower(label, actor, face_yaws, z_levels, ad_w=2400, ad_h=4200, edge=True, beacon=True):
    """Holo ads on the given faces of a tower actor (bounds-based) + neon edges + red beacon on top."""
    o, e = bounds_of(actor)
    top = o.z + e.z
    for fy in face_yaws:
        r = math.radians(fy)
        nx, ny = round(math.cos(r)), round(math.sin(r))
        fx = o.x + nx * (e.x + 30)
        fyy = o.y + ny * (e.y + 30)
        for k, z in enumerate(z_levels):
            if z > top - ad_h / 2 - 200:
                continue
            billboard(f"{label}_Ad{fy}_{k}", (fx, fyy, z), fy, ad_w, ad_h, 60)
        if edge:
            col = G[rng.choice(NEONS)]
            h = top - (o.z - e.z)
            for sgn in (-1, 1):
                if nx:
                    ex, ey = fx, o.y + sgn * e.y * 0.98
                else:
                    ex, ey = o.x + sgn * e.x * 0.98, fyy
                box(f"{label}_Edge{fy}_{sgn}", (ex, ey, o.z - e.z + h / 2), (30, 30, h), col)
    # light rings around the whole tower at a few heights, and a giant vertical brand name on the first face
    base = o.z - e.z
    h = top - base
    for k, f in enumerate((0.42, 0.68, 0.93)):
        z = base + h * f
        col = G[NEONS[(k + len(label)) % len(NEONS)]]
        box(f"{label}_RingN{k}", (o.x, o.y + e.y + 25, z), (e.x * 2 + 60, 12, 60), col)
        box(f"{label}_RingS{k}", (o.x, o.y - e.y - 25, z), (e.x * 2 + 60, 12, 60), col)
        box(f"{label}_RingE{k}", (o.x + e.x + 25, o.y, z), (12, e.y * 2 + 60, 60), col)
        box(f"{label}_RingW{k}", (o.x - e.x - 25, o.y, z), (12, e.y * 2 + 60, 60), col)
    if face_yaws and h > 8000:
        fy = face_yaws[0]
        r = math.radians(fy)
        nx, ny = round(math.cos(r)), round(math.sin(r))
        cn = rng.choice(NEONS)
        px = o.x + nx * (e.x + 45) + (-ny) * (e.x * 0.6 if ny else 0)
        py = o.y + ny * (e.y + 45) + (nx) * (e.y * 0.6 if nx else 0)
        text(f"{label}_Brand", rng.choice(BRANDS), (px, py, base + h * 0.55), fy, min(1400.0, h / 14), COLRGB[cn], 90.0)
    if beacon:
        box(f"{label}_Beacon", (o.x, o.y, top + 150), (160, 160, 160), G["red"])

# =========================================================================== PROLOGUE
if MODE == "prologue":
    ZS = -12000.0
    WFACE, EFACE = 5150.0, 8942.0            # street-facing facade planes (sidewalk outer edges)
    Y0, Y1 = -7100.0, -16200.0

    # ---- shopfront canopies: a warm/cool light band above the ground floor of every front, plus brand text
    for side, x, yaw in (("W", WFACE, 0.0), ("E", EFACE, 180.0)):
        sgn = 1 if side == "W" else -1
        for k, y in enumerate((-8250, -11670, -15090)):
            col = NEONS[(k * 2 + (side == "E")) % len(NEONS)]
            box(f"Canopy_{side}{k}", (x + sgn * 120, y, ZS + 430), (240, 3200, 14), DARKMETAL)
            box(f"CanopyGlow_{side}{k}", (x + sgn * 120, y, ZS + 421), (220, 3150, 3), G[col])
            box(f"CanopyEdge_{side}{k}", (x + sgn * 240, y, ZS + 430), (6, 3200, 22), G[col])
            text(f"Shop_{side}{k}", rng.choice(BRANDS), (x + sgn * 8, y, ZS + 560), yaw, 120, COLRGB[col])
            # facade billboard on the upper floors
            billboard(f"Facade_{side}{k}", (x + sgn * 30, y + rng.uniform(-600, 600), ZS + 1500), yaw, 1500, 800, 30)
    # ---- blade signs sticking out of the facades (vertical holo ads, readable from down the street)
    for i, y in enumerate((-7600, -9500, -10900, -12700, -14200, -15600)):
        for side, x in (("W", WFACE), ("E", EFACE)):
            sgn = 1 if side == "W" else -1
            col = NEONS[(i + (side == "E") * 2) % len(NEONS)]
            cz = ZS + 1050 + (i % 2) * 250
            box(f"Blade_{side}{i}", (x + sgn * 170, y, cz), (300, 26, 1000), rng.choice(SCREENS))
            box(f"BladeRim_{side}{i}", (x + sgn * 325, y, cz), (10, 34, 1010), G[col])
            for face in (-1, 1):
                text(f"BladeTxt_{side}{i}_{face}", rng.choice(BRANDS), (x + sgn * 170, y + face * 16, cz), 90 * face,
                     46, COLRGB[col], 90.0)
    # ---- rooftop brand signs on the fronts
    for k, (x, y, yaw, s) in enumerate(((4746, -8250, 0, "AION"), (9346, -11670, 180, "VEYRA DYNAMICS"),
                                        (4746, -15090, 0, "HALCYON"), (9346, -8250, 180, "NOVA//LINE"))):
        col = NEONS[k % len(NEONS)]
        text(f"Roof_{k}", s, (x, y, ZS + 2800), yaw, 320, COLRGB[col])
        box(f"RoofFrame_{k}", (x, y, ZS + 2580), (40, 2800, 40), G[col])
    # ---- sleek light poles replace the slum lamps (keep their spotlights), bollards, crosswalk light bars
    for a in EAS.get_all_level_actors():
        import re as _re
        if _re.match(r"^StreetLamp_[EW]_\d+$", a.get_actor_label()) and isinstance(a, unreal.StaticMeshActor):
            a.set_actor_hidden_in_game(True); a.set_is_temporarily_hidden_in_editor(True)
            a.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
            loc = a.get_actor_location()
            box(a.get_actor_label() + "_Pole", (loc.x, loc.y, ZS + 330), (22, 22, 660), DARKMETAL)
            arm = 1 if loc.x < 7046 else -1
            box(a.get_actor_label() + "_Arm", (loc.x + arm * 120, loc.y, ZS + 650), (260, 16, 16), DARKMETAL)
            box(a.get_actor_label() + "_Head", (loc.x + arm * 220, loc.y, ZS + 638), (200, 26, 6), G["white"])
            box(a.get_actor_label() + "_Ring", (loc.x, loc.y, ZS + 120), (30, 30, 8), G["cyan"])
    for i, y in enumerate(range(-7000, -16001, -900)):
        for x in (6180, 7912):
            box(f"Bollard_{x}_{i}", (x, y, ZS + 50), (24, 24, 100), DARKMETAL)
            box(f"BollardGlow_{x}_{i}", (x, y, ZS + 92), (26, 26, 6), G["cyan" if i % 2 else "violet"])
    for k, y in enumerate((-9000, -13400)):
        for j in range(8):
            box(f"Crosswalk_{k}_{j}", (6300 + j * 230, y, ZS + 1), (120, 600, 1), G["white"])
    # ---- flying traffic over the street and threading the lift view
    traffic("Sky_Street_A", (7046, -110000, ZS + 4200), 90, 220000, 70, (900, 300), (2500, 4500), (5.0, 1.8, 1.0), 21)
    traffic("Sky_Street_B", (7046, -110000, ZS + 7600), 90, 220000, 60, (1300, 400), (3500, 6500), (6.0, 2.1, 1.2), 22, False)
    traffic("Sky_View_A", (16000, -110000, -7000), 90, 220000, 110, (1100, 400), (3500, 6500), (6.0, 2.1, 1.2), 23)
    traffic("Sky_View_B", (24000, -110000, -2500), 90, 220000, 90, (1400, 500), (4500, 8000), (7.5, 2.6, 1.5), 24, False)
    traffic("Sky_View_C", (31000, -110000, 1500), 90, 220000, 80, (1600, 500), (5000, 9000), (8.5, 3.0, 1.7), 25)
    traffic("Sky_View_D", (9500, -2600, -4500), 0, 160000, 70, (900, 500), (3000, 6000), (6.0, 2.1, 1.2), 26)
    traffic("Sky_Far_A", (62000, -110000, 6000), 90, 220000, 80, (2000, 600), (6000, 10000), (9.0, 3.2, 1.8), 27, False)
    # ---- the lift view: megatower cluster east of the glass shaft (bases at street level), giant holo ads at the
    #      altitudes you rise through, the Glass Crown on the horizon
    # low foreground right outside the glass: you rise past these roofs in the first seconds and the vista opens
    LOW = [("BPP_SFA_Ref_N1", (15500, -10000), 0), ("BPP_CHI_Ref_A1_N1", (13500, -1500), 0), ("BPP_Bldg_Hero_NYG_Modern_Square_A01_N1", (14500, 6000), 90),
           ("BPP_SFJ_Ref_N1", (21000, 1500), 0), ("BPP_NYH_Ref_N1", (19000, -6000), 0)]
    for i, (name, (x, y), yaw) in enumerate(LOW):
        t = bpp(name, f"Low_{i}", (x, y, ZS), yaw)
        if t:
            o, e = bounds_of(t)
            rz, col = o.z + e.z + 30, G[NEONS[i % len(NEONS)]]      # thin neon roof-edge outline, not a slab
            box(f"Low_{i}_RoofN", (o.x, o.y + e.y - 60, rz), (e.x * 2 - 120, 14, 40), col)
            box(f"Low_{i}_RoofS", (o.x, o.y - e.y + 60, rz), (e.x * 2 - 120, 14, 40), col)
            box(f"Low_{i}_RoofE", (o.x + e.x - 60, o.y, rz), (14, e.y * 2 - 120, 40), col)
            box(f"Low_{i}_RoofW", (o.x - e.x + 60, o.y, rz), (14, e.y * 2 - 120, 40), col)
            box(f"Low_{i}_Beacon", (o.x + e.x * 0.7, o.y, o.z + e.z + 150), (100, 100, 100), G["red"])
    # modern mid-distance towers (no historic stone towers in this view)
    MEGA = [("BPP_Bldg_Hero_Tower_CHC_CHD_Modern_A01_N1", (42000, -11000), 0), ("BPP_Bldg_Hero_Mid_SFE_C01_N1", (36000, 9000), 90),
            ("BPP_SFD_RoundSplitTower_N1", (31000, -2000), 0), ("BPP_Bldg_Hero_Mid_NYG_Modern_A01_N1", (50000, 14000), 0),
            ("BPP_SFD_Ref_N1", (60000, -24000), 0), ("BPP_Bldg_Hero_Tower_CHC_CHD_Modern_A01_N1", (75000, 26000), 90)]
    for i, (name, (x, y), yaw) in enumerate(MEGA):
        t = bpp(name, f"Mega_{i}", (x, y, ZS), yaw)
        if t:
            dress_tower(f"Mega_{i}", t, (180,), (-8000, -3500, 1500, 7000), 2600 + 400 * (i % 3), 4400)
    # sci-fi spires: slender dark-glass towers with lit corners, light rings and skybridges - the "future" silhouette
    DG = unreal.load_asset("/Game/NeonVeil/Tests/Materials/TEMP_M_DarkGlass") or DARKMETAL
    SPIRES = [((56000, -2000), 3200, 52000), ((68000, -14000), 2600, 44000), ((88000, 6000), 3800, 60000),
              ((47000, 26000), 2400, 38000), ((98000, -30000), 3000, 48000), ((80000, 40000), 2800, 42000)]
    tops = []
    for i, ((x, y), w, h) in enumerate(SPIRES):
        z0 = ZS
        box(f"Spire_{i}", (x, y, z0 + h / 2), (w, w, h), DG)
        box(f"Spire_{i}_Tip", (x, y, z0 + h + 2500), (w * 0.35, w * 0.35, 5000), DG)
        col = NEONS[i % len(NEONS)]
        for sx in (-1, 1):
            for sy in (-1, 1):
                box(f"Spire_{i}_Corner{sx}{sy}", (x + sx * w / 2, y + sy * w / 2, z0 + h / 2), (40, 40, h), G[col])
        for k in range(int(h / 6000)):
            z = z0 + 6000 * (k + 1)
            box(f"Spire_{i}_Ring{k}", (x, y, z), (w + 40, w + 40, 40 if k % 3 else 120), G["white" if k % 3 else col])
        box(f"Spire_{i}_Beacon", (x, y, z0 + h + 5100), (200, 200, 200), G["red"])
        billboard(f"Spire_{i}_Ad", (x - w / 2 - 40, y, rng.uniform(-7000, 3000)), 180, w * 0.8, w * 1.6, 50)
        tops.append((x, y, h))
    for i, (a_, b_) in enumerate(((0, 1), (0, 3), (2, 4))):
        (x1, y1, _), (x2, y2, _) = tops[a_], tops[b_]
        L = math.hypot(x2 - x1, y2 - y1)
        yaw = math.degrees(math.atan2(y2 - y1, x2 - x1))
        z = ZS + 18000 + 4000 * i
        box(f"Skybridge_{i}", ((x1 + x2) / 2, (y1 + y2) / 2, z), (L, 600, 350), DG, R(y=yaw))
        box(f"Skybridge_{i}_Glow", ((x1 + x2) / 2, (y1 + y2) / 2, z - 180), (L, 520, 8), G["cyan"], R(y=yaw))
    crown = bpp("BPP_Bldg_Hero_Tower_CHC_CHD_Modern_A01_N1", "GlassCrown_Landmark", (120000, 14000, ZS), 0)
    if crown:
        o, e = bounds_of(crown)
        top = o.z + e.z
        for k in range(16):                                            # the crown: a ring of light at the top
            ang = 2 * math.pi * k / 16
            box(f"Crown_Ring{k}", (o.x + math.cos(ang) * e.x * 0.9, o.y + math.sin(ang) * e.y * 0.9, top + 900),
                (300, 300, 1800 + 600 * (k % 2)), G["cyan"])
        box("Crown_Halo", (o.x, o.y, top + 120), (e.x * 2.1, e.y * 2.1, 60), G["white"])
        for k, (yy, pp) in enumerate(((0, 70), (90, 72), (180, 70), (270, 72))):
            spot(f"Crown_Search{k}", (o.x, o.y, top + 400), R(p=pp, y=yy), 400000, 120000, (0.6, 0.9, 1.0), 2.5, 6.0)
    # ---- the station's belly: it floats 124 m up, so near the top of the lift ride you look up at its underside.
    #      A dark structural hull plate (with a cut-out for the lift shaft) + light lines + nav lights.
    BX0, BX1, BY0, BY1, BZ = -9600.0, 10600.0, -4800.0, 3200.0, -480.0
    HX0, HX1, HY0, HY1 = 6780.0, 7320.0, -4800.0, -4330.0          # shaft opening
    def slab(label, x0, x1, y0, y1):
        if x1 - x0 > 10 and y1 - y0 > 10:
            box(label, ((x0 + x1) / 2, (y0 + y1) / 2, BZ), (x1 - x0, y1 - y0, 60), DARKMETAL)
    slab("Belly_W", BX0, HX0, BY0, BY1)
    slab("Belly_E", HX1, BX1, BY0, BY1)
    slab("Belly_N", HX0, HX1, HY1, BY1)
    for k, x in enumerate(range(int(BX0) + 600, int(BX1), 2400)):
        if HX0 - 100 < x < HX1 + 100:
            continue
        box(f"Belly_Line{k}", (x, (BY0 + BY1) / 2, BZ - 32), (30, BY1 - BY0 - 200, 4), G["cyan" if k % 3 else "violet"])
    for k, (x, y) in enumerate(((BX0 + 200, BY0 + 200), (BX1 - 200, BY0 + 200), (BX0 + 200, BY1 - 200), (BX1 - 200, BY1 - 200),
                                (HX1 + 300, HY0 + 150))):
        box(f"Belly_Nav{k}", (x, y, BZ - 60), (90, 90, 60), G["red"])
    for k, (x0, x1) in enumerate(((BX0, BX1),)):
        box("Belly_EdgeS", ((x0 + x1) / 2, BY0 - 10, BZ), (x1 - x0, 20, 70), G["white"])
    # searchlights sweeping up from the street district + red beacons on the near skyline
    for k, (x, y, yy) in enumerate(((2000, -12000, 20), (12600, -15500, 160), (13200, -2600, 110))):
        spot(f"Search_{k}", (x, y, ZS + 2600), R(p=75, y=yy), 250000, 80000, (0.75, 0.85, 1.0), 3.0, 5.0)
    for a in EAS.get_all_level_actors():
        lab = a.get_actor_label()
        SKY_H = {"Skyline_0": 13689, "Skyline_1": 13979, "Skyline_2": 16930, "Skyline_3": 23728, "Skyline_4": 27049}
        if lab in SKY_H:
            loc = a.get_actor_location()
            box(f"{lab}_Beacon", (loc.x, loc.y, ZS + SKY_H[lab] + 120), (120, 120, 120), G["red"])
    # ---- night: low ambient, moon, haze up high, punchier bloom on the street + lift
    for a in EAS.get_all_level_actors():
        if isinstance(a, unreal.SkyLight):
            a.light_component.set_editor_property("intensity", 0.3)
        if isinstance(a, unreal.ExponentialHeightFog):
            fc = a.component
            fc.set_editor_property("fog_inscattering_luminance", unreal.LinearColor(0.02, 0.018, 0.045, 1))
            sd = fc.get_editor_property("second_fog_data")
            sd.set_editor_property("fog_density", 0.0035)
            sd.set_editor_property("fog_height_falloff", 0.02)
            sd.set_editor_property("fog_height_offset", 9000.0)
            fc.set_editor_property("second_fog_data", sd)
            fc.set_editor_property("volumetric_fog_scattering_distribution", 0.4)
            fc.set_editor_property("volumetric_fog_extinction_scale", 2.0)
    moon = EAS.spawn_actor_from_class(unreal.DirectionalLight, V(7046, -6000, 4000), R(p=-28, y=215))
    moon.set_actor_label("Moon"); moon.set_folder_path(FOLDER); moon.tags = [TAG]
    ml = moon.light_component
    ml.set_editor_property("intensity", 0.6)
    ml.set_editor_property("light_color", unreal.Color(150, 175, 255, 255))
    ml.set_editor_property("volumetric_scattering_intensity", 0.4)
    def ppv(label, c, size, prio, bias):
        p = EAS.spawn_actor_from_class(unreal.PostProcessVolume, V(*c), R())
        p.set_actor_label(label); p.set_folder_path(FOLDER); p.tags = [TAG]
        p.set_actor_scale3d(V(size[0] / 200.0, size[1] / 200.0, size[2] / 200.0))
        p.set_editor_property("priority", prio); p.set_editor_property("blend_radius", 400.0)
        st = p.settings
        for k, v in (("auto_exposure_bias", bias), ("bloom_intensity", 1.4), ("white_temp", 7200.0),
                     ("vignette_intensity", 0.5), ("color_saturation", unreal.Vector4(1.05, 1.0, 1.12, 1.0))):
            st.set_editor_property("override_" + k, True); st.set_editor_property(k, v)
        p.set_editor_property("settings", st)
    ppv("Lift_PostProcess", (7046, -4572, (ZS + 380) / 2), (700, 700, 380 - ZS), 3.0, 0.0)
    ppv("Street_Night_PP", (7046, -11500, ZS + 1500), (9000, 11000, 4000), 2.5, -0.2)

# =========================================================================== CROWN
else:
    PATH = [(-58000, -8000), (-50000, -8000), (-44000, -6500), (-38000, 0), (-32000, 6000), (-26000, 7000),
            (-12000, 7000), (-5300, 7000), (-300, 2000)]
    def dist_to_path(x, y):
        return min(math.hypot(x - px, y - py) for px, py in PATH)
    towers = [a for a in EAS.get_all_level_actors() if a.get_actor_label().startswith("CS_")
              and not any(k in a.get_actor_label() for k in DRESS_KEYS) and TAG not in a.tags
              and str(a.get_folder_path()) != FOLDER and not a.get_actor_label().startswith("CS_Search")]
    done = 0
    for a in towers:
        o, e = a.get_actor_bounds(False)
        d = dist_to_path(o.x, o.y)
        if d > 40000:
            continue
        # the faces that look toward the path
        px, py = min(PATH, key=lambda p: math.hypot(o.x - p[0], o.y - p[1]))
        dx, dy = px - o.x, py - o.y
        faces = [0 if dx > 0 else 180] if abs(dx) > abs(dy) else [90 if dy > 0 else 270]
        dress_tower(a.get_actor_label(), a, faces, (-6000, -1500, 3500, 9000), 2600, 4600, edge=(done % 2 == 0))
        done += 1
    log("crown towers dressed:", done)
    # GPU room for the dressing: half the original rain (absolute values so re-runs are idempotent)
    RAIN = {"RainNear_BridgeS": 2100, "RainMid_BridgeS": 1750, "RainNear_TramS": 1600, "RainNear_BridgeN": 2100,
            "RainMid_BridgeN": 1750, "RainNear_TramN": 1600, "RainNear_AtriumN": 2100, "RainMid_AtriumN": 2000}
    for a in EAS.get_all_level_actors():
        if isinstance(a, unreal.NVRainField) and a.get_actor_label() in RAIN:
            a.set_editor_property("count", RAIN[a.get_actor_label()])
            log("rain", a.get_actor_label(), "->", RAIN[a.get_actor_label()])
    for k, (x, y, yy) in enumerate(((-30000, 30000, 300), (-60000, -30000, 40), (15000, 40000, 220), (-20000, -25000, 120))):
        spot(f"Search_{k}", (x, y, 6000), R(p=72, y=yy), 300000, 100000, (0.7, 0.85, 1.0), 2.8, 5.0)
    # the transit spire: light bands on all four faces so it is not a black monolith
    for k, z in enumerate(range(-14000, 6000, 2200)):
        col = G["cyan" if k % 2 else "violet"]
        box(f"Spire_BandS{k}", (-59250, -13030, z), (9500, 12, 50), col)
        box(f"Spire_BandN{k}", (-59250, -2970, z), (9500, 12, 50), col)
        box(f"Spire_BandW{k}", (-64030, -8000, z), (12, 10000, 50), col)
    # the transit spire gets a crown of its own brand
    text("Spire_Brand", "CROWN LINE", (-54400, -8000, 2600), 0, 900, COLRGB["cyan"])

LES = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
LES.save_current_level()
log("dress actors:", sum(1 for a in EAS.get_all_level_actors() if str(a.get_folder_path()) == FOLDER))
open(unreal.Paths.project_saved_dir() + "NV_l1_city_dress.txt", "w").write("\n".join(OUT))
