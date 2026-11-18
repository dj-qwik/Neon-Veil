"""Shrink the Black Honey arm's eight 4K textures (Interchange import) to 1K, streamed and compressed: they pushed the
editor ~900 MB over its video-memory budget. Report: Saved/NV_arm_textures.txt"""
import unreal
OUT = []
EAL = unreal.EditorAssetLibrary
for p in EAL.list_assets("/Game/BlackHoneyArm", recursive=True, include_folder=False):
    t = unreal.load_asset(p)
    if not isinstance(t, unreal.Texture2D):
        continue
    before = (t.get_editor_property("max_texture_size"), str(t.get_editor_property("compression_settings")),
              t.get_editor_property("never_stream"), str(t.get_editor_property("mip_gen_settings")), t.blueprint_get_size_x())
    t.set_editor_property("max_texture_size", 1024)
    t.set_editor_property("never_stream", False)
    if str(t.get_editor_property("mip_gen_settings")).endswith("NO_MIPMAPS"):
        t.set_editor_property("mip_gen_settings", unreal.TextureMipGenSettings.TMGS_FROM_TEXTURE_GROUP)
    if str(t.get_editor_property("compression_settings")).endswith("TC_VECTOR_DISPLACEMENTMAP") or str(t.get_editor_property("compression_settings")).endswith("TC_HDR"):
        t.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_DEFAULT)
    EAL.save_loaded_asset(t, only_if_is_dirty=False)
    OUT.append("%s before %s -> 1024" % (t.get_name(), before))
open(unreal.Paths.project_saved_dir() + "NV_arm_textures.txt", "w").write("\n".join(OUT))
