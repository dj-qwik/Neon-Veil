"""Export the textures used by the tram holoscreen materials to Saved/NV_tramtex/*.png. Saved/NV_tram_tex.txt"""
import os
import unreal
MEL = unreal.MaterialEditingLibrary
OUTD = os.path.join(unreal.Paths.project_saved_dir(), "NV_tramtex")
os.makedirs(OUTD, exist_ok=True)
out = []
for mp in ("/Game/SciFiTramStation/Materials/M_Tram_Holoscreens", "/Game/SciFiTramStation/Materials/M_Tram_Holoscreens_Opaque"):
    m = unreal.load_asset(mp)
    for t in MEL.get_used_textures(m):
        out.append("%s uses %s %dx%d" % (m.get_name(), t.get_path_name(), t.blueprint_get_size_x(), t.blueprint_get_size_y()))
        task = unreal.AssetExportTask()
        task.object = t
        task.filename = os.path.join(OUTD, t.get_name() + ".png")
        task.automated = True
        task.replace_identical = True
        task.prompt = False
        task.exporter = unreal.TextureExporterPNG()
        ok = unreal.Exporter.run_asset_export_task(task)
        out.append("  export %s" % ok)
open(unreal.Paths.project_saved_dir() + "NV_tram_tex.txt", "w").write("\n".join(out))
