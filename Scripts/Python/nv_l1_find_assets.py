"""Find assets by name keywords (argv[2] = comma list) and class. Report: Saved/NV_l1_find.txt"""
import sys
import unreal
keys = [k.lower() for k in (sys.argv[2] if len(sys.argv) > 2 else "asphalt,road,wet,ground,puddle,street,sidewalk").split(",")]
AR = unreal.AssetRegistryHelpers.get_asset_registry()
out = []
for a in AR.get_assets(unreal.ARFilter(package_paths=["/Game"], recursive_paths=True)):
    n = str(a.asset_name).lower()
    c = str(a.asset_class_path.asset_name)
    if c in ("Material", "MaterialInstanceConstant", "StaticMesh", "SoundWave", "SoundCue", "NiagaraSystem", "Blueprint") and any(k in n for k in keys):
        out.append(f"{c}\t{a.package_name}")
open(unreal.Paths.project_saved_dir() + "NV_l1_find.txt", "w").write("\n".join(sorted(out)))
