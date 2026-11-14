"""Catalogue static meshes (path, bounding box min/max, triangle count of LOD0) under a few pack folders.
Report: Saved/NV_l1_mesh_catalog.json"""
import json
import unreal
ROOTS = ["/Game/SoulCity/Environment/Meshes", "/Game/SciFiTramStation/Meshes", "/Game/ModularScifiInterior/Meshes",
         "/Game/CitySampleBuildings", "/Game/SoulCity/LevelContent"]
AR = unreal.AssetRegistryHelpers.get_asset_registry()
out = {}
for root in ROOTS:
    f = unreal.ARFilter(package_paths=[root], recursive_paths=True, class_paths=[unreal.TopLevelAssetPath("/Script/Engine", "StaticMesh")])
    for a in AR.get_assets(f):
        p = str(a.package_name)
        sm = unreal.load_asset(p)
        if not sm:
            continue
        bb = sm.get_bounding_box()
        out[p] = [[bb.min.x, bb.min.y, bb.min.z], [bb.max.x, bb.max.y, bb.max.z]]
open(unreal.Paths.project_saved_dir() + "NV_l1_mesh_catalog.json", "w").write(json.dumps(out))
