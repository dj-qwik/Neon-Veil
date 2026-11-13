"""Perf: the square-plan towers that replaced the round ones cost ~10 fps on the skybridge and pushed VRAM to
5081/5152 MB. Remove the 9 farthest replacements (0.9-1.1 km out, mostly lost in the haze).
Report: Saved/NV_skyline_trim.txt"""
import unreal
FAR = ["CS_Tower_CHJ_B01_03", "CS_Tower_CHJ_A01_18", "CS_Tower_CHJ_A01_16", "CS_Tower_CHJ_B01_13", "CS_Tower_CHJ_B01_05",
       "CS_Tower_CHJ_A01_00", "CS_Tower_CHJ_A01_04", "CS_Tower_CHJ_A01_08", "CS_Tower_CHJ_B01_17"]
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
out = []
for a in EAS.get_all_level_actors():
    if a.get_actor_label() in FAR:
        out.append("removed %s" % a.get_actor_label())
        EAS.destroy_actor(a)
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
out.append("removed %d" % (len(out)))
open(unreal.Paths.project_saved_dir() + "NV_skyline_trim.txt", "w").write("\n".join(out))
