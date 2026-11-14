"""Import ONE prologue voice take: RawAssets/VO/M00P/<id>.wav -> /Game/NeonVeil/Audio/VO/M00P/VO_<id>.
(one file per call: importing p04 inside the batch hook froze the editor twice). arg: line id.
Report: Saved/NV_vo_import_one.txt"""
import os, sys, unreal
LID = sys.argv[-1]
proj = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
wav = os.path.join(proj, "RawAssets", "VO", "M00P", LID + ".wav")
t = unreal.AssetImportTask()
t.filename = wav; t.destination_path = "/Game/NeonVeil/Audio/VO/M00P"; t.destination_name = "VO_" + LID
t.automated = True; t.replace_existing = True; t.save = True
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])
s = unreal.load_asset("/Game/NeonVeil/Audio/VO/M00P/VO_" + LID)
open(unreal.Paths.project_saved_dir() + "NV_vo_import_one.txt", "w").write("%s %s %s" % (LID, bool(s), s.get_editor_property("duration") if s else ""))
