"""Move the breaker box out of the wall: it sat behind SM_Wall7's face (x 1324), so the use-trace hit the wall."""
import unreal
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
LES = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
out = []
for a in EAS.get_all_level_actors():
    if isinstance(a, unreal.NVBreakerPanel):
        l = a.get_actor_location()
        a.set_actor_location(unreal.Vector(1323.0, l.y, l.z), False, False)
        out.append("%s %s -> %s" % (a.get_actor_label(), l, a.get_actor_location()))
LES.save_current_level()
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
open(unreal.Paths.project_saved_dir() + "NV_breaker_move.txt", "w").write("\n".join(out))
