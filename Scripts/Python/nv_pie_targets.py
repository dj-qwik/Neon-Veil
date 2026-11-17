"""PIE: state of every sim training target. Saved/NV_pie_targets.txt"""
import unreal
w = unreal.EditorLevelLibrary.get_game_world()
out = []
for t in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.NVTrainingTarget):
    comps = []
    for c in t.get_components_by_class(unreal.PrimitiveComponent):
        m = c.get_material(0) if hasattr(c, "get_material") else None
        comps.append("%s vis=%s mat=%s" % (c.get_name(), c.is_visible(), m.get_name() if m else None))
    out.append("%s hidden=%s loc=%s | %s" % (t.get_actor_label(), t.is_hidden_ed() if False else t.get_editor_property("hidden"), t.get_actor_location(), "; ".join(comps)))
open(unreal.Paths.project_saved_dir() + "NV_pie_targets.txt", "w").write("\n".join(out))
