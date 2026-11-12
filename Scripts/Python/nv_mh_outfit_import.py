"""Import the free MetaOutfits Casual Wear Male .mhpkg and probe the wardrobe API. Report: Saved/NV_mh_outfit_import.txt"""
import unreal
out = []
SRC = "C:/Users/djqwi/Downloads/oa_casual_m_outfit.mhpkg"
DST = "/Game/Outfits/CasualMale"
AR = unreal.AssetRegistryHelpers.get_asset_registry()
existing = AR.get_assets(unreal.ARFilter(package_paths=[DST], recursive_paths=True))
if not existing:
    t = unreal.AssetImportTask()
    t.set_editor_property("filename", SRC)
    t.set_editor_property("destination_path", DST)
    t.set_editor_property("automated", True)
    t.set_editor_property("save", True)
    t.set_editor_property("replace_existing", True)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])
    out.append(f"imported objects: {[str(p) for p in t.get_editor_property('imported_object_paths')]}")
assets = AR.get_assets(unreal.ARFilter(package_paths=["/Game/Outfits"], recursive_paths=True))
out.append(f"assets under /Game/Outfits: {len(assets)}")
for a in assets:
    c = str(a.asset_class_path.asset_name)
    if c in ("MetaHumanWardrobeItem", "ChaosOutfitAsset", "SkeletalMesh", "MaterialInstanceConstant"):
        out.append(f"  {c}: {a.package_name}")
inst = unreal.load_asset("/Game/NeonVeil/Characters/Director/MHC_Director").get_editor_property("internal_collection").get_editor_property("default_instance")
out.append("instance methods: " + ", ".join(m for m in dir(inst) if not m.startswith("_") and m not in dir(unreal.Object)))
col = unreal.load_asset("/Game/NeonVeil/Characters/Director/MHC_Director").get_editor_property("internal_collection")
out.append("try_add doc: " + str(col.try_add_item_from_wardrobe_item.__doc__))
with open(unreal.Paths.project_saved_dir() + "NV_mh_outfit_import.txt", "w", encoding="utf-8") as fh:
    fh.write("\n".join(out))
