"""Export candidate weapon sounds to WAV (Saved/AudioExport) for offline analysis: the short Sci-Fi Shots Pack2
waves plus the SoundLab1 gunshot/tail/reload waves. Report: Saved/NV_audio_export.txt"""
import os
import unreal
EAL = unreal.EditorAssetLibrary
dst = unreal.Paths.project_saved_dir() + "AudioExport/"
os.makedirs(dst, exist_ok=True)
out = []
paths = []
for p in EAL.list_assets("/Game/Sci-Fi_Shots_Pack2_Game_Of_Weapons/Wave", recursive=False):
    w = unreal.load_asset(p.split(".")[0])
    if isinstance(w, unreal.SoundWave) and w.get_editor_property("duration") <= 0.9:
        paths.append(w)
for p in EAL.list_assets("/Game/FreeWeaponSFX/Wav", recursive=True):
    w = unreal.load_asset(p.split(".")[0])
    if isinstance(w, unreal.SoundWave):
        paths.append(w)
for w in paths:
    t = unreal.AssetExportTask()
    t.set_editor_property("object", w)
    t.set_editor_property("filename", dst + w.get_name() + ".wav")
    t.set_editor_property("automated", True)
    t.set_editor_property("prompt", False)
    t.set_editor_property("replace_identical", True)
    ok = unreal.Exporter.run_asset_export_task(t)
    out.append("%s %.2fs %s" % (w.get_name(), w.get_editor_property("duration"), ok))
open(unreal.Paths.project_saved_dir() + "NV_audio_export.txt", "w").write("\n".join(out))
