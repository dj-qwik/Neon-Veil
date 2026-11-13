"""Puts the imported Fab sim drone on C_Target_Drone in L_M00_GlassCrown.
Body = SM_SimDrone_Body, WeakPoint = SM_SimDrone_Core (the glowing lower lens, shared pivot)."""
import unreal
OUT = unreal.Paths.project_saved_dir() + "NV_drone_place.txt"
log = []
D = "/Game/NeonVeil/Fab/SimDrone/"
body_sm = unreal.load_asset(D + "SM_SimDrone_Body")
core_sm = unreal.load_asset(D + "SM_SimDrone_Core")
SCALE = 4.0   # source is ~36 cm; sim drone reads at ~1.45 m
# Imported mesh axes: up = -Y, front (eye) = -Z. Want up = +Z, front = actor +X.
rot = unreal.MathLibrary.make_rot_from_xz(unreal.Vector(0, 1, 0), unreal.Vector(-1, 0, 0))
log.append("rot %s  up(-Y)->%s  front(-Z)->%s" % (rot, unreal.MathLibrary.greater_greater_vector_rotator(unreal.Vector(0, -1, 0), rot), unreal.MathLibrary.greater_greater_vector_rotator(unreal.Vector(0, 0, -1), rot)))
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
drone = [a for a in eas.get_all_level_actors() if a.get_actor_label() == "C_Target_Drone"]
if not drone:
    raise RuntimeError("C_Target_Drone not found")
d = drone[0]
body = d.get_editor_property("body"); core = d.get_editor_property("weak_point")
log.append("before: body mesh %s scale %s mats %s" % (body.static_mesh.get_name() if body.static_mesh else None, body.relative_scale3d, [m.get_name() if m else None for m in body.get_materials()]))
log.append("before: core mesh %s mats %s" % (core.static_mesh.get_name() if core.static_mesh else None, [m.get_name() if m else None for m in core.get_materials()]))
for comp, sm in ((body, body_sm), (core, core_sm)):
    comp.set_editor_property("override_materials", [])
    comp.set_static_mesh(sm)
body.set_editor_property("relative_scale3d", unreal.Vector(SCALE, SCALE, SCALE))
body.set_editor_property("relative_rotation", rot)
body.set_editor_property("relative_location", unreal.Vector(0, 0, 0))
core.set_editor_property("relative_scale3d", unreal.Vector(1, 1, 1))
core.set_editor_property("relative_rotation", unreal.Rotator(0, 0, 0))
core.set_editor_property("relative_location", unreal.Vector(0, 0, 0))
sh = d.get_editor_property("shield_mesh")
sh.set_editor_property("relative_scale3d", unreal.Vector(1.0 / SCALE, 1.0 / SCALE, 1.0 / SCALE))
sh.set_visibility(False)  # drone has no shield (BeginPlay also hides it when MaxShield == 0)
log.append("after: body mats %s" % [m.get_name() if m else None for m in body.get_materials()])
log.append("after: core mats %s  core world %s" % ([m.get_name() if m else None for m in core.get_materials()], core.get_world_location()))
log.append("actor %s rot %s" % (d.get_actor_location(), d.get_actor_rotation()))
o, e = d.get_actor_bounds(False)
log.append("actor bounds %s ext %s" % (o, e))
unreal.EditorLevelLibrary.save_current_level()
open(OUT, "w").write("\n".join(log))
