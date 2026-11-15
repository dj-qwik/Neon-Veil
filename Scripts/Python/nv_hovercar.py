"""Hover-car mesh for the flying traffic (replaces the plain cube), built with Geometry Script.
Symmetric front/back (the traffic streams fly reverse-lane cars unrotated), modelled at final size (about
500 x 170 x 75 cm) and then normalised to a 100 cm box, because NVTrafficStream scales a unit cube per lane.
Slots: 0 = light bars (the lane's head/tail light material is set on slot 0 per direction: front bar shows the
headlight colour, back bar red, side strips a dim running light), 1 = hull (dark lit metal), 2 = canopy,
3 = thrusters (four glowing pads and a lit keel under the belly, so cars read as vehicles from below).
Points every NVTrafficStream in the level at it. Idempotent. Report: Saved/NV_hovercar.txt
NOTE: UE 5.8's Python/GeometryScript binding crashed the editor at the next garbage collection after this ran
(in python311 while freeing the scratch DynamicMesh). The script saves everything itself, so after running it,
restart the editor before doing more work."""
import unreal
EAL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary
AT = unreal.AssetToolsHelpers.get_asset_tools()
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
GP = unreal.GeometryScript_Primitives
GT = unreal.GeometryScript_MeshTransforms
GA = unreal.GeometryScript_AssetUtils
V = unreal.Vector
OUT = []
D = "/Game/NeonVeil/Vehicles"
MESH = f"{D}/SM_NV_HoverCar"
MATDIR = "/Game/NeonVeil/Materials/Prologue"

def glow_mi(name, color, glow):
    path = f"{D}/{name}"
    mi = unreal.load_asset(path) if EAL.does_asset_exist(path) else AT.create_asset(name, D, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    MEL.set_material_instance_parent(mi, unreal.load_asset(f"{MATDIR}/M_NV_Glow"))
    MEL.set_material_instance_vector_parameter_value(mi, "Color", unreal.LinearColor(*color, 1))
    MEL.set_material_instance_scalar_parameter_value(mi, "Glow", glow)
    EAL.save_loaded_asset(mi)
    return mi

def hull_material():
    path = f"{D}/M_NV_CarHull"
    if EAL.does_asset_exist(path):
        return unreal.load_asset(path)
    m = AT.create_asset("M_NV_CarHull", D, unreal.Material, unreal.MaterialFactoryNew())
    m.set_editor_property("used_with_instanced_static_meshes", True)   # traffic is instanced; without it -> default material
    bc = MEL.create_material_expression(m, unreal.MaterialExpressionConstant3Vector, -400, -100)
    bc.set_editor_property("constant", unreal.LinearColor(0.035, 0.04, 0.05, 1))
    mt = MEL.create_material_expression(m, unreal.MaterialExpressionConstant, -400, 50); mt.set_editor_property("r", 0.85)
    rg = MEL.create_material_expression(m, unreal.MaterialExpressionConstant, -400, 150); rg.set_editor_property("r", 0.3)
    MEL.connect_material_property(bc, "", unreal.MaterialProperty.MP_BASE_COLOR)
    MEL.connect_material_property(mt, "", unreal.MaterialProperty.MP_METALLIC)
    MEL.connect_material_property(rg, "", unreal.MaterialProperty.MP_ROUGHNESS)
    MEL.recompile_material(m)
    EAL.save_loaded_asset(m)
    return m

HULL = hull_material()
_glow = unreal.load_asset(f"{MATDIR}/M_NV_Glow")
if not _glow.get_editor_property("used_with_instanced_static_meshes"):
    _glow.set_editor_property("used_with_instanced_static_meshes", True)
    MEL.recompile_material(_glow); EAL.save_loaded_asset(_glow)
CANOPY = glow_mi("MI_NV_CarCanopy", (0.05, 0.16, 0.22), 1.2)
THRUST = glow_mi("MI_NV_CarThruster", (0.3, 0.85, 1.0), 22.0)
LIGHTS = unreal.load_asset("/Game/NeonVeil/Materials/FX/MI_NV_TrafficCar_White_Fwd")

# a Python-created DynamicMesh was collected under Python at the next GC (editor crash); give it an outer and drop it at the end
mesh = unreal.new_object(unreal.DynamicMesh, name="NV_HoverCarBuild")
def opts(mid):
    o = unreal.GeometryScriptPrimitiveOptions()
    o.set_editor_property("material_id", mid)
    return o
def T(loc=(0, 0, 0), rot=None, scale=(1, 1, 1)):
    return unreal.Transform(V(*loc), rot or unreal.Rotator(), V(*scale))
CENTER = unreal.GeometryScriptPrimitiveOriginMode.CENTER
P90 = unreal.Rotator(roll=0, pitch=90, yaw=0)     # capsule/cylinder axis (local Z) -> along X
# hull: a long flattened capsule; local X -> height, Y -> width, Z -> length after the pitch
GP.append_capsule(mesh, opts(1), T((0, 0, 0), P90, (0.36, 1.7, 1.0)), 50.0, 400.0, 6, 16, 4, CENTER)
# canopy: a smaller flattened capsule on top, mid-ship
GP.append_capsule(mesh, opts(2), T((0, 0, 14), P90, (0.42, 1.25, 1.0)), 40.0, 140.0, 5, 14, 2, CENTER)
# side skirts and a belly keel (hull)
for s in (-1, 1):
    GP.append_box(mesh, opts(1), T((0, s * 80, -8)), 380.0, 14.0, 16.0)
    GP.append_box(mesh, opts(0), T((0, s * 88, -2)), 330.0, 3.0, 4.0)          # running-light strip
GP.append_box(mesh, opts(1), T((0, 0, -20)), 300.0, 60.0, 10.0)
GP.append_box(mesh, opts(3), T((0, 0, -25.5)), 240.0, 8.0, 2.0)               # lit keel line
# four thruster pods under the belly: housing + glowing face
for x in (-150, 150):
    for y in (-52, 52):
        GP.append_cylinder(mesh, opts(1), T((x, y, -30)), 26.0, 12.0, 16, 1, True)
        GP.append_cylinder(mesh, opts(3), T((x, y, -31.5)), 20.0, 2.0, 16, 1, True)
# light bars across each end (headlight / tail light colour comes from the face direction)
for s in (-1, 1):
    GP.append_box(mesh, opts(0), T((s * 236, 0, 4)), 8.0, 120.0, 6.0)
    GP.append_box(mesh, opts(1), T((s * 200, 0, 20)), 20.0, 150.0, 4.0)        # small spoiler ridge
# normalise to a 100 cm cube: NVTrafficStream scales by VehicleScale (about 5 x 1.8 x 1)
GT.scale_mesh(mesh, V(1 / 5.0, 1 / 1.8, 1 / 0.8), V(0, 0, 0), True)

o = unreal.GeometryScriptCreateNewStaticMeshAssetOptions()
o.set_editor_property("enable_recompute_normals", False)
o.set_editor_property("enable_recompute_tangents", True)
o.set_editor_property("enable_nanite", False)
o.set_editor_property("enable_collision", False)
if EAL.does_asset_exist(MESH):
    sm = unreal.load_asset(MESH)
    GA.copy_mesh_to_static_mesh(mesh, sm, unreal.GeometryScriptCopyMeshToAssetOptions(), unreal.GeometryScriptMeshWriteLOD())
else:
    fn = None
    for cls in ("GeometryScript_NewAssetUtils", "GeometryScript_CreateNewAsset", "GeometryScript_AssetUtils"):
        c = getattr(unreal, cls, None)
        if c and hasattr(c, "create_new_static_mesh_asset_from_mesh"):
            fn = c.create_new_static_mesh_asset_from_mesh
            break
    if fn is None:
        names = [n for n in dir(unreal) if n.startswith("GeometryScript_")]
        raise RuntimeError("no create_new_static_mesh_asset_from_mesh; GeometryScript classes: " + ", ".join(names))
    res = fn(mesh, MESH, o)
    sm, outcome = (res[0], res[1]) if isinstance(res, tuple) else (res, None)
    OUT.append(f"create: {outcome}")
mats = []
for i, (name, m) in enumerate((("Lights", LIGHTS), ("Hull", HULL), ("Canopy", CANOPY), ("Thruster", THRUST))):
    sm_ = unreal.StaticMaterial()
    sm_.set_editor_property("material_interface", m)
    sm_.set_editor_property("material_slot_name", name)
    mats.append(sm_)
sm.set_editor_property("static_materials", mats)
EAL.save_loaded_asset(sm)
b = sm.get_bounding_box()
OUT.append(f"mesh {sm.get_path_name()} bounds {b.min} {b.max} slots {len(mats)}")

n = 0
for a in EAS.get_all_level_actors():
    if isinstance(a, unreal.NVTrafficStream):
        a.set_editor_property("vehicle_mesh", sm)
        n += 1
OUT.append(f"streams updated: {n}")
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
open(unreal.Paths.project_saved_dir() + "NV_hovercar.txt", "w").write("\n".join(OUT))
del mesh
import gc; gc.collect()
