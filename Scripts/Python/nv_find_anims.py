"""List animation sequences under the MetaHuman template / crowd folders and anything sit-like. Saved/NV_find_anims.txt"""
import unreal
AR = unreal.AssetRegistryHelpers.get_asset_registry()
out = []
for ad in AR.get_assets_by_class(unreal.TopLevelAssetPath("/Script/Engine", "AnimSequence"), True):
    p = str(ad.package_name)
    if p.startswith("/MetaHuman") or "sit" in p.lower():
        out.append(p)
open(unreal.Paths.project_saved_dir() + "NV_find_anims.txt", "w").write("\n".join(sorted(out)))
