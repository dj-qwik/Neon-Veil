"""Copy Dekogon City Subway Train Modular (free Fab, local only, gitignored) into NeonVeil and inventory it.
Report: Saved/NV_subway_import.txt"""
import os, shutil, unreal
SRC = os.path.expanduser("~/Documents/Unreal Projects/CitySubwayTrainModular/Content/SubwayTrain")
SRC = SRC.replace("\\", "/")
if not os.path.isdir(SRC):
    SRC = "C:/Users/djqwi/Documents/Unreal Projects/CitySubwayTrainModular/Content/SubwayTrain"
DST = unreal.Paths.project_content_dir() + "SubwayTrain"
out = ["src %s exists %s" % (SRC, os.path.isdir(SRC))]
if not os.path.isdir(DST):
    shutil.copytree(SRC, DST)
    out.append("copied")
n = sum(len(f) for _, _, f in os.walk(DST))
out.append("files %d" % n)
AR = unreal.AssetRegistryHelpers.get_asset_registry()
AR.scan_paths_synchronous(["/Game/SubwayTrain"], True)
assets = AR.get_assets_by_path("/Game/SubwayTrain", recursive=True)
by = {}
for a in assets:
    by.setdefault(str(a.asset_class_path.asset_name), []).append(str(a.package_name))
for k in sorted(by):
    out.append("== %s (%d)" % (k, len(by[k])))
    if k in ("Blueprint", "World", "StaticMesh", "SkeletalMesh", "Material"):
        for p in sorted(by[k]):
            out.append("   " + p)
open(unreal.Paths.project_saved_dir() + "NV_subway_import.txt", "w").write("\n".join(out))
