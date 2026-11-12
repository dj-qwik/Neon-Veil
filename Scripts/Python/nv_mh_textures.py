"""Download MetaHuman texture sources for the Director (Epic cloud). Report: Saved/NV_mh_textures.txt"""
import unreal
S = unreal.get_editor_subsystem(unreal.MetaHumanCharacterEditorSubsystem)
ch = unreal.load_asset("/Game/NeonVeil/Characters/Director/MHC_Director")
S.try_add_object_to_edit(ch)
p = unreal.MetaHumanCharacterTextureRequestParams()
p.set_editor_property("blocking", True)
p.set_editor_property("report_progress", True)
S.request_texture_sources(ch, p)
with open(unreal.Paths.project_saved_dir() + "NV_mh_textures.txt", "w", encoding="utf-8") as fh:
    fh.write(f"requested; can build: {S.can_build_meta_human(ch, True)}")
