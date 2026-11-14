"""Import the Sci-Fi Security X-Ray scanner (Fab FBX export in the launcher's vault cache) into
/Game/NeonVeil/Art/XRay. Report: Saved/NV_l1_import_xray.txt"""
import glob, os, zipfile
import unreal
out = []
roots = glob.glob("C:/ProgramData/Epic/EpicGamesLauncher/VaultCache/FabLibrary/Sci-Fi_Security_X-Ray*")
out.append(f"roots {roots}")
files = []
for r in roots:
    for dp, dn, fn in os.walk(r):
        for f in fn:
            files.append(os.path.join(dp, f).replace("\\", "/"))
out += ["  " + f for f in files]
tmp = os.path.join(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_saved_dir()), "Imports", "XRay")
os.makedirs(tmp, exist_ok=True)
for f in files:
    if f.lower().endswith(".zip"):
        zipfile.ZipFile(f).extractall(tmp)
for dp, dn, fn in os.walk(tmp):
    for f in fn:
        files.append(os.path.join(dp, f).replace("\\", "/"))
fbx = [f for f in files if f.lower().endswith(".fbx")]
tex = [f for f in files if f.lower().endswith((".png", ".tga", ".jpg", ".jpeg"))]
out.append(f"fbx {fbx}")
AT = unreal.AssetToolsHelpers.get_asset_tools()
DST = "/Game/NeonVeil/Art/XRay"
tasks = []
for f in tex:
    t = unreal.AssetImportTask()
    t.filename = f; t.destination_path = DST + "/Textures"; t.automated = True; t.replace_existing = True; t.save = True
    tasks.append(t)
for f in fbx:
    t = unreal.AssetImportTask()
    t.filename = f; t.destination_path = DST; t.automated = True; t.replace_existing = True; t.save = True
    ui = unreal.FbxImportUI()
    ui.set_editor_property("import_mesh", True)
    ui.set_editor_property("import_as_skeletal", False)
    ui.set_editor_property("import_materials", True)
    ui.set_editor_property("import_textures", True)
    ui.static_mesh_import_data.set_editor_property("combine_meshes", True)
    ui.static_mesh_import_data.set_editor_property("generate_lightmap_u_vs", False)
    ui.static_mesh_import_data.set_editor_property("auto_generate_collision", True)
    t.options = ui
    tasks.append(t)
AT.import_asset_tasks(tasks)
for t in tasks:
    out.append(f"{os.path.basename(t.filename)} -> {list(t.get_editor_property('imported_object_paths'))}")
open(unreal.Paths.project_saved_dir() + "NV_l1_import_xray.txt", "w").write("\n".join(out))
