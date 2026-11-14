"""List sky/fog/post/directional actors in the current level -> Saved/NV_l1_probe_env.txt"""
import unreal
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
OUT = []
KEEP = ("DirectionalLight", "SkyLight", "SkyAtmosphere", "ExponentialHeightFog", "PostProcessVolume", "VolumetricCloud", "AtmosphericFog", "SkySphere", "BP_Sky")
for a in EAS.get_all_level_actors():
    c = a.get_class().get_name()
    if any(k in c for k in KEEP):
        line = [c, a.get_actor_label(), str(a.get_actor_location()), str(a.get_folder_path())]
        try:
            if "DirectionalLight" in c:
                lc = a.light_component
                line += ["I=", str(lc.intensity), "col", str(lc.light_color), "rot", str(a.get_actor_rotation())]
            if "SkyLight" in c:
                sc = a.light_component
                line += ["I=", str(sc.intensity), "src", str(sc.source_type), "cube", str(sc.cubemap)]
            if "ExponentialHeightFog" in c:
                fc = a.component
                line += ["dens", str(fc.fog_density), "inscat", str(fc.fog_inscattering_luminance), "dirinscat", str(fc.directional_inscattering_luminance)]
            if "PostProcessVolume" in c:
                s = a.settings
                line += ["unbound", str(a.unbound), "expo_min", str(s.auto_exposure_min_brightness), str(s.override_auto_exposure_min_brightness), "max", str(s.auto_exposure_max_brightness), "bias", str(s.auto_exposure_bias), str(s.override_auto_exposure_bias), "method", str(s.auto_exposure_method), str(s.override_auto_exposure_method)]
        except Exception as e:
            line.append("ERR " + str(e))
        OUT.append(" | ".join(line))
open(unreal.Paths.project_saved_dir() + "NV_l1_probe_env.txt", "w").write("\n".join(OUT))
