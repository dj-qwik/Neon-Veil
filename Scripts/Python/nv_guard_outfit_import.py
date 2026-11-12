"""Import the P05 helmet + Tactical Soldier outfit (.mhpkg) and report wardrobe items, materials and slot API.
Report: Saved/NV_guard_outfit_import.txt"""
import os
import unreal
out = []
AR = unreal.AssetRegistryHelpers.get_asset_registry()
PKGS = {"C:/Users/djqwi/Downloads/oa_scifi_helmet_p05.mhpkg": "/Game/Outfits/SciFi_Helmet_P05",
        "C:/Users/djqwi/Downloads/oa_soldier_outfit_v1.mhpkg": "/Game/Outfits/TacticalSoldier"}
for src, dst in PKGS.items():
    out.append(f"{src} exists={os.path.exists(src)} size={os.path.getsize(src) if os.path.exists(src) else 0}")
    if not os.path.exists(src):
        continue
    if AR.get_assets(unreal.ARFilter(package_paths=[dst], recursive_paths=True)):
        out.append("  already imported")
        continue
    t = unreal.AssetImportTask()
    t.set_editor_property("filename", src)
    t.set_editor_property("destination_path", dst)
    t.set_editor_property("automated", True)
    t.set_editor_property("save", True)
    t.set_editor_property("replace_existing", True)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])
    out.append(f"  imported {len(t.get_editor_property('imported_object_paths'))} objects")
MEL = unreal.MaterialEditingLibrary
for dst in PKGS.values():
    for a in AR.get_assets(unreal.ARFilter(package_paths=[dst], recursive_paths=True)):
        c = str(a.asset_class_path.asset_name)
        if c in ("MetaHumanWardrobeItem", "ChaosOutfitAsset", "SkeletalMesh"):
            out.append(f"  {c}: {a.package_name}")
        if c == "MaterialInstanceConstant":
            mi = a.get_asset()
            v = [str(n) for n in MEL.get_vector_parameter_names(mi)]
            s = [str(n) for n in MEL.get_scalar_parameter_names(mi)]
            out.append(f"  MI {a.package_name}\n     V {v}\n     S {s[:25]}")
col = unreal.load_asset("/Game/NeonVeil/Characters/GuardMH/MHC_Guard").get_editor_property("internal_collection")
inst = col.get_editor_property("default_instance")
out.append("instance methods: " + ", ".join(m for m in dir(inst) if not m.startswith("_") and m not in dir(unreal.Object)))
out.append("collection methods: " + ", ".join(m for m in dir(col) if not m.startswith("_") and m not in dir(unreal.Object)))
try:
    pipe = col.get_editor_property("pipeline")
    out.append("pipeline: %s" % pipe)
    spec = pipe.get_specification() if hasattr(pipe, "get_specification") else None
    out.append("spec: %s" % spec)
    if spec:
        slots = spec.get_editor_property("slots")
        for k in slots.keys():
            sv = slots[k]
            out.append("  slot %s allows_multiple=%s" % (k, sv.get_editor_property("allows_multiple_selection") if hasattr(sv, "get_editor_property") else "?"))
except Exception as e:
    out.append("pipeline probe failed %r" % e)
with open(unreal.Paths.project_saved_dir() + "NV_guard_outfit_import.txt", "w", encoding="utf-8") as fh:
    fh.write("\n".join(out))
