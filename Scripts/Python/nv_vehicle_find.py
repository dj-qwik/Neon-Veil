import unreal
AR = unreal.AssetRegistryHelpers.get_asset_registry()
O = []
keys = ("car", "vehicle", "hover", "ship", "spinner", "drone", "truck", "taxi", "van", "flying", "aircraft", "jet", "craft", "sedan")
for ad in AR.get_assets(unreal.ARFilter(class_paths=[unreal.TopLevelAssetPath("/Script/Engine", "StaticMesh")], package_paths=["/Game"], recursive_paths=True)):
    n = str(ad.asset_name).lower()
    if any(k in n for k in keys) and "card" not in n and "scar" not in n:
        O.append(str(ad.package_name))
O.sort()
m = unreal.load_asset("/Game/NeonVeil/Materials/FX/MI_NV_TrafficCar_Cyan_Fwd")
O.append("CAR MI parent: " + (m.get_editor_property("parent").get_path_name() if m else "none"))
if m:
    for p in m.get_editor_property("vector_parameter_values"): O.append(f"  v {p.parameter_info.name} {p.parameter_value}")
    for p in m.get_editor_property("scalar_parameter_values"): O.append(f"  s {p.parameter_info.name} {p.parameter_value}")
open(unreal.Paths.project_saved_dir() + "NV_vehicle_find.txt", "w").write("\n".join(O))
