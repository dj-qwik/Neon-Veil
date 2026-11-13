"""Crown contrast pass (after the white Megascans surfaces flattened the image).
- Walls/ceilings (MI_DIR_CeramicPanel) darker so lights, neon and the city read against them; floors untouched.
- Post: more contrast, deeper toe, a touch more saturation for the neon accents.
- Interior ceiling lights stronger with tighter falloff, so they pool instead of washing the room.
Absolute values, re-runnable. Report: Saved/NV_m9_contrast.txt"""
import unreal
OUT = unreal.Paths.project_saved_dir() + "NV_m9_contrast.txt"
log = []
MEL = unreal.MaterialEditingLibrary
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

mi = unreal.load_asset("/Game/NeonVeil/Materials/Art/MI_DIR_CeramicPanel")
names = [str(n) for n in MEL.get_scalar_parameter_names(mi)]
log.append("CeramicPanel scalars: %s" % names)
if "Brightness" in names:
    MEL.set_material_instance_scalar_parameter_value(mi, "Brightness", 0.74)
    MEL.update_material_instance(mi)
    unreal.EditorAssetLibrary.save_loaded_asset(mi, only_if_is_dirty=False)
    log.append("walls Brightness -> 0.74")

ppv = [a for a in EAS.get_all_level_actors() if a.get_actor_label() == "GlobalPostProcess"][0]
s = ppv.get_editor_property("settings")
def setp(n, v):
    s.set_editor_property("override_" + n, True); s.set_editor_property(n, v)
setp("auto_exposure_bias", 0.3)
setp("color_contrast", unreal.Vector4(1.12, 1.12, 1.12, 1.0))
setp("color_saturation", unreal.Vector4(1.06, 1.06, 1.06, 1.0))
setp("film_toe", 0.6)
setp("film_black_clip", 0.0)
setp("vignette_intensity", 0.38)
ppv.set_editor_property("settings", s)
log.append("post: bias +0.3 contrast 1.12 sat 1.06 toe 0.60 vignette 0.38")

base = {"B_": 6800, "C_": 7400, "D_": 3000, "E_": 2300, "A_": 4000}
n = 0
for a in EAS.get_all_level_actors():
    if isinstance(a, unreal.PointLight) and str(a.get_folder_path()) == "Lighting":
        lab = a.get_actor_label()
        lum = next((v for k, v in base.items() if lab.startswith(k)), None)
        if lum is None or "Sculpture" in lab:
            continue
        lc = a.point_light_component
        lc.set_intensity(lum)
        lc.set_attenuation_radius(1100.0)
        n += 1
log.append("ceiling lights retuned: %d" % n)
for a in EAS.get_all_level_actors():
    if isinstance(a, unreal.SkyLight):
        log.append("skylight %s intensity %.2f" % (a.get_actor_label(), a.light_component.intensity))
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
open(OUT, "w").write("\n".join(log))
