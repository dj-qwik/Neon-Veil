"""List static meshes whose names suggest a power cell / battery / canister, with bounds."""
import unreal

ar = unreal.AssetRegistryHelpers.get_asset_registry()
flt = unreal.ARFilter(class_paths=[unreal.TopLevelAssetPath("/Script/Engine", "StaticMesh"), unreal.TopLevelAssetPath("/Script/Engine", "SkeletalMesh")], recursive_paths=True,
                      package_paths=["/Game", "/MetaHumanCharacter"])
keys = ["helmet", "helm", "mask", "visor", "goggle", "hood", "respirator", "gasmask", "head"]
out = []
for d in ar.get_assets(flt):
    n = str(d.asset_name).lower()
    p = str(d.package_name)
    if "/__External" in p:
        continue
    if any(k in n for k in keys):
        try:
            m = d.get_asset()
            b = m.get_bounding_box() if hasattr(m, "get_bounding_box") else None
            if b:
                s = b.max - b.min
                out.append("%s  %.0fx%.0fx%.0f" % (p, s.x, s.y, s.z))
            else:
                e = m.get_bounds().box_extent
                out.append("%s  SK %.0fx%.0fx%.0f" % (p, 2 * e.x, 2 * e.y, 2 * e.z))
        except Exception as ex:
            out.append("%s  ? %r" % (p, ex))
open(unreal.Paths.project_saved_dir() + "NV_nv_find_helmet.txt", "w").write("\n".join(sorted(out)))
