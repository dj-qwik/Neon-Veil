import sys, unreal
out = unreal.Paths.project_saved_dir() + "TexExport/"
for p in sys.argv[2:]:
    t = unreal.load_asset(p)
    task = unreal.AssetExportTask()
    task.object = t; task.filename = out + t.get_name() + ".tga"; task.automated = True; task.prompt = False; task.replace_identical = True
    task.exporter = unreal.TextureExporterTGA()
    unreal.Exporter.run_asset_export_task(task)
