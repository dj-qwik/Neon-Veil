"""List AnimBlueprints (and their target skeletons) under the MetaHuman plugins. Report: Saved/NV_find_abp.txt"""
import unreal
AR = unreal.AssetRegistryHelpers.get_asset_registry()
out = []
for root in ("/MetaHumanCrowdContent", "/MetaHumanCrowd", "/MetaHumanCharacter", "/MetaHuman", "/Game/MetaHumans", "/Game/Characters"):
    f = unreal.ARFilter(package_paths=[root], recursive_paths=True,
                        class_paths=[unreal.TopLevelAssetPath("/Script/Engine", "AnimBlueprint")])
    for ad in AR.get_assets(f):
        sk = ad.get_tag_value("TargetSkeleton")
        out.append(f"{ad.package_name} | {sk}")
sk = unreal.load_asset("/MetaHumanCharacter/Female/Medium/NormalWeight/Body/metahuman_base_skel")
if sk:
    try:
        out.append("compatible: " + str(sk.get_editor_property("compatible_skeletons")))
    except Exception as e:
        out.append("compat err " + str(e))
open(unreal.Paths.project_saved_dir() + "NV_find_abp.txt", "w").write("\n".join(out))
