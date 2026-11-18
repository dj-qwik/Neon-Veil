"""M00 Glass Crown atrium: move the visitor lounge (sofa, two armchairs, table) off the walkway centreline, where the
sofa blocked the doorway from the entry corridor, into the south-west corner of the atrium (west of the guard loop,
under the mezzanine): sofa against the south wall, table in front, an armchair at each end. Absolute targets, so re-runnable.
Saves the level. Report: Saved/NV_m00_lounge.txt"""
import unreal
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
LES = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
UES = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
MAP = "/Game/NeonVeil/Maps/M00/L_M00_GlassCrown"
if not UES.get_editor_world().get_path_name().startswith(MAP):
    LES.load_level(MAP)
# (x, y, yaw). Sofa: long axis along X, seat faces +Y at yaw 0, so it backs onto the south wall facing into the room.
# Armchairs face local +X: angled in toward the table from either end.
TARGET = {"B_Lounge_Sofa": (3760, -1020, 0), "B_Lounge_Table": (3760, -870, 0),
          "B_Lounge_ChairN": (3600, -830, -15), "B_Lounge_ChairS": (3920, -830, 195)}
OUT = []
for a in EAS.get_all_level_actors():
    t = TARGET.get(a.get_actor_label())
    if t:
        old = a.get_actor_location()
        a.set_actor_location(unreal.Vector(t[0], t[1], old.z), False, False)
        a.set_actor_rotation(unreal.Rotator(roll=0, pitch=0, yaw=t[2]), False)
        o, e = a.get_actor_bounds(False)
        OUT.append("%s (%d,%d) -> (%d,%d) bounds o=(%d,%d) e=(%d,%d)" % (a.get_actor_label(), old.x, old.y, t[0], t[1], o.x, o.y, e.x, e.y))
# anything else the moved group now overlaps
for a in EAS.get_all_level_actors():
    if a.get_actor_label() in TARGET or not isinstance(a, unreal.StaticMeshActor):
        continue
    o, e = a.get_actor_bounds(False)
    if e.x > 1500 or e.y > 1500 or o.z - e.z > 200 or o.z + e.z < 5:
        continue
    if o.x + e.x > 3560 and o.x - e.x < 4000 and o.y + e.y > -1060 and o.y - e.y < -290:
        OUT.append("overlap? %s o=(%d,%d,%d) e=(%d,%d,%d)" % (a.get_actor_label(), o.x, o.y, o.z, e.x, e.y, e.z))
unreal.SystemLibrary.execute_console_command(UES.get_editor_world(), "RebuildNavigation")
LES.save_current_level()
open(unreal.Paths.project_saved_dir() + "NV_m00_lounge.txt", "w", encoding="utf-8").write("\n".join(OUT))
