"""Veyra Central exterior: the hub facade read as a warm, washed-out sunset wall.
 - Moon: was a warm orange (255,175,150) -> cool moonlight, lower intensity (night city, neon does the work).
 - Street post-process: cap how far auto exposure brightens the dark street so the pale facade doesn't blow out.
Args: moon_intensity exp_max (defaults 0.25 1.0). Saves the level only with 'save' as third arg.
Report: Saved/NV_hub_light_fix.txt"""
import unreal, sys
args = sys.argv[2:]
moon_i = float(args[0]) if len(args) > 0 else 0.25
exp_max = float(args[1]) if len(args) > 1 else 1.0
save = len(args) > 2 and args[2] == "save"
OUT = []
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for a in eas.get_all_level_actors():
    lab = a.get_actor_label()
    if lab == "Moon":
        c = a.get_component_by_class(unreal.DirectionalLightComponent)
        c.set_editor_property("intensity", moon_i)
        c.set_editor_property("light_color", unreal.Color(r=170, g=190, b=255, a=255))
        OUT.append(f"Moon -> {moon_i} cool")
    if lab in ("Street_PostProcess", "Street_Night_PP"):
        s = a.get_editor_property("settings")
        s.set_editor_property("override_auto_exposure_max_brightness", True)
        s.set_editor_property("auto_exposure_max_brightness", exp_max)
        a.set_editor_property("settings", s)
        OUT.append(f"{lab} exp max -> {exp_max}")
if save:
    unreal.EditorLoadingAndSavingUtils.save_current_level()
    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    OUT.append("saved")
open(unreal.Paths.project_saved_dir() + "NV_hub_light_fix.txt", "w").write("\n".join(OUT))
