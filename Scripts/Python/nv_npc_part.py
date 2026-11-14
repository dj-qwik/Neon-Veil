"""PIE: show only outfit part N (or 'all'/'none') on actor label prefix. argv[2] = 'Label N'."""
import sys, unreal
UES = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
w = UES.get_game_world()
lab, n = sys.argv[2].split()
for a in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.Character):
    if a.get_actor_label().startswith(lab):
        for c in a.get_components_by_class(unreal.SkeletalMeshComponent):
            nm = c.get_name()
            if nm.startswith("OutfitPart"):
                c.set_visibility(n == "all" or nm == "OutfitPart" + n)
        break
