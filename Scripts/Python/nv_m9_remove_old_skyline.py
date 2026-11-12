"""Remove the M2 graybox skyline (folder 'Skyline': CityN boxes + CityLitN window cards). Superseded by the City Sample
skyline (Skyline_CS); the window cards rendered as flat tan panels beyond the skybridge glass.
Report: Saved/NV_m9_remove_old_skyline.txt"""
import unreal
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
gone = []
for a in list(EAS.get_all_level_actors()):
    if str(a.get_folder_path()) == "Skyline":
        gone.append(a.get_actor_label())
        EAS.destroy_actor(a)
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
with open(unreal.Paths.project_saved_dir() + "NV_m9_remove_old_skyline.txt", "w", encoding="utf-8") as fh:
    fh.write(f"removed {len(gone)}: " + ", ".join(gone))
