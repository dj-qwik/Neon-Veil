"""Check Director rig state; save if rigged. Report: Saved/NV_mh_check.txt"""
import unreal
S = unreal.get_editor_subsystem(unreal.MetaHumanCharacterEditorSubsystem)
ch = unreal.load_asset("/Game/NeonVeil/Characters/Director/MHC_Director")
S.try_add_object_to_edit(ch)
can = S.can_build_meta_human(ch, True)
if can:
    unreal.EditorAssetLibrary.save_loaded_asset(ch, only_if_is_dirty=False)
with open(unreal.Paths.project_saved_dir() + "NV_mh_check.txt", "w", encoding="utf-8") as fh:
    fh.write(f"can build: {can}")
