"""NEON VEIL - M5 art pass: Directorate surface materials.

Builds M_NV_WorldSurface, a world-aligned master material for the Kit A surfaces. It uses
dominant-axis box mapping (3 texture fetches, no blending, since the Directorate is axis-aligned),
procedural panel seams sized to the Bible's 4 m module, a tint, roughness remap and optional
emissive. Material instances (MI_DIR_*) are built from the City Sample Buildings texture sets
(free Epic content, Fab), and every TEMP_ graybox material in L_M00_GlassCrown is swapped for
its art counterpart.

Re-runnable. Report: Saved/NV_m5_materials.txt
"""
import unreal

REPORT = []
def log(*a):
    msg = " ".join(str(x) for x in a)
    REPORT.append(msg)
    unreal.log("[NV M5] " + msg)

AT = unreal.AssetToolsHelpers.get_asset_tools()
EAL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary
AR = unreal.AssetRegistryHelpers.get_asset_registry()

ART = "/Game/NeonVeil/Materials/Art"
MASTER = f"{ART}/M_NV_WorldSurface"
MASTER_GLASS = f"{ART}/M_NV_Glass"
MASTER_EMIT = f"{ART}/M_NV_Emissive"

def ensure_dir(p):
    if not EAL.does_directory_exist(p):
        EAL.make_directory(p)

# ------------------------------------------------------------------ master material
def x(m, cls, px, py, **props):
    e = MEL.create_material_expression(m, cls, px, py)
    for k, v in props.items():
        e.set_editor_property(k, v)
    return e

def link(a, aout, b, bin_):
    ok = MEL.connect_material_expressions(a, aout, b, bin_)
    if not ok:
        log("WARN link failed", a.get_name(), aout, "->", b.get_name(), bin_)

def scalar(m, name, val, px, py, group="Surface"):
    return x(m, unreal.MaterialExpressionScalarParameter, px, py, parameter_name=name, default_value=val, group=group)

def vec(m, name, rgb, px, py, group="Surface"):
    return x(m, unreal.MaterialExpressionVectorParameter, px, py, parameter_name=name,
             default_value=unreal.LinearColor(rgb[0], rgb[1], rgb[2], 1), group=group)

def mask(m, src, px, py, r=False, g=False, b=False):
    e = x(m, unreal.MaterialExpressionComponentMask, px, py, r=r, g=g, b=b, a=False)
    link(src, "", e, "")
    return e

def binop(m, cls, a, b, px, py, aout="", bout=""):
    e = x(m, cls, px, py)
    link(a, aout, e, "A")
    link(b, bout, e, "B")
    return e

def unop(m, cls, a, px, py, aout=""):
    e = x(m, cls, px, py)
    link(a, aout, e, "")
    return e

def build_master(defaults):
    if EAL.does_asset_exist(MASTER):
        EAL.delete_asset(MASTER)
    ensure_dir(ART)
    m = AT.create_asset("M_NV_WorldSurface", ART, unreal.Material, unreal.MaterialFactoryNew())
    m.set_editor_property("used_with_nanite", True)
    m.set_editor_property("used_with_instanced_static_meshes", True)

    # world-space coordinates (cm) -> tile units
    wp = x(m, unreal.MaterialExpressionWorldPosition, -2600, 0)
    tile = scalar(m, "TileSize", 200.0, -2600, 120)
    uvw = binop(m, unreal.MaterialExpressionDivide, wp, tile, -2400, 40)
    uv_xy = mask(m, uvw, -2200, -80, r=True, g=True)
    uv_xz = mask(m, uvw, -2200, 40, r=True, b=True)
    uv_yz = mask(m, uvw, -2200, 160, g=True, b=True)

    # dominant axis of the surface normal
    nrm = x(m, unreal.MaterialExpressionVertexNormalWS, -2600, 320)
    an = unop(m, unreal.MaterialExpressionAbs, nrm, -2400, 320)
    ax = mask(m, an, -2200, 280, r=True)
    ay = mask(m, an, -2200, 360, g=True)
    az = mask(m, an, -2200, 440, b=True)
    mxy = binop(m, unreal.MaterialExpressionMax, ax, ay, -2000, 320)
    side = x(m, unreal.MaterialExpressionIf, -1800, 120)
    link(ax, "", side, "A"); link(ay, "", side, "B")
    link(uv_yz, "", side, "A > B"); link(uv_yz, "", side, "A == B"); link(uv_xz, "", side, "A < B")
    uvsel = x(m, unreal.MaterialExpressionIf, -1600, 0)
    link(az, "", uvsel, "A"); link(mxy, "", uvsel, "B")
    link(uv_xy, "", uvsel, "A > B"); link(uv_xy, "", uvsel, "A == B"); link(side, "", uvsel, "A < B")

    # textures (sampler types follow the actual imported textures)
    def tex_param(name, path, py):
        t = unreal.load_asset(path)
        e = x(m, unreal.MaterialExpressionTextureSampleParameter2D, -1300, py, parameter_name=name, group="Textures")
        e.set_editor_property("texture", t)
        cs = t.get_editor_property("compression_settings")
        vt = bool(t.get_editor_property("virtual_texture_streaming"))
        S = unreal.MaterialSamplerType
        if cs == unreal.TextureCompressionSettings.TC_NORMALMAP:
            st = S.SAMPLERTYPE_VIRTUAL_NORMAL if vt else S.SAMPLERTYPE_NORMAL
        elif cs == unreal.TextureCompressionSettings.TC_MASKS:
            st = S.SAMPLERTYPE_VIRTUAL_MASKS if vt else S.SAMPLERTYPE_MASKS
        elif not t.get_editor_property("srgb"):
            st = S.SAMPLERTYPE_VIRTUAL_LINEAR_COLOR if vt else S.SAMPLERTYPE_LINEAR_COLOR
        else:
            st = S.SAMPLERTYPE_VIRTUAL_COLOR if vt else S.SAMPLERTYPE_COLOR
        log("  tex", name, path.split("/")[-1], "vt" if vt else "", str(cs).split(".")[-1], "->", str(st).split(".")[-1])
        e.set_editor_property("sampler_type", st)
        link(uvsel, "", e, "UVs")
        return e

    td = tex_param("BaseColor", defaults["D"], -200)
    tn = tex_param("Normal", defaults["N"], 100)
    to = tex_param("ORM", defaults["ORM"], 400)

    # panel seams: distance to the nearest panel edge, in cm
    psize = scalar(m, "PanelSize", 400.0, -1800, 600, "Panels")
    seamw = scalar(m, "SeamWidth", 0.6, -1800, 700, "Panels")
    seamdark = scalar(m, "SeamDarken", 0.35, -1800, 800, "Panels")
    selcm = binop(m, unreal.MaterialExpressionMultiply, uvsel, tile, -1400, 600)
    uvp = binop(m, unreal.MaterialExpressionDivide, selcm, psize, -1250, 600)
    fr = unop(m, unreal.MaterialExpressionFrac, uvp, -1100, 600)
    om = unop(m, unreal.MaterialExpressionOneMinus, fr, -1100, 700)
    edge2 = binop(m, unreal.MaterialExpressionMin, fr, om, -950, 650)
    ex = mask(m, edge2, -800, 620, r=True)
    ey = mask(m, edge2, -800, 700, g=True)
    edge = binop(m, unreal.MaterialExpressionMin, ex, ey, -650, 650)
    edgecm = binop(m, unreal.MaterialExpressionMultiply, edge, psize, -500, 650)
    ratio = binop(m, unreal.MaterialExpressionDivide, edgecm, seamw, -350, 650)
    sat = unop(m, unreal.MaterialExpressionSaturate, ratio, -200, 650)
    seam = unop(m, unreal.MaterialExpressionOneMinus, sat, -50, 650)    # 1 on the seam

    # base colour = texture * tint * brightness, darkened in seams
    tint = vec(m, "Tint", (1, 1, 1), -1000, -350)
    bright = scalar(m, "Brightness", 1.0, -1000, -250)
    b1 = binop(m, unreal.MaterialExpressionMultiply, td, tint, -800, -250, aout="RGB")
    b2 = binop(m, unreal.MaterialExpressionMultiply, b1, bright, -650, -250)
    dk = x(m, unreal.MaterialExpressionLinearInterpolate, -450, -250)
    link(b2, "", dk, "A")
    darker = binop(m, unreal.MaterialExpressionMultiply, b2, seamdark, -650, -150)
    link(darker, "", dk, "B")
    link(seam, "", dk, "Alpha")
    MEL.connect_material_property(dk, "", unreal.MaterialProperty.MP_BASE_COLOR)

    # normal with strength
    nstr = scalar(m, "NormalStrength", 0.8, -1000, 200)
    flat = x(m, unreal.MaterialExpressionConstant3Vector, -1000, 280, constant=unreal.LinearColor(0, 0, 1, 1))
    nl = x(m, unreal.MaterialExpressionLinearInterpolate, -600, 150)
    link(flat, "", nl, "A"); link(tn, "RGB", nl, "B"); link(nstr, "", nl, "Alpha")
    MEL.connect_material_property(nl, "", unreal.MaterialProperty.MP_NORMAL)

    # roughness remap from ORM.G (+ seams a touch rougher), AO from ORM.R
    rmin = scalar(m, "RoughnessMin", 0.15, -1000, 450)
    rmax = scalar(m, "RoughnessMax", 0.6, -1000, 530)
    rl = x(m, unreal.MaterialExpressionLinearInterpolate, -600, 450)
    link(rmin, "", rl, "A"); link(rmax, "", rl, "B"); link(to, "G", rl, "Alpha")
    seamr = binop(m, unreal.MaterialExpressionMultiply, seam, seamw, -400, 560)   # small bump
    radd = binop(m, unreal.MaterialExpressionAdd, rl, seamr, -250, 480)
    MEL.connect_material_property(radd, "", unreal.MaterialProperty.MP_ROUGHNESS)
    MEL.connect_material_property(to, "R", unreal.MaterialProperty.MP_AMBIENT_OCCLUSION)

    metal = scalar(m, "Metallic", 0.0, -600, 750)
    MEL.connect_material_property(metal, "", unreal.MaterialProperty.MP_METALLIC)

    ecol = vec(m, "EmissiveColor", (0, 0, 0), -600, 850, "Emissive")
    estr = scalar(m, "EmissiveStrength", 0.0, -600, 950, "Emissive")
    em = binop(m, unreal.MaterialExpressionMultiply, ecol, estr, -400, 900)
    MEL.connect_material_property(em, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)

    MEL.recompile_material(m)
    EAL.save_loaded_asset(m, only_if_is_dirty=False)
    log("built", MASTER)
    return m

def build_glass():
    """Physically plausible architectural glass: thin translucent, low roughness, subtle tint,
    Fresnel-driven opacity so it reads at grazing angles (Lumen reflections on the surface)."""
    if EAL.does_asset_exist(MASTER_GLASS):
        EAL.delete_asset(MASTER_GLASS)
    m = AT.create_asset("M_NV_Glass", ART, unreal.Material, unreal.MaterialFactoryNew())
    m.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
    m.set_editor_property("translucency_lighting_mode", unreal.TranslucencyLightingMode.TLM_SURFACE_PER_PIXEL_LIGHTING)
    m.set_editor_property("used_with_nanite", False)
    tint = vec(m, "Tint", (0.02, 0.035, 0.04), -600, 0)
    MEL.connect_material_property(tint, "", unreal.MaterialProperty.MP_BASE_COLOR)
    rough = scalar(m, "Roughness", 0.04, -600, 120)
    MEL.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    spec = scalar(m, "Specular", 1.0, -600, 200)
    MEL.connect_material_property(spec, "", unreal.MaterialProperty.MP_SPECULAR)
    fres = x(m, unreal.MaterialExpressionFresnel, -800, 320)
    omin = scalar(m, "OpacityFacing", 0.12, -800, 420)
    omax = scalar(m, "OpacityGrazing", 0.6, -800, 500)
    ol = x(m, unreal.MaterialExpressionLinearInterpolate, -500, 400)
    link(omin, "", ol, "A"); link(omax, "", ol, "B"); link(fres, "", ol, "Alpha")
    MEL.connect_material_property(ol, "", unreal.MaterialProperty.MP_OPACITY)
    MEL.recompile_material(m)
    EAL.save_loaded_asset(m, only_if_is_dirty=False)
    log("built", MASTER_GLASS)
    return m

def build_emissive():
    if EAL.does_asset_exist(MASTER_EMIT):
        EAL.delete_asset(MASTER_EMIT)
    m = AT.create_asset("M_NV_Emissive", ART, unreal.Material, unreal.MaterialFactoryNew())
    m.set_editor_property("used_with_nanite", True)
    base = vec(m, "BaseColor", (0.01, 0.01, 0.012), -600, -100)
    MEL.connect_material_property(base, "", unreal.MaterialProperty.MP_BASE_COLOR)
    col = vec(m, "EmissiveColor", (0.2, 1.6, 2.4), -800, 100, "Emissive")
    strn = scalar(m, "EmissiveStrength", 1.0, -800, 220, "Emissive")
    e = binop(m, unreal.MaterialExpressionMultiply, col, strn, -500, 150)
    MEL.connect_material_property(e, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    r = scalar(m, "Roughness", 0.4, -600, 320)
    MEL.connect_material_property(r, "", unreal.MaterialProperty.MP_ROUGHNESS)
    MEL.recompile_material(m)
    EAL.save_loaded_asset(m, only_if_is_dirty=False)
    log("built", MASTER_EMIT)
    return m

# ------------------------------------------------------------------ instances
def mi(name, parent, scalars=None, vectors=None, textures=None):
    path = f"{ART}/{name}"
    if EAL.does_asset_exist(path):
        EAL.delete_asset(path)
    f = unreal.MaterialInstanceConstantFactoryNew()
    inst = AT.create_asset(name, ART, unreal.MaterialInstanceConstant, f)
    MEL.set_material_instance_parent(inst, parent)
    for k, v in (scalars or {}).items():
        MEL.set_material_instance_scalar_parameter_value(inst, k, v)
    for k, v in (vectors or {}).items():
        MEL.set_material_instance_vector_parameter_value(inst, k, unreal.LinearColor(v[0], v[1], v[2], 1))
    for k, p in (textures or {}).items():
        if p:
            MEL.set_material_instance_texture_parameter_value(inst, k, unreal.load_asset(p))
    MEL.update_material_instance(inst)
    EAL.save_loaded_asset(inst, only_if_is_dirty=False)
    log("MI", name, "<-", {k: v.split("/")[-1] for k, v in (textures or {}).items() if v})
    return inst

def tex_args(s):
    return {"BaseColor": s.get("D"), "Normal": s.get("N"), "ORM": s.get("ORM")}

def main():
    CS = "/Game/CitySampleBuildings/Textures"
    def cs(folder, color, normal=None, orm=None):
        return {"D": f"{CS}/{folder}/{color}.{color}",
                "N": f"{CS}/{folder}/{normal or 'T_' + folder + '_N'}.{normal or 'T_' + folder + '_N'}",
                "ORM": f"{CS}/{folder}/{orm or 'T_' + folder + '_AORMD'}.{orm or 'T_' + folder + '_AORMD'}"}
    sets = {
        "painted": cs("PaintedMetal", "T_PaintedMetal_C"),
        "paintedstone": cs("PaintedStone", "T_PaintedStone_White_C"),
        "blackmarble": cs("Granite", "T_Granite_Black_C", "T_Granite_Black_N", "T_Granite_Black_AORMD"),
        "granite": cs("Granite", "T_Granite_White_C"),
        "brushed": cs("MetalBrushed", "T_MetalBrushed_C"),
        "concrete": cs("Limestone", "T_Limestone_Grey_C"),
    }
    complete = {}
    for k, v in sets.items():
        if all(EAL.does_asset_exist(p.split(".")[0]) for p in v.values()):
            complete[k] = v
        else:
            log("missing set", k, [p for p in v.values() if not EAL.does_asset_exist(p.split(".")[0])])
    if not complete:
        log("ERROR no complete texture set found")
        return
    first = next(iter(complete.values()))
    master = build_master(first)
    glass = build_glass()
    emit = build_emissive()

    def pick(*names):
        for n in names:
            if n in complete:
                return complete[n]
        return first

    # Kit A: immaculate ceramic-white panels with a faint cool cast (painted metal, tinted)
    walls = mi("MI_DIR_CeramicPanel", master,
               {"TileSize": 240.0, "PanelSize": 400.0, "SeamWidth": 0.8, "SeamDarken": 0.4,
                "Brightness": 1.0, "RoughnessMin": 0.18, "RoughnessMax": 0.42, "NormalStrength": 0.35},
               {"Tint": (0.92, 0.95, 1.0)}, tex_args(pick("paintedstone", "painted")))
    floor = mi("MI_DIR_PolishedStone", master,
               {"TileSize": 300.0, "PanelSize": 100.0 * 4, "SeamWidth": 0.5, "SeamDarken": 0.55,
                "Brightness": 0.9, "RoughnessMin": 0.06, "RoughnessMax": 0.28, "NormalStrength": 0.25},
               {"Tint": (0.85, 0.87, 0.9)}, tex_args(pick("blackmarble", "granite")))
    titan = mi("MI_DIR_Titanium", master,
               {"TileSize": 160.0, "PanelSize": 200.0, "SeamWidth": 0.4, "SeamDarken": 0.6,
                "Metallic": 1.0, "Brightness": 0.55, "RoughnessMin": 0.22, "RoughnessMax": 0.45,
                "NormalStrength": 0.5},
               {"Tint": (0.42, 0.45, 0.5)}, tex_args(pick("brushed")))
    concrete = mi("MI_DIR_ArchConcrete", master,
                  {"TileSize": 400.0, "PanelSize": 400.0, "SeamWidth": 1.0, "SeamDarken": 0.5,
                   "Brightness": 0.85, "RoughnessMin": 0.45, "RoughnessMax": 0.8},
                  {"Tint": (0.78, 0.8, 0.84)}, tex_args(pick("concrete")))
    city = mi("MI_DIR_CityMass", master,
              {"TileSize": 600.0, "PanelSize": 400.0, "SeamWidth": 6.0, "SeamDarken": 0.2,
               "Brightness": 0.12, "RoughnessMin": 0.3, "RoughnessMax": 0.7},
              {"Tint": (0.6, 0.65, 0.75)}, tex_args(pick("concrete")))
    rubber = mi("MI_DIR_SimMat", master,
                {"TileSize": 200.0, "PanelSize": 200.0, "SeamWidth": 0.6, "SeamDarken": 0.5,
                 "Brightness": 0.5, "RoughnessMin": 0.6, "RoughnessMax": 0.9},
                {"Tint": (0.35, 0.38, 0.42)}, tex_args(pick("concrete")))

    glass_i = mi("MI_DIR_Glass", glass)
    darkglass = mi("MI_DIR_DarkGlass", glass, {"OpacityFacing": 0.85, "OpacityGrazing": 0.97, "Roughness": 0.02},
                   {"Tint": (0.003, 0.004, 0.006)})
    cyan = mi("MI_DIR_CyanLight", emit, {"EmissiveStrength": 6.0}, {"EmissiveColor": (0.2, 1.6, 2.4)})
    data = mi("MI_DIR_DataWall", emit, {"EmissiveStrength": 2.5}, {"EmissiveColor": (0.15, 0.6, 1.0)})
    windows = mi("MI_DIR_CityWindows", emit, {"EmissiveStrength": 3.0}, {"EmissiveColor": (1.4, 0.9, 0.5)})

    swap = {
        "TEMP_M_CrownCeramic": walls,
        "TEMP_M_CrownFloor_v2": floor,
        "TEMP_M_Titanium": titan,
        "TEMP_M_Glass": glass_i,
        "TEMP_M_DarkGlass": darkglass,
        "TEMP_M_CyanEmissive": cyan,
        "TEMP_M_DataWall": data,
        "TEMP_M_CityBlock": city,
        "TEMP_M_CityWindows": windows,
    }
    # graybox concrete-ish leftovers (if any) and the sim-suite floor area
    swap_level(swap)

def swap_level(swap):
    EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    LES = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    changed = 0
    for a in EAS.get_all_level_actors():
        for c in a.get_components_by_class(unreal.StaticMeshComponent):
            n = c.get_num_materials()
            for i in range(n):
                mat = c.get_material(i)
                if mat and mat.get_name() in swap:
                    c.set_material(i, swap[mat.get_name()])
                    changed += 1
    log("material slots swapped:", changed)
    LES.save_current_level()

try:
    main()
finally:
    with open(unreal.Paths.project_saved_dir() + "NV_m5_materials.txt", "w", encoding="utf-8") as fh:
        fh.write("\n".join(REPORT))
