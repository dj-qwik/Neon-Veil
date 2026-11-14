"""PIE: set the player's ViewmodelNearClearance (arg cm) and report the current weapon. Report: Saved/NV_pie_clear.txt"""
import unreal, sys
v = float(sys.argv[2]) if len(sys.argv) > 2 else 7.0
OUT = []
worlds = unreal.EditorLevelLibrary.get_game_world() if hasattr(unreal.EditorLevelLibrary, "get_game_world") else None
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
for a in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.Character):
    try:
        a.set_editor_property("viewmodel_near_clearance", v)
        OUT.append(f"{a.get_name()} clearance -> {v}")
    except Exception as e:
        pass
open(unreal.Paths.project_saved_dir() + "NV_pie_clear.txt", "w").write("\n".join(OUT))
