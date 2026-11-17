"""Crown Line ride music down 20% (MusicVolume on the level's NVTramRide). Report: Saved/NV_ride_music_vol.txt"""
import unreal
out = []
for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
    if isinstance(a, unreal.NVTramRide):
        v = a.get_editor_property("music_volume")
        a.set_editor_property("music_volume", round(v * 0.8, 4))
        out.append("%s music_volume %.3f -> %.3f (%s)" % (a.get_actor_label(), v, a.get_editor_property("music_volume"), a.get_editor_property("music")))
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
out.append("saved")
open(unreal.Paths.project_saved_dir() + "NV_ride_music_vol.txt", "w").write("\n".join(out))
