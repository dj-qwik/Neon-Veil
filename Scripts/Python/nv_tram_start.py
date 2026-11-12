"""Move PlayerStart_TramExit inside the parked (100 m out) tram cabin. Report: Saved/NV_tram_start.txt"""
import unreal
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    if a.get_actor_label() == "PlayerStart_TramExit":
        a.set_actor_location(unreal.Vector(-193, 325 + 10000, 100), False, False)
        a.set_actor_rotation(unreal.Rotator(yaw=0), False)
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
open(unreal.Paths.project_saved_dir() + "NV_tram_start.txt", "w").write("ok")
