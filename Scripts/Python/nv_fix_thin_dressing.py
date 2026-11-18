"""Scripted dressing kept BlockAll collision where the scripts asked for none (set_collision_enabled at edit time did not
persist). Thin decorative pieces (signs, screen overlays, frames, trim strips, lintels, rods, painted faces: a
vertical side <= 10 cm; floor slabs excluded) then block the player's use-trace in front of terminals and boards. Make those NoCollision; leave bulky props
(planters, vending, bins, totems), gates, walls and interactables alone. Saves the open level.
Report: Saved/NV_fix_thin_<map>.txt"""
import unreal
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
DRESS = ("NVDRESS2", "NVROUTE", "NVM01ART", "NVM01DIR", "NVM01", "NVLANTERN", "NVE", "NVG2")
out = []
n = 0
RESTORE = ("Plat_GapFill_N", "Plat_GapFill_S")   # walkable fillers a first pass of this script cleared by mistake
for a in EAS.get_all_level_actors():
    tg = [str(t) for t in a.tags]
    if not any(t in DRESS for t in tg):
        continue
    lab = a.get_actor_label()
    if lab.startswith(("I_", "G_", "T_", "CP_", "Tut_")) or isinstance(a, unreal.NVInteractableActor):
        continue
    if not isinstance(a, unreal.StaticMeshActor):
        continue
    o, ext = a.get_actor_bounds(False)
    if lab in RESTORE:
        for c in a.get_components_by_class(unreal.PrimitiveComponent):
            if c.get_collision_profile_name() != "BlockAll":
                c.modify(); c.set_collision_profile_name("BlockAll"); n += 1
                out.append("restored BlockAll: %s" % lab)
        continue
    if min(ext.x, ext.y, ext.z) * 2 > 10.0:
        continue
    # floors, slabs and gap fillers are thin in Z but walked on: never touch them
    if ext.z <= min(ext.x, ext.y) and min(ext.x, ext.y) * 2 > 40.0:
        continue
    for c in a.get_components_by_class(unreal.PrimitiveComponent):
        if c.get_collision_profile_name() != "NoCollision":
            c.modify()
            c.set_collision_profile_name("NoCollision")
            n += 1
            out.append("no collision: %-32s %.0fx%.0fx%.0f [%s]" % (lab, ext.x*2, ext.y*2, ext.z*2, ",".join(tg)))
out.insert(0, "%d components changed" % n)
if n:
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
open(unreal.Paths.project_saved_dir() + "NV_fix_thin_%s.txt" % w.get_name(), "w").write("\n".join(out))
