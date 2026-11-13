"""Export the Fab music packs' SoundWaves to Saved/MusicReview/*.wav for offline review (not shipped).
Report: Saved/NV_music_export.txt"""
import unreal, os
OUT = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_saved_dir()) + "MusicReview/"
os.makedirs(OUT, exist_ok=True)
log = []
reg = unreal.AssetRegistryHelpers.get_asset_registry()
for root in ("/Game/Cyber_Punk_Music_v11", "/Game/Free_Cyber_Metal_Music_Pack"):
    for ad in reg.get_assets_by_path(root, recursive=True):
        if str(ad.asset_class_path.asset_name) != "SoundWave":
            continue
        sw = ad.get_asset()
        t = unreal.AssetExportTask()
        t.object = sw
        t.filename = OUT + str(ad.asset_name) + ".wav"
        t.automated = True; t.prompt = False; t.replace_identical = True
        ok = unreal.Exporter.run_asset_export_task(t)
        log.append("%s %s dur %.1f" % (ad.asset_name, ok, sw.get_editor_property("duration")))
open(unreal.Paths.project_saved_dir() + "NV_music_export.txt", "w").write("\n".join(log))
