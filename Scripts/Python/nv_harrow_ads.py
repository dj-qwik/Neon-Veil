"""Harrow ADS alignment: put the scope lens centre on the screen centre (checked in PIE)."""
import unreal, sys
x, z = (float(sys.argv[1]), float(sys.argv[2])) if len(sys.argv) > 2 else (22.0, -13.6)
w = unreal.load_asset("/Game/NeonVeil/Data/Weapons/DA_Weapon_Harrow")
w.set_editor_property("viewmodel_ads_offset", unreal.Vector(x, 0, z))
unreal.EditorAssetLibrary.save_loaded_asset(w, only_if_is_dirty=False)
unreal.log("[NV] Harrow ads -> %s" % w.get_editor_property("viewmodel_ads_offset"))
