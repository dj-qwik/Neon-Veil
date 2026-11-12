"""Find MetaHuman presets / wardrobe / grooms anywhere (after Optional Content install). Report: Saved/NV_mh_probe3.txt"""
import unreal
AR = unreal.AssetRegistryHelpers.get_asset_registry()
out = []
for cls in ("MetaHumanCharacter", "MetaHumanWardrobeItem", "MetaHumanCharacterPalette", "GroomAsset", "GroomBindingAsset", "AnimSequence", "MetaHumanCollection"):
    f = unreal.ARFilter(class_paths=[unreal.TopLevelAssetPath("/Script/MetaHumanCharacter" if cls.startswith("MetaHumanChar") else
        ("/Script/MetaHumanCharacterPalette" if cls in ("MetaHumanWardrobeItem", "MetaHumanCharacterPalette", "MetaHumanCollection") else
         ("/Script/HairStrandsCore" if cls.startswith("Groom") else "/Script/Engine")), cls)], recursive_classes=True)
    assets = AR.get_assets(f)
    paths = sorted(str(a.package_name) for a in assets)
    if cls == "AnimSequence":
        paths = [p for p in paths if "MetaHuman" in p or "Idle" in p or "idle" in p][:60]
    out.append(f"== {cls}: {len(assets)}")
    out += ["   " + p for p in paths[:120]]
w = unreal.Paths.engine_plugins_dir()
out.append("optional content warning check: see log")
with open(unreal.Paths.project_saved_dir() + "NV_mh_probe3.txt", "w", encoding="utf-8") as fh:
    fh.write("\n".join(out))
