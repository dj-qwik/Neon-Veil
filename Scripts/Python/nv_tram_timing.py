"""C00 ride 18 s (+~1.2 s door delay + 1.4 s open = ~21-24 s from spawn to open doors). Report: Saved/NV_tram_timing.txt"""
import unreal
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    if a.get_actor_label() == "C00_TramArrival":
        a.set_editor_property("duration", 18.0)
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
open(unreal.Paths.project_saved_dir() + "NV_tram_timing.txt", "w").write("ok")
