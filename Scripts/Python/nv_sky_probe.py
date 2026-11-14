"""Sky light / sky / atmosphere settings. Report: Saved/NV_sky_probe.txt"""
import unreal
OUT = []
for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
    for c in a.get_components_by_class(unreal.SkyLightComponent):
        props = {}
        for p in ("intensity", "source_type", "cubemap", "light_color", "lower_hemisphere_color", "lower_hemisphere_is_black", "real_time_capture", "indirect_lighting_intensity", "sky_distance_threshold", "volumetric_scattering_intensity"):
            try:
                v = c.get_editor_property(p)
                props[p] = v.get_path_name() if hasattr(v, "get_path_name") else v
            except Exception as e:
                props[p] = "?"
        OUT.append(f"SKYLIGHT {a.get_actor_label()} folder={a.get_folder_path()} {props}")
    for c in a.get_components_by_class(unreal.StaticMeshComponent):
        sm = c.static_mesh
        if sm and ("Sky" in sm.get_name() or "sky" in a.get_actor_label().lower()):
            mats = [c.get_material(i).get_path_name() for i in range(c.get_num_materials()) if c.get_material(i)]
            OUT.append(f"SKYMESH {a.get_actor_label()} {sm.get_name()} mats={mats} scale={a.get_actor_scale3d()}")
    if isinstance(a, unreal.PostProcessVolume):
        s = a.get_editor_property("settings")
        vals = {}
        for p in ("white_temp", "white_tint", "color_saturation", "color_gain", "color_gamma", "scene_color_tint", "bloom_intensity", "override_white_temp", "override_scene_color_tint", "override_color_gain"):
            try:
                vals[p] = s.get_editor_property(p)
            except Exception:
                pass
        OUT.append(f"PPV {a.get_actor_label()} prio={a.get_editor_property('priority')} unbound={a.get_editor_property('unbound')} {vals}")
open(unreal.Paths.project_saved_dir() + "NV_sky_probe.txt", "w").write("\n".join(str(x) for x in OUT))
