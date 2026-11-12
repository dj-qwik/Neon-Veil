"""List static meshes whose names suggest a power cell / battery / canister, with bounds."""
import unreal

ar = unreal.AssetRegistryHelpers.get_asset_registry()
flt = unreal.ARFilter(class_paths=[unreal.TopLevelAssetPath("/Script/Engine", "StaticMesh")], recursive_paths=True,
                      package_paths=["/Game"])
keys = ["batter", "cell", "canister", "tank", "capsule", "power", "fuse", "core", "generator", "cylinder", "pack", "box",
        "crate", "module", "unit", "pipe"]
out = []
for d in ar.get_assets(flt):
    n = str(d.asset_name).lower()
    p = str(d.package_name)
    if p.startswith("/Game/CitySample") or "/__External" in p:
        continue
    if any(k in n for k in keys):
        m = d.get_asset()
        b = m.get_bounding_box()
        s = b.max - b.min
        out.append("%s  %.0fx%.0fx%.0f" % (p, s.x, s.y, s.z))
open(unreal.Paths.project_saved_dir() + "NV_nv_find_cell.txt", "w").write("\n".join(sorted(out)))
