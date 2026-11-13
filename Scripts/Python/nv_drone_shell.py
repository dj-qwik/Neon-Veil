"""Sim drone, collision rework: full-res Nanite shell for rendering, a 18k-tri convex-hull proxy
(SM_SimDrone_BodyCol, one hull per part, lens excluded) as its complex collision, so weapon traces
are cheap and the lower lens (WeakPoint) stays exposed. Per-triangle collision on the 1.3M-tri
source froze the editor while cooking."""
import unreal, gzip, shutil, os
OUT = unreal.Paths.project_saved_dir() + "NV_drone_shell.txt"
SRC = unreal.Paths.project_saved_dir() + "Megascans/drone_nv/"
DST = "/Game/NeonVeil/Fab/SimDrone"
log = []
AT = unreal.AssetToolsHelpers.get_asset_tools()
EAL = unreal.EditorAssetLibrary
SMS = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
if not os.path.exists(SRC + "SM_SimDrone_Shell.obj"):
    shutil.copyfile(SRC + "SM_SimDrone_Body.obj", SRC + "SM_SimDrone_Shell.obj")

def imp(name):
    t = unreal.AssetImportTask()
    t.filename = SRC + name + ".obj"; t.destination_path = DST; t.destination_name = name
    t.automated = True; t.replace_existing = True; t.save = False
    AT.import_asset_tasks([t])
    return unreal.load_asset(DST + "/" + name)

col = imp("SM_SimDrone_BodyCol")
col.set_editor_property("body_setup", col.get_editor_property("body_setup"))
bs = col.get_editor_property("body_setup"); bs.set_editor_property("collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
log.append("col tris %d" % SMS.get_number_verts(col, 0))

shell = imp("SM_SimDrone_Shell")
for i, sl in enumerate(shell.get_editor_property("static_materials")):
    slot = str(sl.get_editor_property("material_slot_name"))
    mi = unreal.load_asset(DST + "/" + slot)
    if mi: shell.set_material(i, mi)
    log.append("slot %s -> %s" % (slot, mi.get_name() if mi else None))
ns = shell.get_editor_property("nanite_settings"); ns.enabled = True; shell.set_editor_property("nanite_settings", ns)
SMS.remove_collisions(shell)
SMS.add_simple_collisions(shell, unreal.ScriptCollisionShapeType.BOX)
bs = shell.get_editor_property("body_setup"); bs.set_editor_property("collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_DEFAULT)
shell.set_editor_property("complex_collision_mesh", col)
log.append("shell complex collision -> %s" % shell.get_editor_property("complex_collision_mesh"))

core = unreal.load_asset(DST + "/SM_SimDrone_Core")
log.append("core trace flag %s" % core.get_editor_property("body_setup").get_editor_property("collision_trace_flag"))
for a in (col, shell, core): EAL.save_loaded_asset(a)

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
d = [a for a in eas.get_all_level_actors() if a.get_actor_label() == "C_Target_Drone"][0]
S = 4.0
rot = unreal.MathLibrary.make_rot_from_xz(unreal.Vector(0, 1, 0), unreal.Vector(-1, 0, 0))
body = d.get_editor_property("body")
body.set_editor_property("override_materials", [])
body.set_static_mesh(shell)
body.set_editor_property("relative_scale3d", unreal.Vector(S, S, S))
body.set_editor_property("relative_rotation", rot)
wp = d.get_editor_property("weak_point")
wp.set_static_mesh(core)
wp.set_editor_property("relative_location", unreal.Vector(0, 0, 0)); wp.set_editor_property("relative_rotation", unreal.Rotator(0, 0, 0)); wp.set_editor_property("relative_scale3d", unreal.Vector(1, 1, 1))
sh = d.get_editor_property("shield_mesh"); sh.set_editor_property("relative_scale3d", unreal.Vector(1 / S, 1 / S, 1 / S)); sh.set_visibility(False)
log.append("body %s wp %s" % (body.static_mesh.get_name(), wp.static_mesh.get_name()))
unreal.EditorLevelLibrary.save_current_level()
open(OUT, "w").write("\n".join(log))
