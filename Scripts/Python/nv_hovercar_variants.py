"""Two more flying-car designs for the traffic, plus a second hover-pad colour (Geometry Script).
  SM_NV_HoverCar_Wedge  - low, wide interceptor: sloped nose, bubble canopy, twin tail fins, big rear pads, accent
                          side stripes. Crimson paint.
  SM_NV_HoverCar_Hauler - boxy cargo hauler: cab + ribbed cargo pod, roof beacon strip, six pads. Amber paint.
Same slot layout as SM_NV_HoverCar (0 lights, 1 hull, 2 canopy, 3 accent/thrusters) and the same normalisation, so
NVTrafficStream mixes them freely (ExtraMeshes) and tints slot 3 per car (AccentMaterials: cyan / magenta).
Both have a nose (+X); NVTrafficStream turns reverse-lane cars round. Only builds assets; nv_traffic_variety.py
points the streams at them. Same Geometry Script GC hazard as nv_hovercar.py: restart the editor afterwards.
Report: Saved/NV_hovercar_variants.txt"""
import unreal
EAL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary
AT = unreal.AssetToolsHelpers.get_asset_tools()
GP = unreal.GeometryScript_Primitives
GT = unreal.GeometryScript_MeshTransforms
GA = unreal.GeometryScript_AssetUtils
V = unreal.Vector
OUT = []
D = "/Game/NeonVeil/Vehicles"
MATDIR = "/Game/NeonVeil/Materials/Prologue"
CENTER = unreal.GeometryScriptPrimitiveOriginMode.CENTER

def glow_mi(name, color, glow):
    path = f"{D}/{name}"
    mi = unreal.load_asset(path) if EAL.does_asset_exist(path) else AT.create_asset(name, D, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    MEL.set_material_instance_parent(mi, unreal.load_asset(f"{MATDIR}/M_NV_Glow"))
    MEL.set_material_instance_vector_parameter_value(mi, "Color", unreal.LinearColor(*color, 1))
    MEL.set_material_instance_scalar_parameter_value(mi, "Glow", glow)
    EAL.save_loaded_asset(mi)
    return mi

def paint_master():
    path = f"{D}/M_NV_CarPaint"
    if EAL.does_asset_exist(path):
        return unreal.load_asset(path)       # never rebuild an existing graph (editor crash)
    m = AT.create_asset("M_NV_CarPaint", D, unreal.Material, unreal.MaterialFactoryNew())
    m.set_editor_property("used_with_instanced_static_meshes", True)
    bc = MEL.create_material_expression(m, unreal.MaterialExpressionVectorParameter, -400, -100)
    bc.set_editor_property("parameter_name", "Paint")
    bc.set_editor_property("default_value", unreal.LinearColor(0.1, 0.1, 0.1, 1))
    mt = MEL.create_material_expression(m, unreal.MaterialExpressionScalarParameter, -400, 50)
    mt.set_editor_property("parameter_name", "Metallic"); mt.set_editor_property("default_value", 0.6)
    rg = MEL.create_material_expression(m, unreal.MaterialExpressionScalarParameter, -400, 150)
    rg.set_editor_property("parameter_name", "Roughness"); rg.set_editor_property("default_value", 0.28)
    MEL.connect_material_property(bc, "", unreal.MaterialProperty.MP_BASE_COLOR)
    MEL.connect_material_property(mt, "", unreal.MaterialProperty.MP_METALLIC)
    MEL.connect_material_property(rg, "", unreal.MaterialProperty.MP_ROUGHNESS)
    MEL.recompile_material(m)
    EAL.save_loaded_asset(m)
    return m

def paint_mi(name, color, metallic, rough):
    path = f"{D}/{name}"
    mi = unreal.load_asset(path) if EAL.does_asset_exist(path) else AT.create_asset(name, D, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    MEL.set_material_instance_parent(mi, PAINT)
    MEL.set_material_instance_vector_parameter_value(mi, "Paint", unreal.LinearColor(*color, 1))
    MEL.set_material_instance_scalar_parameter_value(mi, "Metallic", metallic)
    MEL.set_material_instance_scalar_parameter_value(mi, "Roughness", rough)
    EAL.save_loaded_asset(mi)
    return mi

PAINT = paint_master()
CRIMSON = paint_mi("MI_NV_CarPaint_Crimson", (0.20, 0.012, 0.03), 0.7, 0.22)
AMBER = paint_mi("MI_NV_CarPaint_Amber", (0.38, 0.20, 0.015), 0.35, 0.45)
CANOPY = unreal.load_asset(f"{D}/MI_NV_CarCanopy")
THRUST = unreal.load_asset(f"{D}/MI_NV_CarThruster")
MAGENTA = glow_mi("MI_NV_CarThruster_Magenta", (1.0, 0.1, 0.62), 22.0)
LIGHTS = unreal.load_asset("/Game/NeonVeil/Materials/FX/MI_NV_TrafficCar_White_Fwd")

def opts(mid):
    o = unreal.GeometryScriptPrimitiveOptions()
    o.set_editor_property("material_id", mid)
    return o
def T(loc=(0, 0, 0), rot=None, scale=(1, 1, 1)):
    return unreal.Transform(V(*loc), rot or unreal.Rotator(), V(*scale))
def box(m, mid, loc, size, rot=None):
    GP.append_box(m, opts(mid), T(loc, rot), size[0], size[1], size[2], 0, 0, 0, CENTER)
def cyl(m, mid, loc, r, h, steps=16):
    GP.append_cylinder(m, opts(mid), T(loc), r, h, steps, 0, True, CENTER)
def pad(m, loc, r_house, r_glow):
    cyl(m, 1, loc, r_house, 12.0)
    cyl(m, 3, (loc[0], loc[1], loc[2] - 6.5), r_glow, 2.0)
P90 = unreal.Rotator(roll=0, pitch=90, yaw=0)

def wedge(m):
    box(m, 1, (0, 0, 0), (400, 150, 30))                                      # main body
    box(m, 1, (250, 0, -3), (130, 128, 18), unreal.Rotator(roll=0, pitch=-7, yaw=0))   # sloped nose
    box(m, 1, (-215, 0, 4), (70, 176, 36))                                    # rear deck
    box(m, 1, (-40, 0, -22), (300, 90, 14))                                   # belly plate
    GP.append_capsule(m, opts(2), T((50, 0, 20), P90, (0.38, 1.0, 1.0)), 34.0, 120.0, 5, 14, 2, CENTER)  # canopy
    for s in (-1, 1):
        box(m, 1, (-110, s * 92, 2), (170, 14, 34))                            # side intakes
        box(m, 1, (-205, s * 66, 36), (54, 6, 40), unreal.Rotator(roll=0, pitch=-18, yaw=0))  # tail fins
        box(m, 3, (30, s * 76, 9), (300, 2, 3))                               # accent stripe
        box(m, 3, (-205, s * 69, 50), (30, 2, 4))                              # fin tip light
        pad(m, (-150, s * 58, -24), 34.0, 28.0)                               # big rear pads
        pad(m, (175, s * 46, -18), 18.0, 14.0)                                # small front pads
        box(m, 0, (300, s * 46, 0), (8, 30, 4))                               # split headlights
    box(m, 3, (-40, 0, -29.5), (220, 6, 2))                                   # keel glow
    box(m, 0, (-252, 0, 8), (6, 164, 6))                                      # tail bar

def hauler(m):
    box(m, 1, (195, 0, 6), (130, 172, 72))                                     # cab
    box(m, 2, (246, 0, 30), (60, 150, 4), unreal.Rotator(roll=0, pitch=-38, yaw=0))   # windscreen
    box(m, 1, (-55, 0, 18), (370, 192, 92))                                    # cargo pod
    for x in (-220, -138, -56, 26, 108):
        box(m, 1, (x, 0, 18), (10, 198, 98))                                   # pod ribs
    box(m, 1, (0, 0, -30), (470, 124, 12))                                     # chassis rail
    box(m, 3, (-55, 0, 66), (310, 6, 3))                                       # roof beacon strip
    for s in (-1, 1):
        box(m, 3, (-55, s * 99, -14), (330, 2, 3))                             # skirt accent
        box(m, 0, (262, s * 62, -4), (4, 40, 10))                              # headlights
        box(m, 0, (-242, s * 80, 50), (4, 22, 22))                             # tail clusters
        for x in (-195, -55, 85):
            pad(m, (x, s * 68, -40), 26.0, 20.0)
    box(m, 0, (-242, 0, -10), (4, 150, 6))                                     # tail bar

def build(name, fn, hull):
    path = f"{D}/{name}"
    m = unreal.new_object(unreal.DynamicMesh, name=f"NV_{name}_Build")
    fn(m)
    GT.scale_mesh(m, V(1 / 5.0, 1 / 1.8, 1 / 0.8), V(0, 0, 0), True)    # same normalisation as SM_NV_HoverCar
    if EAL.does_asset_exist(path):
        sm = unreal.load_asset(path)
        GA.copy_mesh_to_static_mesh(m, sm, unreal.GeometryScriptCopyMeshToAssetOptions(), unreal.GeometryScriptMeshWriteLOD())
    else:
        o = unreal.GeometryScriptCreateNewStaticMeshAssetOptions()
        o.set_editor_property("enable_recompute_normals", False)
        o.set_editor_property("enable_recompute_tangents", True)
        o.set_editor_property("enable_nanite", False)
        o.set_editor_property("enable_collision", False)
        fnc = None
        for cls in ("GeometryScript_NewAssetUtils", "GeometryScript_CreateNewAsset", "GeometryScript_AssetUtils"):
            c = getattr(unreal, cls, None)
            if c and hasattr(c, "create_new_static_mesh_asset_from_mesh"):
                fnc = c.create_new_static_mesh_asset_from_mesh
                break
        res = fnc(m, path, o)
        sm = res[0] if isinstance(res, tuple) else res
    mats = []
    for slot, mat in (("Lights", LIGHTS), ("Hull", hull), ("Canopy", CANOPY), ("Thruster", THRUST)):
        s_ = unreal.StaticMaterial()
        s_.set_editor_property("material_interface", mat)
        s_.set_editor_property("material_slot_name", slot)
        mats.append(s_)
    sm.set_editor_property("static_materials", mats)
    EAL.save_loaded_asset(sm)
    b = sm.get_bounding_box()
    OUT.append(f"{name}: bounds {b.min} {b.max}")
    return m

keep = [build("SM_NV_HoverCar_Wedge", wedge, CRIMSON), build("SM_NV_HoverCar_Hauler", hauler, AMBER)]
OUT.append("magenta pad MI: " + MAGENTA.get_path_name())
open(unreal.Paths.project_saved_dir() + "NV_hovercar_variants.txt", "w").write("\n".join(OUT))
del keep
import gc; gc.collect()
