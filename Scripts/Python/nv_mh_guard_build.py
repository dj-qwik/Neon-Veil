"""Assemble the shared guard MetaHuman (UE Optimized pipeline).
Step-wise and logged: duplicate -> open for edit -> can_build check -> build. Report: Saved/NV_mh_guard_build.txt"""
import unreal

REPORT = []
def log(*a):
    msg = " ".join(str(x) for x in a)
    REPORT.append(msg)
    unreal.log("[NV guard build] " + msg)

EAL = unreal.EditorAssetLibrary
SRC = None
DIR = "/Game/NeonVeil/Characters/GuardMH"
DST = f"{DIR}/MHC_Guard"
QUALITY = "MEDIUM"      # LOW / MEDIUM / HIGH / CINEMATIC (Optimized pipeline); 6 GB GPU -> medium
BUILD = True

def main():
    S = unreal.get_editor_subsystem(unreal.MetaHumanCharacterEditorSubsystem)
    if not EAL.does_asset_exist(DST):
        if not EAL.does_directory_exist(DIR):
            EAL.make_directory(DIR)
        EAL.duplicate_asset(SRC, DST)
        log("duplicated", SRC, "->", DST)
    ch = unreal.load_asset(DST)
    log("loaded", ch, "high-res textures:", ch.get_editor_property("has_high_resolution_textures"))
    ok = S.try_add_object_to_edit(ch)
    log("opened for edit:", ok)
    can = S.can_build_meta_human(ch, True)
    log("can build:", can)
    if can and BUILD:
        p = unreal.MetaHumanCharacterEditorBuildParameters()
        p.set_editor_property("pipeline_type", unreal.MetaHumanDefaultPipelineType.OPTIMIZED)
        p.set_editor_property("pipeline_quality", getattr(unreal.MetaHumanQualityLevel, QUALITY))
        p.set_editor_property("absolute_build_path", DIR)
        p.set_editor_property("name_override", "Guard")
        S.build_meta_human(ch, p)
        log("build requested")
        AR = unreal.AssetRegistryHelpers.get_asset_registry()
        assets = AR.get_assets(unreal.ARFilter(package_paths=[DIR], recursive_paths=True))
        log("assets now under", DIR, len(assets))
        for a in assets:
            if str(a.asset_class_path.asset_name) in ("Blueprint", "SkeletalMesh", "AnimBlueprint"):
                log("  ", str(a.asset_class_path.asset_name), str(a.package_name))
    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)

try:
    main()
finally:
    with open(unreal.Paths.project_saved_dir() + "NV_mh_guard_build.txt", "w", encoding="utf-8") as fh:
        fh.write("\n".join(REPORT))
