"""Imports the free Fab 'SciFi Drone' (Oleg Ushenok) as the sim-suite training drone.
Source OBJ is a single untextured mesh; Saved/Megascans/drone_nv/*.obj are a local split
(body vs lower lens 'core') with five material slots assigned per part (see Docs).
Fab content: imported to /Game/NeonVeil/Fab (gitignored), never redistributed."""
import unreal
OUT = unreal.Paths.project_saved_dir() + "NV_drone_import.txt"
SRC = unreal.Paths.project_saved_dir() + "Megascans/drone_nv/"
DST = "/Game/NeonVeil/Fab/SimDrone"
log = []
import gzip, shutil, os
if os.path.exists(SRC + "SM_SimDrone_Body.obj.gz"):
    with gzip.open(SRC + "SM_SimDrone_Body.obj.gz", "rb") as gi, open(SRC + "SM_SimDrone_Body.obj", "wb") as go:
        shutil.copyfileobj(gi, go)
AT = unreal.AssetToolsHelpers.get_asset_tools()
MEL = unreal.MaterialEditingLibrary
EAL = unreal.EditorAssetLibrary

def imp(name):
    t = unreal.AssetImportTask()
    t.filename = SRC + name + ".obj"
    t.destination_path = DST
    t.destination_name = name
    t.automated = True
    t.replace_existing = True
    t.save = False
    AT.import_asset_tasks([t])
    paths = list(t.imported_object_paths)
    log.append("%s -> %s" % (name, paths))
    for p in paths:
        a = unreal.load_asset(p)
        if isinstance(a, unreal.StaticMesh):
            return a
    return unreal.load_asset(DST + "/" + name)

# Master material: params only, Nanite-safe.
MP = DST + "/M_NV_DroneSurface"
if EAL.does_asset_exist(MP):
    mat = unreal.load_asset(MP)
else:
    mat = AT.create_asset("M_NV_DroneSurface", DST, unreal.Material, unreal.MaterialFactoryNew())
    def vp(n, v, x, y):
        e = MEL.create_material_expression(mat, unreal.MaterialExpressionVectorParameter, x, y)
        e.set_editor_property("parameter_name", n); e.set_editor_property("default_value", unreal.LinearColor(*v)); return e
    def sp(n, v, x, y):
        e = MEL.create_material_expression(mat, unreal.MaterialExpressionScalarParameter, x, y)
        e.set_editor_property("parameter_name", n); e.set_editor_property("default_value", v); return e
    bc = vp("BaseColor", (0.8, 0.8, 0.8, 1), -600, -200)
    MEL.connect_material_property(bc, "", unreal.MaterialProperty.MP_BASE_COLOR)
    MEL.connect_material_property(sp("Metallic", 0.0, -600, 0), "", unreal.MaterialProperty.MP_METALLIC)
    MEL.connect_material_property(sp("Roughness", 0.4, -600, 100), "", unreal.MaterialProperty.MP_ROUGHNESS)
    em = vp("EmissiveColor", (0, 0, 0, 1), -800, 250)
    es = sp("EmissiveStrength", 0.0, -800, 400)
    mul = MEL.create_material_expression(mat, unreal.MaterialExpressionMultiply, -400, 300)
    MEL.connect_material_expressions(em, "", mul, "A"); MEL.connect_material_expressions(es, "", mul, "B")
    MEL.connect_material_property(mul, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    mat.set_editor_property("used_with_nanite", True)
    MEL.recompile_material(mat)

SLOTS = {  # name: base, metal, rough, emissive, strength
    "MI_Drone_WhitePaint":  ((0.62, 0.63, 0.65, 1), 0.0, 0.38, (0, 0, 0, 1), 0.0),
    "MI_Drone_OrangePaint": ((0.80, 0.16, 0.03, 1), 0.0, 0.34, (0, 0, 0, 1), 0.0),
    "MI_Drone_DarkMetal":   ((0.03, 0.03, 0.035, 1), 0.6, 0.45, (0, 0, 0, 1), 0.0),
    "MI_Drone_GlowCyan":    ((0.1, 0.6, 0.8, 1), 0.0, 0.1, (0.15, 0.85, 1.0, 1), 40.0),
    "MI_Drone_GlowYellow":  ((0.9, 0.6, 0.05, 1), 0.0, 0.3, (1.0, 0.65, 0.08, 1), 8.0),
}
mis = {}
for n, (b, m, r, e, s) in SLOTS.items():
    p = DST + "/" + n
    if EAL.does_asset_exist(p):
        mi = unreal.load_asset(p)
    else:
        mi = AT.create_asset(n, DST, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    mi.set_editor_property("parent", mat)
    MEL.set_material_instance_vector_parameter_value(mi, "BaseColor", unreal.LinearColor(*b))
    MEL.set_material_instance_scalar_parameter_value(mi, "Metallic", m)
    MEL.set_material_instance_scalar_parameter_value(mi, "Roughness", r)
    MEL.set_material_instance_vector_parameter_value(mi, "EmissiveColor", unreal.LinearColor(*e))
    MEL.set_material_instance_scalar_parameter_value(mi, "EmissiveStrength", s)
    mis[n] = mi

SMS = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
for name in ("SM_SimDrone_Body", "SM_SimDrone_Core"):
    sm = imp(name)
    if not sm:
        log.append("IMPORT FAILED " + name); continue
    mats = sm.get_editor_property("static_materials")
    for i, sl in enumerate(mats):
        slot = str(sl.get_editor_property("material_slot_name"))
        hit = [k for k in mis if k.lower() in slot.lower() or slot.lower() in k.lower()]
        if hit:
            sm.set_material(i, mis[hit[0]])
        log.append("  slot %d %s -> %s" % (i, slot, hit[0] if hit else "?"))
    ns = sm.get_editor_property("nanite_settings"); ns.enabled = True
    sm.set_editor_property("nanite_settings", ns)
    SMS.remove_collisions(sm)
    SMS.add_simple_collisions(sm, unreal.ScriptCollisionShapeType.BOX)
    bs = sm.get_bounds()
    log.append("  bounds origin %s extent %s tris(lod0)=%d" % (bs.origin, bs.box_extent, SMS.get_number_verts(sm, 0)))
    EAL.save_loaded_asset(sm)
for a in list(mis.values()) + [mat]:
    EAL.save_loaded_asset(a)
open(OUT, "w").write("\n".join(log))
