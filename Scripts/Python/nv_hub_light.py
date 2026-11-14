"""Probe what lights the Veyra Central hub exterior. Report: Saved/NV_hub_light.txt"""
import unreal
OUT = []
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
acts = eas.get_all_level_actors()
hub = [a for a in acts if a.get_actor_label().startswith("Hub_Facade")]
lo = None; hi = None
for a in hub:
    o, e = a.get_actor_bounds(False)
    mn = o - e; mx = o + e
    lo = mn if lo is None else unreal.Vector(min(lo.x, mn.x), min(lo.y, mn.y), min(lo.z, mn.z))
    hi = mx if hi is None else unreal.Vector(max(hi.x, mx.x), max(hi.y, mx.y), max(hi.z, mx.z))
    comps = a.get_components_by_class(unreal.StaticMeshComponent)
    mats = []
    for c in comps:
        for i in range(c.get_num_materials()):
            m = c.get_material(i)
            mats.append(m.get_path_name() if m else "None")
    OUT.append(f"FACADE {a.get_actor_label()} loc={a.get_actor_location()} ext={e} folder={a.get_folder_path()} mats={mats[:6]}")
OUT.append(f"hub bounds {lo} .. {hi}")
for a in acts:
    for c in a.get_components_by_class(unreal.LightComponent):
        p = c.get_world_location()
        near = lo is not None and (lo.x - 4000 < p.x < hi.x + 4000 and lo.y - 4000 < p.y < hi.y + 4000)
        if isinstance(c, (unreal.DirectionalLightComponent, unreal.SkyLightComponent)) or near:
            extra = ""
            try:
                extra = f" radius={c.get_editor_property('attenuation_radius')}"
            except Exception:
                pass
            try:
                extra += f" units={c.get_editor_property('intensity_units')}"
            except Exception:
                pass
            OUT.append(f"LIGHT {a.get_actor_label()} {c.get_class().get_name()} I={c.get_editor_property('intensity')} col={c.get_editor_property('light_color')} loc={p} vis={c.is_visible()} folder={a.get_folder_path()}{extra}")
for a in acts:
    for cls in (unreal.SkyLightComponent, unreal.ExponentialHeightFogComponent, unreal.PostProcessComponent):
        for c in a.get_components_by_class(cls):
            OUT.append(f"ENV {a.get_actor_label()} {cls.__name__}")
    if isinstance(a, unreal.PostProcessVolume):
        s = a.get_editor_property("settings")
        OUT.append(f"PPV {a.get_actor_label()} unbound={a.get_editor_property('unbound')} expmin={s.get_editor_property('auto_exposure_min_brightness')} expmax={s.get_editor_property('auto_exposure_max_brightness')} bias={s.get_editor_property('auto_exposure_bias')} method={s.get_editor_property('auto_exposure_method')} override_bias={s.get_editor_property('override_auto_exposure_bias')}")
    if isinstance(a, unreal.ExponentialHeightFog):
        c = a.get_component_by_class(unreal.ExponentialHeightFogComponent)
        OUT.append(f"FOG {a.get_actor_label()} dens={c.get_editor_property('fog_density')} inscat={c.get_editor_property('fog_inscattering_luminance')} dirinscat={c.get_editor_property('directional_inscattering_luminance')}")
open(unreal.Paths.project_saved_dir() + "NV_hub_light.txt", "w").write("\n".join(OUT))
