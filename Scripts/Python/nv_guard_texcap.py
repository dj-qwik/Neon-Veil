"""Cap guard texture sizes (VRAM: packaged peak was 5.19 / 5.15 GB with three MetaHuman guards).
Guards are seen at mid distance in dark rooms: outfit + helmet 1024, face/head (under the full helmet) 512,
everything else in the guard MetaHuman build 1024. Report: Saved/NV_guard_texcap.txt"""
import unreal
EAL = unreal.EditorAssetLibrary
out = []
roots = {"/Game/Outfits/TacticalSoldier": 1024, "/Game/Outfits/SciFi_Helmet_P05": 1024,
         "/Game/NeonVeil/Characters/GuardMH": 1024}
n = 0
for root, cap in roots.items():
    for p in EAL.list_assets(root, recursive=True):
        a = EAL.find_asset_data(p)
        if str(a.asset_class_path.asset_name) not in ("Texture2D",):
            continue
        t = a.get_asset()
        name = t.get_name().lower()
        c = 512 if (root.endswith("GuardMH") and any(k in name for k in ("face", "head"))) else cap
        sx = t.blueprint_get_size_x()
        if sx > c and t.get_editor_property("max_texture_size") != c:
            t.set_editor_property("max_texture_size", c)
            EAL.save_loaded_asset(t, only_if_is_dirty=False)
            n += 1
            out.append("%s %d -> %d" % (t.get_path_name(), sx, c))
out.insert(0, "capped %d textures" % n)
open(unreal.Paths.project_saved_dir() + "NV_guard_texcap.txt", "w").write("\n".join(out))
