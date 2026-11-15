import unreal
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
O = []
def props(c, names):
    out = []
    for n in names:
        try: out.append(f"{n}={c.get_editor_property(n)}")
        except Exception: pass
    return " | ".join(out)
for a in EAS.get_all_level_actors():
    lab = a.get_actor_label()
    for c in a.get_components_by_class(unreal.ExponentialHeightFogComponent):
        O.append(f"FOG {lab}: " + props(c, ["fog_density", "fog_height_falloff", "fog_inscattering_luminance", "fog_inscattering_color", "directional_inscattering_luminance", "directional_inscattering_color", "volumetric_fog", "volumetric_fog_albedo", "volumetric_fog_emissive", "volumetric_fog_scattering_distribution", "volumetric_fog_extinction_scale", "start_distance", "fog_max_opacity", "second_fog_data"]))
        O.append(f"   loc {a.get_actor_location()}")
    for c in a.get_components_by_class(unreal.DirectionalLightComponent):
        O.append(f"DIR {lab}: rot {a.get_actor_rotation()} " + props(c, ["intensity", "light_color", "temperature", "use_temperature", "cast_shadows", "atmosphere_sun_light", "volumetric_scattering_intensity"]))
    for c in a.get_components_by_class(unreal.SkyLightComponent):
        O.append(f"SKY {lab}: " + props(c, ["intensity", "light_color", "source_type", "real_time_capture", "lower_hemisphere_color", "cubemap", "sky_distance_threshold", "volumetric_scattering_intensity"]))
    for c in a.get_components_by_class(unreal.SkyAtmosphereComponent):
        O.append(f"ATMO {lab}")
    if isinstance(a, unreal.PostProcessVolume):
        s = a.get_editor_property("settings")
        fields = ["auto_exposure_method", "auto_exposure_bias", "auto_exposure_min_brightness", "auto_exposure_max_brightness", "white_temp", "white_tint", "color_saturation", "color_contrast", "color_gain", "color_gamma", "color_offset", "scene_color_tint", "bloom_intensity", "film_toe", "film_shoulder", "local_exposure_highlight_contrast_scale"]
        vals = []
        for f in fields:
            try:
                ov = s.get_editor_property("override_" + f) if hasattr(s, "get_editor_property") else None
                vals.append(f"{f}={s.get_editor_property(f)}{'*' if ov else ''}")
            except Exception: pass
        O.append(f"PPV {lab} unbound={a.get_editor_property('unbound')} prio={a.get_editor_property('priority')}: " + " | ".join(vals))
    n = a.get_class().get_name()
    if "Sky" in n and "Light" not in n:
        O.append(f"SKYACTOR {lab} {n}")
    for c in a.get_components_by_class(unreal.StaticMeshComponent):
        m = c.static_mesh
        if m and ("Sky" in m.get_name() or "Sphere" in m.get_name()) and c.get_editor_property("bounds_scale") >= 0 and max(a.get_actor_scale3d().x, 0) > 50:
            O.append(f"SKYMESH {lab} {m.get_name()} mat {c.get_material(0).get_path_name() if c.get_material(0) else None} scale {a.get_actor_scale3d()}")
open(unreal.Paths.project_saved_dir() + "NV_atmo_probe.txt", "w").write("\n".join(O))
