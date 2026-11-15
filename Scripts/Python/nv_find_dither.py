import unreal
O = []
ar = unreal.AssetRegistryHelpers.get_asset_registry()
f = unreal.ARFilter(package_paths=["/Engine"], recursive_paths=True, class_paths=[unreal.TopLevelAssetPath("/Script/Engine", "MaterialFunction")])
for a in ar.get_assets(f):
    n = str(a.asset_name)
    if "ither" in n or "Dither" in n:
        O.append(str(a.package_name))
O.append("classes: " + str([c for c in dir(unreal) if "Dither" in c]))
p = "/Game/NeonVeil/UI/Nav/M_NV_NavArrowMasked"
if unreal.EditorAssetLibrary.does_asset_exist(p):
    O.append("delete broken: %s" % unreal.EditorAssetLibrary.delete_asset(p))
open(unreal.Paths.project_saved_dir() + "NV_find_dither.txt", "w").write("\n".join(O))
