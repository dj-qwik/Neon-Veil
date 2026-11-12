"""List MetaHuman presets and every wardrobe item (WI_*) available in the project/plugin content."""
import unreal

EAL = unreal.EditorAssetLibrary
out = ["PRESETS"]
for p in EAL.list_assets("/MetaHumanCharacter/Optional/Presets", recursive=False):
    out.append("  " + p.split(".")[0])
out.append("WARDROBE ITEMS")
AR = unreal.AssetRegistryHelpers.get_asset_registry()
for root in ["/MetaHumanCharacter", "/Game"]:
    for d in AR.get_assets(unreal.ARFilter(package_paths=[root], recursive_paths=True,
                                          class_paths=[unreal.TopLevelAssetPath("/Script/MetaHumanCharacterPalette", "MetaHumanWardrobeItem")])):
        out.append("  " + str(d.package_name))
open(unreal.Paths.project_saved_dir() + "NV_nv_mh_list.txt", "w").write("\n".join(out))
