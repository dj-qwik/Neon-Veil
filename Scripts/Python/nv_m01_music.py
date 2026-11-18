"""M01 escape music: Cyber Punk Music v11 "Background 10" (Kloudization, Fab) - the pack's fastest track (~129 BPM)
with the hardest kick. Imported as a loop into the gitignored Fab folder and set as the Black Protocol director's
CombatMusic; it starts once the Director has left (and after a checkpoint load inside M01).
Level matches the Crown Line ride (NVTramRide MusicVolume 0.6 on Background 2): Background 10 measures ~0.7 dB
quieter, so 0.65. Report: Saved/NV_m01_music.txt"""
import os
import unreal

PROJ = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
SRC = os.path.join(PROJ, "Saved", "MusicReview", "10_Background_10.wav")
DEST = "/Game/NeonVeil/Fab/Music"
NAME = "MUS_M01_Escape_FabCyberPunk10"
VOLUME = 0.65
MAP = "/Game/NeonVeil/Maps/M00/L_M00_GlassCrown"
out = []
def log(*a):
    out.append(" ".join(str(x) for x in a))

t = unreal.AssetImportTask()
t.filename = SRC; t.destination_path = DEST; t.destination_name = NAME
t.automated = True; t.replace_existing = True; t.save = True
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])
w = unreal.load_asset(f"{DEST}/{NAME}")
log("imported", w, "dur", w.get_editor_property("duration") if w else None)
w.set_editor_property("looping", True)
sc = unreal.load_asset("/Game/NeonVeil/Audio/Mix/SC_NV_Music")
if sc:
    w.set_editor_property("sound_class_object", sc)     # Music volume slider
unreal.EditorAssetLibrary.save_loaded_asset(w, only_if_is_dirty=False)

LES = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
UES = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
if not UES.get_editor_world().get_path_name().startswith(MAP):
    LES.load_level(MAP)
for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
    if isinstance(a, unreal.NVBlackProtocolDirector):
        a.set_editor_property("combat_music", w)
        a.set_editor_property("combat_music_volume", VOLUME)
        log("director", a.get_actor_label(), "music", w.get_name(), "volume", VOLUME)
    if isinstance(a, unreal.NVTramRide):
        log("tram reference", a.get_editor_property("music").get_name(), a.get_editor_property("music_volume"))
LES.save_current_level()
open(unreal.Paths.project_saved_dir() + "NV_m01_music.txt", "w").write("\n".join(out))
