"""Crown Line tram route display in English with our stops (VEYRA CENTRAL / NEON MARKET / SKYPORT GATE / GLASS CROWN).
Reimports the Sci-Fi Tram Station holoscreen emissive atlas from Art/Tram/T_NV_Tram_Holoscreens_E.png (the pack's own
atlas with the four station labels repainted), keeping the texture's settings. The pack is local Fab content, so rerun
this after re-acquiring it. Report: Saved/NV_tram_screens.txt"""
import os
import unreal
out = []
SRC = os.path.join(unreal.Paths.project_dir(), "Art", "Tram", "T_NV_Tram_Holoscreens_E.png")
DEST = "/Game/SciFiTramStation/Textures"
NAME = "T_Train_Holoscreens_E"
try:
    old = unreal.load_asset(DEST + "/" + NAME)
    keep = {p: old.get_editor_property(p) for p in ("srgb", "compression_settings", "lod_group", "mip_gen_settings")}
    out.append("before %s %s" % (old.blueprint_get_size_x(), keep))
    t = unreal.AssetImportTask()
    t.filename = SRC
    t.destination_path = DEST
    t.destination_name = NAME
    t.replace_existing = True
    t.automated = True
    t.save = False
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])
    tex = unreal.load_asset(DEST + "/" + NAME)
    for p, v in keep.items():
        tex.set_editor_property(p, v)
    unreal.EditorAssetLibrary.save_loaded_asset(tex, only_if_is_dirty=False)
    out.append("imported %s -> %s %dx%d" % (SRC, tex.get_path_name(), tex.blueprint_get_size_x(), tex.blueprint_get_size_y()))
except Exception:
    import traceback; out.append(traceback.format_exc())
open(unreal.Paths.project_saved_dir() + "NV_tram_screens.txt", "w").write("\n".join(out))
