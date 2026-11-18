"""List static meshes in the art kits (asset-registry tags only, nothing loaded). Report: Saved/NV_kit_inventory.txt"""
import unreal
AR = unreal.AssetRegistryHelpers.get_asset_registry()
OUT = []
for root in ("/Game/ModularScifiInterior", "/Game/Clinic", "/Game/SoulCity", "/Game/SciFI_Lite_Assets", "/Game/Sci_Fi_Light",
             "/Game/SciFiTramStation", "/Game/LevelPrototyping"):
    assets = AR.get_assets_by_path(root, recursive=True)
    n = 0
    for a in assets:
        if str(a.asset_class_path.asset_name) != "StaticMesh":
            continue
        n += 1
        size = a.get_tag_value("ApproxSize") or ""
        tris = a.get_tag_value("Triangles") or ""
        OUT.append("%s\t%s\t%s" % (a.package_name, size, tris))
    OUT.append("## %s: %d meshes" % (root, n))
open(unreal.Paths.project_saved_dir() + "NV_kit_inventory.txt", "w", encoding="utf-8").write("\n".join(OUT))
