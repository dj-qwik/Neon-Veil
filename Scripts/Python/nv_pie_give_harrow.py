"""PIE test helper: give the player the Harrow (not in the M00 loadout) to check its ADS alignment."""
import unreal
w = unreal.EditorLevelLibrary.get_game_world()
h = unreal.load_asset("/Game/NeonVeil/Data/Weapons/DA_Weapon_Harrow")
for p in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.NVPlayerCharacter):
    p.get_component_by_class(unreal.NVWeaponComponent).give_weapon(h, True)
    unreal.log("[NV] gave Harrow to %s" % p.get_name())
