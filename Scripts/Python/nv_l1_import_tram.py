"""Copy the Sci-Fi Tram Station content (UE 5.4 sample project) into NeonVeil at the same mount point
(/Game/SciFiTramStation) so every internal reference stays valid, then rescan. Report: Saved/NV_l1_import_tram.txt"""
import os, shutil
import unreal
SRC = "C:/Users/djqwi/Documents/Unreal Projects/TramStationSrc/Content/SciFiTramStation"
DST = os.path.join(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_content_dir()), "SciFiTramStation")
out = []
if not os.path.isdir(DST):
    # skip the 5.4 lighting builds and the layered PSDs: we rebuild lighting in our own map
    shutil.copytree(SRC, DST, ignore=shutil.ignore_patterns("*_BuiltData.uasset", "*.psd"))
    out.append("copied")
else:
    out.append("already present")
n = sum(len(f) for _, _, f in os.walk(DST))
out.append(f"files: {n}")
AR = unreal.AssetRegistryHelpers.get_asset_registry()
AR.scan_paths_synchronous(["/Game/SciFiTramStation"], True)
assets = AR.get_assets(unreal.ARFilter(package_paths=["/Game/SciFiTramStation"], recursive_paths=True))
out.append(f"registry assets: {len(assets)}")
for a in assets:
    if str(a.asset_class_path.asset_name) in ("World", "Blueprint"):
        out.append(f"  {a.asset_class_path.asset_name}: {a.package_name}")
open(unreal.Paths.project_saved_dir() + "NV_l1_import_tram.txt", "w").write("\n".join(out))
