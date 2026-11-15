"""Night, not dusk: take the peach out of the street and lift views.
The street/lift post-process volumes had a 7200-7600 K white balance (warms the whole image), let auto exposure
brighten up to EV100 20 (a dark night street got exposed like dusk), heavy bloom; fog, sky light and moon fed warm
city light back into the haze. Here: cool white balance, a floor on auto exposure so the night stays dark, cooler
fog/sky/moon, less bloom. args: [ev_min] [bias] [white_temp]  Idempotent; saves. Report: Saved/NV_night_grade.txt"""
import sys, unreal
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
args = [float(a) for a in sys.argv[2:5]] if len(sys.argv) > 2 else []
EV_MIN = args[0] if len(args) > 0 else 1.6
BIAS = args[1] if len(args) > 1 else -0.9
WT = args[2] if len(args) > 2 else 5200.0
OUT = []
def pp(s, name, val):
    s.set_editor_property(name, val)
    s.set_editor_property("override_" + name, True)
for a in EAS.get_all_level_actors():
    lab = a.get_actor_label()
    if isinstance(a, unreal.PostProcessVolume) and lab in ("Street_PostProcess", "Street_Night_PP", "Lift_PostProcess"):
        s = a.get_editor_property("settings")
        pp(s, "white_temp", WT)
        pp(s, "white_tint", 0.0)
        pp(s, "auto_exposure_bias", BIAS)
        pp(s, "auto_exposure_min_brightness", EV_MIN)       # can't adapt brighter than this exposure: night stays night
        pp(s, "auto_exposure_max_brightness", EV_MIN + 6.0)
        pp(s, "bloom_intensity", 0.8)
        pp(s, "color_saturation", unreal.Vector4(0.95, 0.98, 1.08, 1.0))
        pp(s, "color_contrast", unreal.Vector4(1.06, 1.06, 1.06, 1.0))
        pp(s, "color_gain", unreal.Vector4(0.92, 0.97, 1.08, 1.0))
        pp(s, "color_gamma", unreal.Vector4(1.0, 1.0, 1.03, 1.0))
        a.set_editor_property("settings", s)
        OUT.append(f"PPV {lab}: WT {WT} bias {BIAS} EV {EV_MIN}..{EV_MIN + 6}")
    for c in a.get_components_by_class(unreal.ExponentialHeightFogComponent):
        c.set_editor_property("fog_inscattering_luminance", unreal.LinearColor(0.004, 0.007, 0.02, 1))
        c.set_editor_property("volumetric_fog_albedo", unreal.Color(r=170, g=195, b=255, a=255))
        c.set_editor_property("volumetric_fog_extinction_scale", 1.4)
        OUT.append(f"fog {lab}: cooler, thinner")
    for c in a.get_components_by_class(unreal.SkyLightComponent):
        c.set_editor_property("intensity", 0.14)
        c.set_editor_property("light_color", unreal.Color(r=150, g=175, b=255, a=255))
        c.recapture_sky()
        OUT.append(f"sky light {lab}: 0.14, blue")
    for c in a.get_components_by_class(unreal.DirectionalLightComponent):
        c.set_editor_property("intensity", 0.4)
        c.set_editor_property("light_color", unreal.Color(r=140, g=170, b=255, a=255))
        c.set_editor_property("volumetric_scattering_intensity", 0.2)
        OUT.append(f"moon {lab}: 0.4, blue")
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
open(unreal.Paths.project_saved_dir() + "NV_night_grade.txt", "w").write("\n".join(OUT))
