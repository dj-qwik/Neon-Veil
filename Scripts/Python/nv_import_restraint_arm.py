"""Import the Black Honey robotic arm (Gerardo Justel, CC-BY, Fab) from Downloads as one combined static mesh:
/Game/BlackHoneyArm/SM_BlackHoneyArm (folder gitignored like all Fab content). Also probes Underground Sci-Fi mesh bounds
for the crawlway dressing. Report: Saved/NV_import_arm.txt"""
import os
import unreal

OUT = []
def log(*a): OUT.append(" ".join(str(x) for x in a))
SRC = os.path.join(os.path.expanduser("~"), "Downloads", "black_honey_robotic_arm.glb")
DST = "/Game/BlackHoneyArm"
EAL = unreal.EditorAssetLibrary
try:
    if not EAL.does_asset_exist(DST + "/SM_BlackHoneyArm"):
        log("source exists", os.path.exists(SRC), SRC)
        pipeline = unreal.InterchangeGenericAssetsPipeline()
        try:
            mp = pipeline.get_editor_property("mesh_pipeline")
            mp.set_editor_property("combine_static_meshes", True)
            pipeline.set_editor_property("import_only_animations", False)
        except Exception as e:
            log("pipeline props", e)
        try:
            pipeline.get_editor_property("common_meshes_properties").set_editor_property("force_all_mesh_as_type", unreal.InterchangeForceMeshType.IFMT_STATIC_MESH)
        except Exception as e:
            log("force static", e)
        src = unreal.InterchangeManager.create_source_data(SRC)
        params = unreal.ImportAssetParameters()
        params.is_automated = True
        params.override_pipelines.append(unreal.SoftObjectPath(pipeline.get_path_name()))
        mgr = unreal.InterchangeManager.get_interchange_manager_scripted()
        res = mgr.import_asset(DST, src, params)
        log("import result", res)
    assets = EAL.list_assets(DST, recursive=True, include_folder=False)
    log("assets", len(assets))
    meshes = []
    for p in assets:
        a = unreal.load_asset(p)
        if isinstance(a, unreal.StaticMesh):
            bb = a.get_bounding_box()
            meshes.append((p, bb))
            log("SM", p, "min", bb.min, "max", bb.max, "mats", a.get_num_sections(0) if hasattr(a, "get_num_sections") else "")
        elif isinstance(a, unreal.SkeletalMesh):
            log("SK", p)
    # combined mesh: rename the biggest to SM_BlackHoneyArm
    if meshes and not EAL.does_asset_exist(DST + "/SM_BlackHoneyArm"):
        big = max(meshes, key=lambda m: (m[1].max - m[1].min).length())
        ok = EAL.rename_asset(big[0].split(".")[0], DST + "/SM_BlackHoneyArm")
        log("renamed", big[0], ok)
    for p in assets:
        if "Material" in str(type(unreal.load_asset(p))):
            log("MAT", p)
    # Underground Sci-Fi bounds
    for n in ("SM_Panels3x3_01", "SM_Panels3x3_04", "SM_Panels3x3_07", "SM_Bunker_Floor02_1m", "SM_Bunker_Floor01", "SM_Vent01", "SM_Wires01",
              "SM_Bunker_Fan", "SM_Bunker_FanFrame", "SM_Lamp01", "SM_Lamp02", "SM_TubeQuarter01", "SM_TubeTransition01", "SM_SupportBeams01",
              "SM_GlassTube01", "SM_HoloTube01", "SM_Bunker_Wall01_Rails", "SM_FloorWall_Border", "SM_Decor_CircleHole", "SM_Storage01", "SM_Cube_1m"):
        m = unreal.load_asset("/Game/UndergroundSciFi/Meshes/" + n)
        if m:
            bb = m.get_bounding_box()
            log("USF", n, "min(%d,%d,%d) max(%d,%d,%d)" % (bb.min.x, bb.min.y, bb.min.z, bb.max.x, bb.max.y, bb.max.z),
                "|", ",".join(sm.get_name() for sm in [m.get_material(i) for i in range(m.get_num_sections(0))] if sm))
        else:
            log("USF missing", n)
    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(False, True)
except Exception as e:
    import traceback
    log("ERROR", traceback.format_exc())
open(unreal.Paths.project_saved_dir() + "NV_import_arm.txt", "w", encoding="utf-8").write("\n".join(OUT))
