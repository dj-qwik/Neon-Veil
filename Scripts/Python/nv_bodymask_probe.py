import unreal
AR = unreal.AssetRegistryHelpers.get_asset_registry()
O = []
for p in ["/Engine/EngineResources/Black", "/Engine/EngineResources/WhiteSquareTexture", "/Engine/EngineResources/DefaultTexture"]:
    t = unreal.load_asset(p)
    if t: O.append(f"{p} srgb {t.get_editor_property('srgb')} comp {t.get_editor_property('compression_settings')} vt {t.get_editor_property('virtual_texture_streaming')}")
for ad in AR.get_assets(unreal.ARFilter(package_paths=["/MetaHumanCrowdContent/Outfits"], recursive_paths=True, class_paths=[unreal.TopLevelAssetPath("/Script/Engine", "Texture2D")])):
    if "bodymask" in str(ad.asset_name).lower():
        t = unreal.load_asset(str(ad.package_name))
        O.append(f"{ad.package_name} srgb {t.get_editor_property('srgb')} comp {t.get_editor_property('compression_settings')} vt {t.get_editor_property('virtual_texture_streaming')}")
for p in ["/MetaHumanCrowdContent/Characters/Assembled/HeavysetFemale_Head02/Body/Baked/T_Body_BC_VT", "/MetaHumanCrowdContent/Characters/Assembled/HeavysetFemale_Head02/Body/Baked/T_Body_N_VT"]:
    t = unreal.load_asset(p)
    O.append(f"{p} srgb {t.get_editor_property('srgb')} comp {t.get_editor_property('compression_settings')} vt {t.get_editor_property('virtual_texture_streaming')}")
m = unreal.load_asset("/MetaHumanCrowdContent/Characters/Assembled/HeavysetFemale_Head02/Body/Materials/MI_Body_Baked_VT")
O.append("orig body MI parent " + m.get_editor_property("parent").get_path_name())
for tp in m.get_editor_property("texture_parameter_values"):
    O.append(f"  {tp.parameter_info.name} = {tp.parameter_value.get_path_name() if tp.parameter_value else None}")
open(unreal.Paths.project_saved_dir() + "NV_bodymask_probe.txt", "w").write("\n".join(O))
