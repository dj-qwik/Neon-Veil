"""Wire the KINEMATION Sci-fi FPS pack and the Sci-Fi Armor Pack 05 into the game.
- Player: SKM_SciFi_Arms as the first-person arms.
- Weapons: VX-9 pistol -> Onyx revolver, Kestrel SMG -> Gepard, Harrow rifle -> ARX Mk2, each with its arms
  idle/fire/reload/draw anims and the weapon's own fire/reload anims.
- Guards (in L_M00_GlassCrown): Manny base (hidden, animating) wearing SKM_SciFi_Clothing_P05 + helmet v1.
- VRAM: Etherion textures capped to 1024, armour/KINEMATION to 1024 (6 GB card).
Report: Saved/NV_fps_arms_setup.txt"""
import unreal
EAL = unreal.EditorAssetLibrary
LES = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
V, R = unreal.Vector, unreal.Rotator
OUT = []
def log(*a):
    OUT.append(" ".join(str(x) for x in a))
K = "/Game/KINEMATION/Sci-fi_FPS_Pack"

def find(path):
    return unreal.load_asset(path) if EAL.does_asset_exist(path) else None

# ---- VRAM: texture caps
for root, cap in (("/Game/ModularScifiInterior", 1024), ("/Game/SciFi_Armor_Pack_05", 1024), (K, 1024)):
    n = 0
    for p in EAL.list_assets(root, recursive=True):
        d = EAL.find_asset_data(p)
        if str(d.asset_class_path.asset_name) != "Texture2D":
            continue
        t = d.get_asset()
        if max(t.blueprint_get_size_x(), t.blueprint_get_size_y()) > cap and t.get_editor_property("max_texture_size") != cap:
            t.set_editor_property("max_texture_size", cap)
            EAL.save_loaded_asset(t, only_if_is_dirty=False)
            n += 1
    log("textures capped", root, cap, n)

# ---- player arms (the C++ falls back to SKM_SciFi_Arms if this default does not stick)
cls = unreal.load_object(None, "/Game/NeonVeil/Core/BP_NVPlayerCharacter.BP_NVPlayerCharacter_C")
cdo = unreal.get_default_object(cls)
arms = find(f"{K}/Gloves/Meshes/SKM_SciFi_Arms")
cdo.set_editor_property("arms_mesh_asset", arms)
EAL.save_asset("/Game/NeonVeil/Core/BP_NVPlayerCharacter", only_if_is_dirty=False)
log("player arms:", arms)

# ---- weapons
CA = f"{K}/Animations/Character/UE5"
WA = f"{K}/Animations/Weapons"
CFG = {
    "DA_Weapon_VX9": dict(W="Onyx", folder="Onyx_Revolver", mesh=f"{K}/Weapons/Onyx_Revolver/SKM_Onyx", bone="ik_hand_gun",
                          reload="A_FP_Onyx_Reload_Empty", wreload="A_W_Onyx_Reload_Empty",
                          hip=V(8, 0, 14), ads=V(6, -5.5, 16.5), muzzle=V(0, 19, 2)),
    "DA_Weapon_Kestrel": dict(W="Gepard", folder="Gepard", mesh=f"{K}/Weapons/Gepard/SKM_Gepard", bone="ik_hand_gun",
                              reload="A_FP_Gepard_Reload", wreload="A_W_Gepard_Reload",
                              hip=V(10, 3, 6), ads=V(6, -6, 12), muzzle=V(0, 28, 0)),
    "DA_Weapon_Harrow": dict(W="ARX", folder="ARX_Mk1", mesh=f"{K}/Weapons/ARX_Mk2_Rifle/SKM_ARX_Mk2", bone="ik_hand_gun",
                             reload="A_FP_ARX_Reload", wreload="A_W_ARX_Reload",
                             hip=V(14, 2, 9), ads=V(6, -12.5, 10.5), muzzle=V(0, 49, 6)),
}
for name, c in CFG.items():
    w = find("/Game/NeonVeil/Data/Weapons/" + name)
    if not w:
        log("missing", name); continue
    W, f = c["W"], c["folder"]
    sets = {
        "weapon_mesh": find(c["mesh"]), "weapon_static_mesh": None,
        "weapon_fire_anim": find(f"{WA}/{f}/A_W_{W}_Fire"),
        "weapon_reload_anim": find(f"{WA}/{f}/{c['wreload']}"),
        "arms_idle_anim": find(f"{CA}/{f}/A_FP_{W}_Idle"),
        "arms_fire_anim": find(f"{CA}/{f}/A_FP_{W}_Fire"),
        "arms_reload_anim": find(f"{CA}/{f}/{c['reload']}"),
        "arms_draw_anim": find(f"{CA}/{f}/A_FP_{W}_Draw"),
        "arms_weapon_bone": unreal.Name(c["bone"]),
        "arms_weapon_offset": unreal.Transform(),
        "viewmodel_rotation": R(0, 0, 0), "viewmodel_scale": V(1, 1, 1),
        "viewmodel_hip_offset": c["hip"], "viewmodel_ads_offset": c["ads"],
        "muzzle_offset": c["muzzle"], "weapon_reload_anim_rate": 0.0,
    }
    for k, v in sets.items():
        try:
            w.set_editor_property(k, v)
        except Exception as e:
            log("  set fail", name, k, e)
    EAL.save_loaded_asset(w, only_if_is_dirty=False)
    log(name, "->", W, "|", ", ".join(f"{k}={'ok' if v is not None else 'NONE'}" for k, v in sets.items() if "anim" in k))

# ---- guards in the Crown
MAP = "/Game/NeonVeil/Maps/M00/L_M00_GlassCrown"
if not unreal.EditorLevelLibrary.get_editor_world().get_path_name().startswith(MAP):
    LES.load_level(MAP)
manny = find("/Game/Characters/Mannequins/Meshes/SKM_Manny_Simple")
anim = unreal.load_object(None, "/Game/Characters/Mannequins/Anims/Unarmed/ABP_Unarmed.ABP_Unarmed_C")
suit = find("/Game/SciFi_Armor_Pack_05/Mesh/SKM_SciFi_Clothing_P05")
helm = find("/Game/SciFi_Armor_Pack_05/Mesh/Parts/SKM_SciFi_Helmet_v1_P05")
parts = [p for p in (suit, helm) if p]
n = 0
for a in EAS.get_all_level_actors():
    if not isinstance(a, unreal.NVGuardCharacter):
        continue
    a.set_editor_property("body_mesh_asset", manny)
    a.set_editor_property("body_anim_class", anim)
    a.set_editor_property("appearance_class", None)
    a.set_editor_property("helmet_mesh_asset", None)
    a.set_editor_property("outfit_parts", parts)
    a.set_editor_property("hide_body_under_outfit", True)
    a.set_actor_location(a.get_actor_location(), False, False)
    n += 1
log("guards suited:", n, "parts", [p.get_name() for p in parts])
LES.save_current_level()
open(unreal.Paths.project_saved_dir() + "NV_fps_arms_setup.txt", "w").write("\n".join(OUT))
