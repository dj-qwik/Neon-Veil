"""Save the tuned baton grip on DA_Weapon_Baton (run with PIE stopped)."""
import unreal
d = unreal.load_asset("/Game/NeonVeil/Data/Weapons/DA_Weapon_Baton")
d.set_editor_property("arms_weapon_offset", unreal.Transform(unreal.Vector(0.0, 2.0, -11.0), unreal.Rotator(roll=50.0, pitch=-5.0, yaw=0.0), unreal.Vector(1, 1, 1)))
for k in ("weapon_mesh", "weapon_fire_anim", "weapon_reload_anim", "arms_fire_anim", "arms_reload_anim"):
    if d.get_editor_property(k):
        d.set_editor_property(k, None)
ok = unreal.EditorAssetLibrary.save_loaded_asset(d, only_if_is_dirty=False)
open(unreal.Paths.project_saved_dir() + "NV_baton_grip_save.txt", "w").write("saved %s %s mesh=%s" % (ok, d.get_editor_property("arms_weapon_offset"), d.get_editor_property("weapon_mesh")))
