"""PIE: report the crowd detail actually applied to the citizens. Saved/NV_pie_lodcheck.txt"""
import os
import unreal
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
out = []
for c in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.NVGuardCharacter)[:4]:
    for m in c.get_components_by_class(unreal.SkinnedMeshComponent):
        a = m.get_skinned_asset() if hasattr(m, "get_skinned_asset") else None
        if a:
            out.append("%s %s %s forced=%s stream=%s predicted=%s" % (c.get_actor_label(), m.get_name(), a.get_name(),
                       m.get_editor_property("forced_lod_model"), m.get_editor_property("streaming_distance_multiplier"),
                       m.get_editor_property("predicted_lod_level") if False else ""))
open(os.path.join(unreal.Paths.project_saved_dir(), "NV_pie_lodcheck.txt"), "w").write("\n".join(out))
