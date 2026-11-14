"""Street rain at half density (1100) in the prologue map. Report: Saved/NV_rain_half.txt"""
import unreal
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
LES = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
MAP = "/Game/NeonVeil/Maps/M00/L_M00_Prologue"
if not unreal.EditorLevelLibrary.get_editor_world().get_path_name().startswith(MAP):
    LES.load_level(MAP)
out = []
for a in EAS.get_all_level_actors():
    if a.get_class().get_name() == "NVRainField":
        a.set_editor_property("count", 1100)
        out.append("%s -> 1100" % a.get_actor_label())
LES.save_current_level()
open(unreal.Paths.project_saved_dir() + "NV_rain_half.txt", "w").write("\n".join(out))
