import unreal
AR = unreal.AssetRegistryHelpers.get_asset_registry()
O = []
for ad in AR.get_assets(unreal.ARFilter(package_paths=["/MetaHumanCrowdContent"], recursive_paths=True)):
    p = str(ad.package_name); c = str(ad.asset_class_path.asset_name)
    if any(k in p.lower() for k in ("hair", "groom", "brow", "beard", "lash")) or c in ("GroomAsset", "GroomBindingAsset", "Blueprint"):
        O.append(f"{c} {p}")
O.sort()
O.append("--- assembled HeavysetFemale_Head02")
for ad in AR.get_assets(unreal.ARFilter(package_paths=["/MetaHumanCrowdContent/Characters/Assembled/HeavysetFemale_Head02"], recursive_paths=True)):
    O.append(f"{ad.asset_class_path.asset_name} {ad.package_name}")
for cv in ("r.Streaming.PoolSize", "r.VT.PoolSizeScale", "r.Streaming.LimitPoolSizeToVRAM"):
    O.append(f"{cv} = {unreal.SystemLibrary.get_console_variable_int_value(cv)} / {unreal.SystemLibrary.get_console_variable_float_value(cv)}")
open(unreal.Paths.project_saved_dir() + "NV_crowd_list.txt", "w").write("\n".join(O))
