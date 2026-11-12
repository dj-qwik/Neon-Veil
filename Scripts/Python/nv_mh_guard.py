"""Create the shared guard MetaHuman (one identity for all three M00 guards; faces sit under full helmets).
Duplicate preset -> cloud auto-rig -> cloud textures. Build happens later (nv_mh_guard_build) once the
Directorate outfit + P05 helmet are in. Report: Saved/NV_mh_guard.txt"""
import unreal

REPORT = []
def log(*a):
    REPORT.append(" ".join(str(x) for x in a)); unreal.log("[NV guard mh] " + REPORT[-1])

EAL = unreal.EditorAssetLibrary
SRC = "/MetaHumanCharacter/Optional/Presets/Mateo"
DIR = "/Game/NeonVeil/Characters/GuardMH"
DST = f"{DIR}/MHC_Guard"
try:
    S = unreal.get_editor_subsystem(unreal.MetaHumanCharacterEditorSubsystem)
    if not EAL.does_asset_exist(DST):
        if not EAL.does_directory_exist(DIR):
            EAL.make_directory(DIR)
        EAL.duplicate_asset(SRC, DST)
        log("duplicated", SRC)
    ch = unreal.load_asset(DST)
    log("open for edit:", S.try_add_object_to_edit(ch))
    log("can build before rig:", S.can_build_meta_human(ch, True))
    p = unreal.MetaHumanCharacterAutoRiggingRequestParams()
    p.set_editor_property("rig_type", unreal.MetaHumanRigType.JOINTS_AND_BLEND_SHAPES)
    p.set_editor_property("blocking", True)
    p.set_editor_property("report_progress", True)
    S.request_auto_rigging(ch, p)
    log("rig done")
    t = unreal.MetaHumanCharacterTextureRequestParams()
    t.set_editor_property("blocking", True)
    t.set_editor_property("report_progress", True)
    S.request_texture_sources(ch, t)
    log("textures done; can build:", S.can_build_meta_human(ch, True))
    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
except Exception as e:
    log("ERROR", repr(e))
    raise
finally:
    with open(unreal.Paths.project_saved_dir() + "NV_mh_guard.txt", "w", encoding="utf-8") as fh:
        fh.write("\n".join(REPORT))
