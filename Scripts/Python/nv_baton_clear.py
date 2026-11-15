"""DA_Weapon_Baton was duplicated from the VX9: clear the leftover revolver mesh and gun anims (soft refs ignore None)."""
import unreal
OUT = []
d = unreal.load_asset("/Game/NeonVeil/Data/Weapons/DA_Weapon_Baton")
for k in ("weapon_mesh", "weapon_fire_anim", "weapon_reload_anim", "arms_fire_anim", "arms_reload_anim"):
    before = d.get_editor_property(k)
    ok = False
    for v in (None, unreal.SoftObjectPath(), ""):
        try:
            d.set_editor_property(k, v)
        except Exception as e:
            OUT.append(f"{k} {v!r}: {e}")
            continue
        now = d.get_editor_property(k)
        if not now or str(now) in ("", "None"):
            ok = True
            break
    OUT.append(f"{k}: {before} -> {d.get_editor_property(k)} ok={ok}")
unreal.EditorAssetLibrary.save_loaded_asset(d, only_if_is_dirty=False)
open(unreal.Paths.project_saved_dir() + "NV_baton_clear.txt", "w").write("\n".join(OUT))
