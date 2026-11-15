import unreal, collections
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
O = []; zones = collections.Counter()
for a in EAS.get_all_level_actors():
    for c in a.get_components_by_class(unreal.LocalLightComponent):
        l = c.get_world_location()
        zone = "street" if l.z < -6000 else ("station" if l.z > -500 else "mid")
        zones[(zone, str(a.get_folder_path()), type(c).__name__, bool(c.get_editor_property("cast_shadows")))] += 1
        if len(O) < 60:
            O.append(f"{a.get_actor_label()} [{a.get_folder_path()}] {type(c).__name__} at {l.x:.0f},{l.y:.0f},{l.z:.0f} r {c.get_editor_property('attenuation_radius'):.0f} I {c.get_editor_property('intensity'):.1f} shadow {c.get_editor_property('cast_shadows')} vol {c.get_editor_property('volumetric_scattering_intensity')} mob {c.get_editor_property('mobility')} maxdd {c.get_editor_property('max_draw_distance')}")
O.insert(0, "\n".join(f"{k}: {v}" for k, v in zones.most_common()))
open(unreal.Paths.project_saved_dir() + "NV_light_list.txt", "w").write("\n".join(O))
