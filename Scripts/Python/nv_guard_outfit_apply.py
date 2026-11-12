"""Dress MHC_Guard: Tactical Soldier outfit (carbon) + Sci Fi Helmet P05 (Directorate white), no hair groom,
then assemble BP_Guard (Optimized / MEDIUM). Report: Saved/NV_guard_outfit_apply.txt"""
import unreal
out = []
def log(*a):
    out.append(" ".join(str(x) for x in a)); unreal.log("[NV guard outfit] " + out[-1])
EAL = unreal.EditorAssetLibrary
DIR = "/Game/NeonVeil/Characters/GuardMH"
try:
    S = unreal.get_editor_subsystem(unreal.MetaHumanCharacterEditorSubsystem)
    ch = unreal.load_asset(DIR + "/MHC_Guard")
    S.try_add_object_to_edit(ch)
    col = ch.get_editor_property("internal_collection")
    inst = col.get_editor_property("default_instance")
    log("slots:", [str(s) for s in col.get_slot_names()])
    soldier = unreal.load_asset("/Game/Outfits/TacticalSoldier/WI_Soldier_Outfit_v1")
    helmet = unreal.load_asset("/Game/Outfits/SciFi_Helmet_P05/WI_OA_SciFi_Helmet_P05")
    k1 = col.try_add_item_from_wardrobe_item("Outfits", soldier)
    k2 = col.try_add_item_from_wardrobe_item("Outfits", helmet)
    log("keys", k1, k2)
    inst.set_single_slot_selection("Outfits", k1)
    sel = unreal.MetaHumanPipelineSlotSelection()
    log("selection struct fields:", [f for f in dir(sel) if not f.startswith("_")])
    sel.set_editor_property("slot_name", "Outfits")
    sel.set_editor_property("selected_item", k2)
    log("add helmet selection:", inst.try_add_slot_selection(sel))
    for slot in [str(s) for s in col.get_slot_names()]:
        if slot.lower() in ("hair", "beard", "mustache", "peachfuzz"):
            try:
                inst.set_single_slot_selection(slot, None)
                log("cleared", slot)
            except Exception as e:
                log("could not clear", slot, repr(e))
    log("selection:", inst.get_slot_selection_data())
    EAL.save_loaded_asset(ch, only_if_is_dirty=False)
    log("can build:", S.can_build_meta_human(ch, True))
    p = unreal.MetaHumanCharacterEditorBuildParameters()
    p.set_editor_property("pipeline_type", unreal.MetaHumanDefaultPipelineType.OPTIMIZED)
    p.set_editor_property("pipeline_quality", unreal.MetaHumanQualityLevel.MEDIUM)
    p.set_editor_property("absolute_build_path", DIR)
    p.set_editor_property("name_override", "Guard")
    S.build_meta_human(ch, p)
    log("build requested")
    AR = unreal.AssetRegistryHelpers.get_asset_registry()
    for a in AR.get_assets(unreal.ARFilter(package_paths=[DIR], recursive_paths=True)):
        if str(a.asset_class_path.asset_name) in ("Blueprint", "SkeletalMesh"):
            log("  ", str(a.asset_class_path.asset_name), str(a.package_name))
    for a in AR.get_assets(unreal.ARFilter(package_paths=["/Game/Outfits/TacticalSoldier"], recursive_paths=True)):
        if "Material" in str(a.asset_class_path.asset_name):
            log("  soldier mat", str(a.asset_class_path.asset_name), str(a.package_name))
    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
finally:
    with open(unreal.Paths.project_saved_dir() + "NV_guard_outfit_apply.txt", "w", encoding="utf-8") as fh:
        fh.write("\n".join(out))
