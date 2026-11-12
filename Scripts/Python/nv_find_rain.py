"""List Niagara systems / textures / materials whose name suggests rain, drops, splash, streak. Report: Saved/NV_find_rain.txt"""
import unreal
AR = unreal.AssetRegistryHelpers.get_asset_registry()
out = []
f = unreal.ARFilter(package_paths=["/Game"], recursive_paths=True)
for a in AR.get_assets(f):
    n = str(a.asset_name).lower()
    if any(k in n for k in ("rain", "drop", "splash", "streak", "drizzle", "weather", "puddle", "wet")):
        out.append(f"{str(a.asset_class_path.asset_name):28s} {a.package_name}")
out.sort()
with open(unreal.Paths.project_saved_dir() + "NV_find_rain.txt", "w", encoding="utf-8") as fh:
    fh.write("\n".join(out) or "none")
