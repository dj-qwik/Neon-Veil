"""Request MetaHuman auto-rigging (Epic cloud service) for the Director, blocking. Report: Saved/NV_mh_rig.txt"""
import unreal
REPORT = []
def log(*a):
    REPORT.append(" ".join(str(x) for x in a)); unreal.log("[NV director rig] " + REPORT[-1])
try:
    S = unreal.get_editor_subsystem(unreal.MetaHumanCharacterEditorSubsystem)
    ch = unreal.load_asset("/Game/NeonVeil/Characters/Director/MHC_Director")
    log("open for edit:", S.try_add_object_to_edit(ch))
    p = unreal.MetaHumanCharacterAutoRiggingRequestParams()
    p.set_editor_property("rig_type", unreal.MetaHumanRigType.JOINTS_AND_BLEND_SHAPES)
    p.set_editor_property("blocking", True)
    p.set_editor_property("report_progress", True)
    S.request_auto_rigging(ch, p)
    log("auto-rig returned; can build now:", S.can_build_meta_human(ch, True))
    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
finally:
    with open(unreal.Paths.project_saved_dir() + "NV_mh_rig.txt", "w", encoding="utf-8") as fh:
        fh.write("\n".join(REPORT))
