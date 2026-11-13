"""Hook a Fab score track (Cyber Punk Music v11, Background 6) to the simulation suite as the
Combat-state layer. The WAV is imported into the gitignored Fab folder (licence: local use only).
Explore bed MUS_CrownBed is ducked while it plays; the antechamber dropout is unchanged."""
import os, unreal
PROJ = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
SRC = os.path.join(PROJ, "Saved", "MusicReview", "6_Background_6.wav")
DEST = "/Game/NeonVeil/Fab/Music"
NAME = "MUS_M00_SimSuite_FabCyberPunk06"
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
out = []
def log(*a):
    out.append(" ".join(str(x) for x in a)); unreal.log("[nv_music_sim] " + out[-1])

t = unreal.AssetImportTask()
t.filename = SRC; t.destination_path = DEST; t.destination_name = NAME
t.automated = True; t.replace_existing = True; t.save = True
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])
w = unreal.load_asset(f"{DEST}/{NAME}")
log("imported", w, "dur", w.get_editor_property("duration") if w else None)
w.set_editor_property("looping", True)
unreal.EditorAssetLibrary.save_loaded_asset(w)

bed = None; sim = None
for a in EAS.get_all_level_actors():
    if a.get_actor_label() == "MUS_CrownBed": bed = a
    if isinstance(a, unreal.NVSimulationDirector): sim = a
log("bed", bed, "sim", sim)
sim.set_editor_property("sim_music", w)
sim.set_editor_property("sim_music_volume", 0.22)
sim.set_editor_property("music_to_duck", bed)
sim.set_editor_property("duck_level", 0.15)
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
log("sim music hooked:", sim.get_editor_property("sim_music"), sim.get_editor_property("music_to_duck"))
open(os.path.join(PROJ, "Saved", "NV_music_sim.txt"), "w").write("\n".join(out))
