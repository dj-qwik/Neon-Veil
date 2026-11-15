import unreal, collections
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
O = []; C = collections.Counter()
for a in EAS.get_all_level_actors():
    for c in a.get_components_by_class(unreal.ParticleSystemComponent):
        t = c.get_editor_property("template")
        l = c.get_world_location()
        C[(t.get_name() if t else None, a.get_class().get_name())] += 1
        if len(O) < 15: O.append(f"{a.get_actor_label()} {a.get_class().get_name()} {t.get_path_name() if t else None} at {l.x:.0f},{l.y:.0f},{l.z:.0f}")
    for c in a.get_components_by_class(unreal.NiagaraComponent):
        C[("NIAGARA " + (c.get_asset().get_name() if c.get_asset() else "None"), a.get_class().get_name())] += 1
O.insert(0, "\n".join(f"{k}: {v}" for k, v in C.most_common()))
open(unreal.Paths.project_saved_dir() + "NV_fx_list.txt", "w").write("\n".join(O))
