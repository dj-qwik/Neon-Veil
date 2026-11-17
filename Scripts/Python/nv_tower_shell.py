"""Glass Crown: wrap the playable interior (atrium, sim suite, gallery, antechamber, Director's office) in a tower so
it no longer reads as rooms floating in the sky from the Crown Line tram.
 * Curtain wall of dark tinted glass around x 3440..16900, y +-1900, z -200..1500 (see-through from inside, so the
   atrium's skyline view survives), with floor-edge spandrels and mullions.
 * Opaque tower body below the floors down into the fog (-40000) with a procedural lit-window facade, a roof slab
   and a glowing crown band; an opening in the west face where the skybridge enters.
Idempotent (rebuilds folder Tower_Shell). Report: Saved/NV_tower_shell.txt"""
import unreal

OUT = []
def log(*a):
    OUT.append(" ".join(str(x) for x in a))

EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
EAL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary
AT = unreal.AssetToolsHelpers.get_asset_tools()
V = unreal.Vector
FOLDER = "Tower_Shell"
MATDIR = "/Game/NeonVeil/Materials/Tower"
CUBE = unreal.load_asset("/Engine/BasicShapes/Cube")

X0, X1 = 3440.0, 16900.0
Y0, Y1 = -1900.0, 1900.0
ZF, ZR = -200.0, 1500.0          # glass from floor-edge to roof
ZB = -40000.0                    # tower body bottom (lost in the fog)
T = 30.0                         # wall thickness
BRIDGE = (-330.0, 330.0, -60.0, 510.0)   # skybridge entry hole in the west face (y0, y1, z0, z1)

def material(name):
    path = f"{MATDIR}/{name}"
    if EAL.does_asset_exist(path):
        m = unreal.load_asset(path)
        MEL.delete_all_material_expressions(m)
    else:
        m = AT.create_asset(name, MATDIR, unreal.Material, unreal.MaterialFactoryNew())
    return m

def ex(m, cls, x, y, **p):
    e = MEL.create_material_expression(m, cls, x, y)
    for k, v in p.items():
        e.set_editor_property(k, v)
    return e

def k1(m, v, x, y):
    return ex(m, unreal.MaterialExpressionConstant, x, y, r=v)

def k3(m, c, x, y):
    return ex(m, unreal.MaterialExpressionConstant3Vector, x, y, constant=unreal.LinearColor(c[0], c[1], c[2], 1))

def op(m, cls, a, b, x, y):
    e = ex(m, cls, x, y)
    MEL.connect_material_expressions(a, "", e, "A")
    MEL.connect_material_expressions(b, "", e, "B")
    return e

def one(m, cls, src, x, y, **p):
    e = ex(m, cls, x, y, **p)
    MEL.connect_material_expressions(src, "", e, "")
    return e

def glass_material():
    m = material("M_NV_TowerGlass")
    m.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
    m.set_editor_property("translucency_lighting_mode", unreal.TranslucencyLightingMode.TLM_SURFACE)
    m.set_editor_property("two_sided", True)
    MEL.connect_material_property(k3(m, (0.01, 0.025, 0.04), -400, 0), "", unreal.MaterialProperty.MP_BASE_COLOR)
    MEL.connect_material_property(k1(m, 0.9, -400, 100), "", unreal.MaterialProperty.MP_METALLIC)
    MEL.connect_material_property(k1(m, 0.08, -400, 200), "", unreal.MaterialProperty.MP_ROUGHNESS)
    fres = ex(m, unreal.MaterialExpressionFresnel, -700, 300, exponent=3.0, base_reflect_fraction=0.0)
    opac = op(m, unreal.MaterialExpressionAdd, op(m, unreal.MaterialExpressionMultiply, fres, k1(m, 0.45, -700, 420), -550, 300),
              k1(m, 0.32, -550, 420), -400, 300)
    MEL.connect_material_property(opac, "", unreal.MaterialProperty.MP_OPACITY)
    MEL.recompile_material(m)
    EAL.save_loaded_asset(m)
    return m

def facade_material():
    """Dark tower skin with a world-aligned grid of windows, roughly a third of them lit (hash per cell)."""
    m = material("M_NV_TowerFacade")
    wp = ex(m, unreal.MaterialExpressionWorldPosition, -1800, 0)
    mx = one(m, unreal.MaterialExpressionComponentMask, wp, -1600, -100, r=True, g=False, b=False, a=False)
    my = one(m, unreal.MaterialExpressionComponentMask, wp, -1600, 0, r=False, g=True, b=False, a=False)
    mz = one(m, unreal.MaterialExpressionComponentMask, wp, -1600, 100, r=False, g=False, b=True, a=False)
    u = op(m, unreal.MaterialExpressionMultiply, op(m, unreal.MaterialExpressionAdd, mx, my, -1450, -50), k1(m, 1 / 170.0, -1450, 50), -1300, -50)
    v = op(m, unreal.MaterialExpressionMultiply, mz, k1(m, 1 / 330.0, -1450, 150), -1300, 100)
    fu, fv = one(m, unreal.MaterialExpressionFrac, u, -1150, -50), one(m, unreal.MaterialExpressionFrac, v, -1150, 100)
    def edge(f, lo, hi, y):
        a = one(m, unreal.MaterialExpressionSaturate, op(m, unreal.MaterialExpressionMultiply,
                op(m, unreal.MaterialExpressionSubtract, f, k1(m, lo, -1000, y + 40), -950, y), k1(m, 40.0, -1000, y + 80), -850, y), -750, y)
        b = one(m, unreal.MaterialExpressionSaturate, op(m, unreal.MaterialExpressionMultiply,
                op(m, unreal.MaterialExpressionSubtract, k1(m, hi, -1000, y + 120), f, -950, y + 120), k1(m, 40.0, -1000, y + 160), -850, y + 120), -750, y + 120)
        return op(m, unreal.MaterialExpressionMultiply, a, b, -650, y)
    win = op(m, unreal.MaterialExpressionMultiply, edge(fu, 0.18, 0.82, -300), edge(fv, 0.28, 0.78, 0), -550, -150)
    # per-cell hash: frac(sin(floor(u)*12.9898 + floor(v)*78.233) * 43758.5)
    cu, cv = one(m, unreal.MaterialExpressionFloor, u, -1150, 250), one(m, unreal.MaterialExpressionFloor, v, -1150, 350)
    h = op(m, unreal.MaterialExpressionAdd, op(m, unreal.MaterialExpressionMultiply, cu, k1(m, 12.9898, -1050, 250), -950, 250),
           op(m, unreal.MaterialExpressionMultiply, cv, k1(m, 78.233, -1050, 350), -950, 350), -850, 300)
    s = one(m, unreal.MaterialExpressionSine, h, -750, 300, period=6.283185)
    hf = one(m, unreal.MaterialExpressionFrac, op(m, unreal.MaterialExpressionMultiply, s, k1(m, 43758.5, -700, 400), -650, 300), -550, 300)
    lit = one(m, unreal.MaterialExpressionSaturate, op(m, unreal.MaterialExpressionMultiply,
              op(m, unreal.MaterialExpressionSubtract, hf, k1(m, 0.64, -500, 400), -450, 300), k1(m, 30.0, -450, 400), -350, 300), -250, 300)
    warm = op(m, unreal.MaterialExpressionMultiply, op(m, unreal.MaterialExpressionMultiply, win, lit, -400, 0),
              k3(m, (1.5, 0.95, 0.5), -400, 120), -250, 0)
    MEL.connect_material_property(warm, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    MEL.connect_material_property(k3(m, (0.012, 0.014, 0.02), -250, -200), "", unreal.MaterialProperty.MP_BASE_COLOR)
    MEL.connect_material_property(k1(m, 0.6, -250, -120), "", unreal.MaterialProperty.MP_METALLIC)
    MEL.connect_material_property(k1(m, 0.25, -250, -60), "", unreal.MaterialProperty.MP_ROUGHNESS)
    MEL.recompile_material(m)
    EAL.save_loaded_asset(m)
    return m

def flat(name, base, emis=None, metal=0.7, rough=0.35):
    m = material(name)
    MEL.connect_material_property(k3(m, base, -400, 0), "", unreal.MaterialProperty.MP_BASE_COLOR)
    if emis:
        MEL.connect_material_property(k3(m, emis, -400, 100), "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    MEL.connect_material_property(k1(m, metal, -400, 200), "", unreal.MaterialProperty.MP_METALLIC)
    MEL.connect_material_property(k1(m, rough, -400, 300), "", unreal.MaterialProperty.MP_ROUGHNESS)
    MEL.recompile_material(m)
    EAL.save_loaded_asset(m)
    return m

def box(label, lo, hi, mat):
    c = V((lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, (lo[2] + hi[2]) / 2)
    a = EAS.spawn_actor_from_class(unreal.StaticMeshActor, c, unreal.Rotator())
    a.set_actor_label(label)
    a.set_folder_path(FOLDER)
    sm = a.static_mesh_component
    sm.set_static_mesh(CUBE)
    sm.set_material(0, mat)
    sm.set_collision_profile_name("NoCollision")
    sm.set_editor_property("can_ever_affect_navigation", False)
    a.set_actor_scale3d(V((hi[0] - lo[0]) / 100.0, (hi[1] - lo[1]) / 100.0, (hi[2] - lo[2]) / 100.0))
    return a

def main():
    for a in EAS.get_all_level_actors():
        if str(a.get_folder_path()) == FOLDER:
            EAS.destroy_actor(a)
    glass, facade = glass_material(), facade_material()
    frame = flat("M_NV_TowerFrame", (0.02, 0.022, 0.026))
    band = flat("M_NV_TowerCrownBand", (0.0, 0.0, 0.0), (0.4, 2.4, 3.6), 0.0, 0.5)
    n = 0
    # --- curtain wall (glass) ---
    # north / south / east faces
    box("TS_Glass_N", (X0, Y1 - T, ZF), (X1, Y1, ZR), glass); box("TS_Glass_S", (X0, Y0, ZF), (X1, Y0 + T, ZR), glass)
    box("TS_Glass_E", (X1 - T, Y0, ZF), (X1, Y1, ZR), glass)
    # west face around the skybridge hole
    by0, by1, bz0, bz1 = BRIDGE
    box("TS_Glass_W_S", (X0, Y0, ZF), (X0 + T, by0, ZR), glass); box("TS_Glass_W_N", (X0, by1, ZF), (X0 + T, Y1, ZR), glass)
    box("TS_Glass_W_Top", (X0, by0, bz1), (X0 + T, by1, ZR), glass)
    n += 6
    # --- spandrels (floor edge, mid, roof edge) and mullions ---
    for i, (z0, z1) in enumerate(((ZF, ZF + 180), (590, 620), (990, 1020), (ZR - 60, ZR))):
        box(f"TS_Span{i}_N", (X0 - 10, Y1 - T - 10, z0), (X1 + 10, Y1 + 10, z1), frame)
        box(f"TS_Span{i}_S", (X0 - 10, Y0 - 10, z0), (X1 + 10, Y0 + T + 10, z1), frame)
        box(f"TS_Span{i}_E", (X1 - T - 10, Y0 - 10, z0), (X1 + 10, Y1 + 10, z1), frame)
        for side, (ya, yb) in (("WS", (Y0 - 10, by0)), ("WN", (by1, Y1 + 10))):
            box(f"TS_Span{i}_{side}", (X0 - 10, ya, z0), (X0 + T + 10, yb, z1), frame)
        n += 5
    step = 600.0
    x = X0
    while x <= X1 + 1:
        box(f"TS_Mull_N{int(x)}", (x - 8, Y1 - 4, ZF), (x + 8, Y1 + 18, ZR), frame)
        box(f"TS_Mull_S{int(x)}", (x - 8, Y0 - 18, ZF), (x + 8, Y0 + 4, ZR), frame)
        n += 2
        x += step
    y = Y0
    while y <= Y1 + 1:
        box(f"TS_Mull_E{int(y)}", (X1 - 4, y - 8, ZF), (X1 + 18, y + 8, ZR), frame)
        if not (by0 - 20 < y < by1 + 20):
            box(f"TS_Mull_W{int(y)}", (X0 - 18, y - 8, ZF), (X0 + 4, y + 8, ZR), frame)
        n += 2
        y += step
    # --- tower body below the floors, roof, crown ---
    box("TS_Body", (X0 - 40, Y0 - 40, ZB), (X1 + 40, Y1 + 40, ZF), facade)
    box("TS_Roof", (X0 - 40, Y0 - 40, ZR), (X1 + 40, Y1 + 40, ZR + 120), frame)
    box("TS_Crown", (X0 + 200, Y0 + 200, ZR + 120), (X1 - 200, Y1 - 200, ZR + 2600), facade)
    box("TS_CrownBand0", (X0 + 180, Y0 + 180, ZR + 900), (X1 - 180, Y1 - 180, ZR + 940), band)
    box("TS_CrownBand1", (X0 + 180, Y0 + 180, ZR + 2560), (X1 - 180, Y1 - 180, ZR + 2620), band)
    # skybridge entry: a dark frame around the hole so the bridge visibly plugs into the facade
    box("TS_BridgeCollar_Top", (X0 - 60, by0 - 60, bz1), (X0 + T, by1 + 60, bz1 + 60), frame)
    box("TS_BridgeCollar_S", (X0 - 60, by0 - 60, ZF), (X0 + T, by0, bz1), frame)
    box("TS_BridgeCollar_N", (X0 - 60, by1, ZF), (X0 + T, by1 + 60, bz1), frame)
    n += 8
    log("shell pieces", n)
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    log("saved")

try:
    main()
except Exception:
    import traceback
    log(traceback.format_exc())
finally:
    open(unreal.Paths.project_saved_dir() + "NV_tower_shell.txt", "w").write("\n".join(OUT))
