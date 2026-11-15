import unreal, collections
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
C = collections.Counter(); ex = {}
for a in EAS.get_all_level_actors():
    lab = a.get_actor_label()
    for c in a.get_components_by_class(unreal.StaticMeshComponent):
        if c.get_editor_property("cast_shadow"):
            k = (lab.split("_")[0], a.get_class().get_name(), type(c).__name__)
            C[k] += 1; ex.setdefault(k, lab)
open(unreal.Paths.project_saved_dir() + "NV_shadow_probe.txt", "w").write("\n".join(f"{k}: {v}  e.g. {ex[k]}" for k, v in C.most_common(40)))
