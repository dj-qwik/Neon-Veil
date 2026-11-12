"""Wire the free PStudio 'Sci Fi gunpack' into the Bible weapons (VX-9 pistol, Kestrel SMG, Harrow rifle).
Meshes lie along +/-Y; viewmodel space is X forward, so yaw turns the muzzle to +X. Muzzle offsets are in mesh
space (no sockets in the pack). Textures capped to 2048 (first-person). Tuning values live here. Report: Saved/NV_guns_setup.txt"""
import unreal
EAL = unreal.EditorAssetLibrary
P = "/Game/Pack/"
V, R = unreal.Vector, unreal.Rotator
out = []
CFG = {
    "DA_Weapon_VX9": dict(
        mesh=P + "B_W_Sci_fi_pistol/skeletal_mesh/SK_A_Sci_fi_Pistol",
        fire=P + "B_W_Sci_fi_pistol/animation/A_Sci_fi_Pistol_Anim_B_W_sci_fi_pistol_punch",
        reload=P + "B_W_Sci_fi_pistol/animation/A_Sci_fi_Pistol_Anim_B_W_sci_fi_pistol_reload",
        yaw=-90.0, pitch=1.0, scale=0.6, hip=V(34, 8.5, -11.5), ads=V(24, 0, -6.2), muzzle=V(0, 19, 5)),
    "DA_Weapon_Kestrel": dict(
        mesh=P + "b_w_smg_mini/skeletal_mesh/SK_b_w_smg_mini",
        fire=P + "b_w_smg_mini/animation/A_animations_Anim_Armature_b_w_smg_-mini_fire",
        reload=P + "b_w_smg_mini/animation/A_animations_Anim_Armature_b_w_smg_-mini_reload",
        yaw=-92.0, pitch=0.0, scale=0.6, hip=V(40, 11, -13), ads=V(22, 0, -10.4), muzzle=V(0, 30, 6)),  # bullpup: muzzle +Y
    "DA_Weapon_Harrow": dict(
        mesh=P + "Sci_fi_sniper_rifle/mesh/SK_SCI_fi_sniper_rifle_ANIMATION",
        fire=P + "Sci_fi_sniper_rifle/animation/A_SCI_fi_sniper_rifle_ANIMATION_Anim_Armature_SCI_FI_SNIPER_RIFLE_TRIGGER",
        reload=P + "Sci_fi_sniper_rifle/animation/A_SCI_fi_sniper_rifle_ANIMATION_Anim_Armature_SCI_FI_SNIPER_RIFLE_RELOAD",
        yaw=-90.0, pitch=0.0, scale=0.62, hip=V(42, 12, -15), ads=V(16, 0, -11.5), muzzle=V(0, 60, 5)),  # not in M00; untested in play
}
for name, c in CFG.items():
    w = unreal.load_asset("/Game/NeonVeil/Data/Weapons/" + name)
    w.set_editor_property("weapon_mesh", unreal.load_asset(c["mesh"]))
    w.set_editor_property("weapon_static_mesh", None)
    w.set_editor_property("weapon_fire_anim", unreal.load_asset(c["fire"]))
    w.set_editor_property("weapon_reload_anim", unreal.load_asset(c["reload"]))
    w.set_editor_property("viewmodel_rotation", R(roll=0, pitch=c["pitch"], yaw=c["yaw"]))
    w.set_editor_property("viewmodel_scale", V(c["scale"], c["scale"], c["scale"]))
    w.set_editor_property("viewmodel_hip_offset", c["hip"])
    w.set_editor_property("viewmodel_ads_offset", c["ads"])
    w.set_editor_property("muzzle_offset", c["muzzle"])
    EAL.save_loaded_asset(w, only_if_is_dirty=False)
    out.append("%s -> %s" % (name, c["mesh"].split("/")[-1]))
    folder = c["mesh"].rsplit("/", 2)[0]
    n = 0
    for p in EAL.list_assets(folder, recursive=True):
        d = EAL.find_asset_data(p)
        if str(d.asset_class_path.asset_name) == "Texture2D":
            t = d.get_asset()
            if t.blueprint_get_size_x() > 2048 and t.get_editor_property("max_texture_size") != 2048:
                t.set_editor_property("max_texture_size", 2048)
                EAL.save_loaded_asset(t, only_if_is_dirty=False)
                n += 1
    out.append("   textures capped: %d" % n)
open(unreal.Paths.project_saved_dir() + "NV_guns_setup.txt", "w").write("\n".join(out))
