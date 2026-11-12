"""NEON VEIL - lighting/exposure baseline for M00 (start of the M6 lighting pass).

Night at 02:17 (Bible §4): a cool, controlled interior against a warm-and-neon city sunk in haze.
 - Global post process: clamped histogram exposure (no blow-out on the white Kit A panels),
   restrained bloom, slight vignette, cool shadows / neutral highlights.
 - Interior point lights brought down and given a cooler, more architectural colour.
 - Height fog thickened far away only (start distance keeps interiors clean) so the skyline
   bases dissolve into haze and the towers read in depth layers.
Re-runnable (absolute values). Report: Saved/NV_m6_lighting.txt
"""
import unreal

REPORT = []
def log(*a):
    msg = " ".join(str(x) for x in a)
    REPORT.append(msg)
    unreal.log("[NV M6 light] " + msg)

EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
LES = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)

def find(label):
    for a in EAS.get_all_level_actors():
        if a.get_actor_label() == label:
            return a
    return None

def setp(settings, name, value):
    try:
        settings.set_editor_property("override_" + name, True)
        settings.set_editor_property(name, value)
    except Exception as e:
        log("pp skipped", name, str(e)[:80])

def main():
    ppv = find("GlobalPostProcess")
    s = ppv.get_editor_property("settings")
    setp(s, "auto_exposure_method", unreal.AutoExposureMethod.AEM_HISTOGRAM)
    setp(s, "auto_exposure_min_brightness", 2.2)     # EV100 (extended luminance range)
    setp(s, "auto_exposure_max_brightness", 4.2)
    setp(s, "auto_exposure_bias", -0.3)
    setp(s, "auto_exposure_speed_up", 2.0)
    setp(s, "auto_exposure_speed_down", 1.2)
    setp(s, "bloom_intensity", 0.55)
    setp(s, "bloom_threshold", 1.2)
    setp(s, "vignette_intensity", 0.32)
    setp(s, "color_saturation_shadows", unreal.Vector4(0.95, 0.97, 1.05, 1.0))
    setp(s, "color_gain_shadows", unreal.Vector4(0.94, 0.98, 1.06, 1.0))
    setp(s, "color_contrast", unreal.Vector4(1.06, 1.06, 1.06, 1.0))
    setp(s, "film_toe", 0.6)
    setp(s, "lumen_scene_lighting_quality", 1.0)
    setp(s, "lumen_reflection_quality", 1.0)
    ppv.set_editor_property("settings", s)
    log("post process tuned")

    n = 0
    for a in EAS.get_all_level_actors():
        if isinstance(a, unreal.PointLight) and str(a.get_folder_path()) == "Lighting":
            lc = a.point_light_component
            lab = a.get_actor_label()
            base = {"B_": 5200, "C_": 6000, "D_": 2400, "E_": 1800, "A_": 3200}
            lum = next((v for k, v in base.items() if lab.startswith(k)), None)
            if lum is None or "Sculpture" in lab:
                continue
            lc.set_intensity(lum)
            lc.set_light_color(unreal.LinearColor(0.86, 0.93, 1.0, 1.0))
            lc.set_editor_property("source_radius", 30.0)
            lc.set_editor_property("soft_source_radius", 60.0)
            n += 1
    log("interior lights retuned:", n)

    fog = find("HeightFog")
    if fog:
        fc = fog.component
        for k, v in (("fog_density", 0.035), ("fog_height_falloff", 0.06), ("start_distance", 4000.0),
                     ("fog_inscattering_luminance", unreal.LinearColor(0.035, 0.05, 0.085, 1.0)),
                     ("fog_inscattering_color", unreal.LinearColor(0.035, 0.05, 0.085, 1.0)),
                     ("volumetric_fog_scattering_distribution", 0.4)):
            try:
                fc.set_editor_property(k, v)
            except Exception as e:
                log("fog prop skipped", k, str(e)[:80])
        fog.set_actor_location(unreal.Vector(0, 0, -6000), False, False)
        log("fog tuned")
    LES.save_current_level()

try:
    main()
finally:
    with open(unreal.Paths.project_saved_dir() + "NV_m6_lighting.txt", "w", encoding="utf-8") as fh:
        fh.write("\n".join(REPORT))
