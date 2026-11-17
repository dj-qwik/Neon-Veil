"""Glass Crown atrium: post-process volume that darkens the room (negative exposure bias, slight vignette) so the
holographic orrery reads. Args: [bias, default -1.3]. Report: Saved/NV_atrium_mood.txt"""
import sys
import unreal
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
args = [a for a in sys.argv[1:] if not a.endswith(".py")]
BIAS = float(args[0]) if args else -1.3
out = []
ppv = next((a for a in EAS.get_all_level_actors() if a.get_actor_label() == "B_AtriumMood"), None)
if not ppv:
    ppv = EAS.spawn_actor_from_class(unreal.PostProcessVolume, unreal.Vector(4900, 0, 600), unreal.Rotator())
    ppv.set_actor_label("B_AtriumMood")
    ppv.set_folder_path("B_Atrium")
ppv.set_actor_scale3d(unreal.Vector(2700 / 200.0, 2100 / 200.0, 1180 / 200.0))
ppv.set_editor_property("unbound", False)
ppv.set_editor_property("priority", 5.0)
ppv.set_editor_property("blend_radius", 250.0)
s = ppv.get_editor_property("settings")
s.set_editor_property("override_auto_exposure_bias", True)
s.set_editor_property("auto_exposure_bias", BIAS)
s.set_editor_property("override_vignette_intensity", True)
s.set_editor_property("vignette_intensity", 0.55)
ppv.set_editor_property("settings", s)
o, e = ppv.get_actor_bounds(False)
out.append("ppv bounds %s %s bias %s" % (o, e, BIAS))
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
out.append("saved")
open(unreal.Paths.project_saved_dir() + "NV_atrium_mood.txt", "w").write("\n".join(out))
