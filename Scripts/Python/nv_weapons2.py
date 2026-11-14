"""Weapon roster v2 (all held by the KINEMATION arms):
  VX-9 pistol      original PStudio pistol, Onyx arms set (procedural reload dip + the pistol's own reload anim)
  Kestrel SMG      KINEMATION Gepard
  Harrow rifle     original PStudio scoped sniper, ARX arms set, scope overlay + zoom when aimed
  ARX-2 carbine    new: KINEMATION ARX Mk2, full auto
  TP-12 breacher   new: KINEMATION TP12 pump shotgun, 8 pellets
Viewmodel numbers are tuned in PIE (nv_pie_fps vm/aw) and recorded here. Report: Saved/NV_weapons2.txt"""
import unreal
EAL = unreal.EditorAssetLibrary
V, R = unreal.Vector, unreal.Rotator
OUT = []
def log(*a):
    OUT.append(" ".join(str(x) for x in a))
D = "/Game/NeonVeil/Data/Weapons/"
K = "/Game/KINEMATION/Sci-fi_FPS_Pack"
CA, WA = f"{K}/Animations/Character/UE5", f"{K}/Animations/Weapons"
P = "/Game/Pack/"

def find(p):
    return unreal.load_asset(p) if p and EAL.does_asset_exist(p) else None

def xf(loc=(0, 0, 0), rot=(0, 0, 0), scale=1.0):
    return unreal.Transform(location=V(*loc), rotation=R(pitch=rot[0], yaw=rot[1], roll=rot[2]), scale=V(scale, scale, scale))

def ensure(name, src):
    if not EAL.does_asset_exist(D + name):
        EAL.duplicate_asset(D + src, D + name)
        log("created", name, "from", src)
    return find(D + name)

CFG = {
    "DA_Weapon_VX9": dict(
        mesh=P + "B_W_Sci_fi_pistol/skeletal_mesh/SK_A_Sci_fi_Pistol",
        wfire=P + "B_W_Sci_fi_pistol/animation/A_Sci_fi_Pistol_Anim_B_W_sci_fi_pistol_punch",
        wreload=P + "B_W_Sci_fi_pistol/animation/A_Sci_fi_Pistol_Anim_B_W_sci_fi_pistol_reload",
        arms="Onyx_Revolver/A_FP_Onyx", reload=None, attach=xf((0, -4, -5), (0, 0, 0), 0.6),
        hip=V(8, 0, 14), ads=V(6, -5.8, 18.4), conv=R(0, 0, 0), muzzle=V(0, 19, 5)),
    "DA_Weapon_Kestrel": dict(
        mesh=f"{K}/Weapons/Gepard/SKM_Gepard", wfire=None, wreload=f"{WA}/Gepard/A_W_Gepard_Reload",
        arms="Gepard/A_FP_Gepard", reload="Gepard/A_FP_Gepard_Reload", attach=xf(),
        hip=V(10, 3, 6), ads=V(6, -6, 12), conv=R(0, 0, 0), muzzle=V(0, 28, 0)),
    "DA_Weapon_Harrow": dict(
        mesh=P + "Sci_fi_sniper_rifle/mesh/SK_SCI_fi_sniper_rifle_ANIMATION",
        wfire=P + "Sci_fi_sniper_rifle/animation/A_SCI_fi_sniper_rifle_ANIMATION_Anim_Armature_SCI_FI_SNIPER_RIFLE_TRIGGER",
        wreload=P + "Sci_fi_sniper_rifle/animation/A_SCI_fi_sniper_rifle_ANIMATION_Anim_Armature_SCI_FI_SNIPER_RIFLE_RELOAD",
        arms="ARX_Mk1/A_FP_ARX", reload="ARX_Mk1/A_FP_ARX_Reload", attach=xf((4, 6, -6), (0, 0, 0), 0.62),
        hip=V(18, -2, 11), ads=V(4, -12.5, 6), conv=R(0, 0, 0), muzzle=V(0, 60, 5), scope=True, ads_fov=18.0),
    "DA_Weapon_ARX": dict(src="DA_Weapon_Kestrel", name="ARX-2 CARBINE",
        mesh=f"{K}/Weapons/ARX_Mk2_Rifle/SKM_ARX_Mk2", wfire=f"{WA}/ARX_Mk1/A_W_ARX_Fire", wreload=f"{WA}/ARX_Mk1/A_W_ARX_Reload",
        arms="ARX_Mk1/A_FP_ARX", reload="ARX_Mk1/A_FP_ARX_Reload", attach=xf(),
        hip=V(14, 2, 9), ads=V(6, -12.2, 10.9), conv=R(0, 0, 0), muzzle=V(0, 49, 6),
        stats=dict(damage=24.0, rounds_per_minute=640.0, magazine_size=30, starting_reserve_ammo=120, reload_time=2.3,
                   hip_spread_deg=2.0, ads_spread_deg=0.25, ads_fov=60.0, fire_mode=unreal.NVFireMode.FULL_AUTO)),
    "DA_Weapon_TP12": dict(src="DA_Weapon_Harrow", name="TP-12 BREACHER",
        mesh=f"{K}/Weapons/TP12/SKM_TP12", wfire=None, wreload=None,
        arms="TP12/A_FP_TP12", reload=None, attach=xf(),
        hip=V(12, 2, 8), ads=V(6, -12.4, 13.75), conv=R(0, 0, 0), muzzle=V(0, 45, 4),
        stats=dict(damage=11.0, rounds_per_minute=70.0, magazine_size=6, starting_reserve_ammo=30, reload_time=2.8,
                   hip_spread_deg=2.5, ads_spread_deg=1.6, pellet_count=8, pellet_spread_deg=3.0, range=3500.0,
                   ads_fov=68.0, weak_point_bonus=1.25, fire_mode=unreal.NVFireMode.SEMI_AUTO, bloom_deg=0.0)),
}
for name, c in CFG.items():
    w = ensure(name, c["src"]) if "src" in c else find(D + name)
    if not w:
        log("MISSING", name); continue
    a = c["arms"]
    sets = {
        "weapon_mesh": find(c["mesh"]), "weapon_static_mesh": None,
        "weapon_fire_anim": find(c.get("wfire")), "weapon_reload_anim": find(c.get("wreload")),
        "arms_idle_anim": find(f"{CA}/{a}_Idle"), "arms_fire_anim": find(f"{CA}/{a}_Fire"),
        "arms_draw_anim": find(f"{CA}/{a}_Draw"),
        "arms_reload_anim": find(f"{CA}/{c['reload']}") if c.get("reload") else None,
        "arms_weapon_bone": unreal.Name("ik_hand_gun"), "arms_weapon_offset": c["attach"],
        "viewmodel_rotation": c["conv"], "viewmodel_scale": V(1, 1, 1),
        "viewmodel_hip_offset": c["hip"], "viewmodel_ads_offset": c["ads"], "muzzle_offset": c["muzzle"],
        "weapon_reload_anim_rate": 0.0, "scope_overlay": c.get("scope", False),
    }
    if "ads_fov" in c:
        sets["ads_fov"] = c["ads_fov"]
    if "name" in c:
        sets["display_name"] = c["name"]
    for k, v in c.get("stats", {}).items():
        if k == "bloom_deg":
            continue
        sets[k] = v
    for k, v in sets.items():
        try:
            w.set_editor_property(k, v)
        except Exception as e:
            log("  set fail", name, k, e)
    EAL.save_loaded_asset(w, only_if_is_dirty=False)
    log(name, "| arms", a, "| anims:", ", ".join(k for k, v in sets.items() if "anim" in k and v is None and k != "weapon_reload_anim_rate"), "missing")

# loadout: everything is available from the start (trim in BP_NVPlayerCharacter > Weapons > StartingWeapons)
bp_path = "/Game/NeonVeil/Core/BP_NVPlayerCharacter"
bp = unreal.load_asset(bp_path)
unreal.BlueprintEditorLibrary.compile_blueprint(bp)
cls = EAL.load_blueprint_class(bp_path)
cdo = unreal.get_default_object(cls)
wc = cdo.get_editor_property("weapons")
order = ["DA_Weapon_VX9", "DA_Weapon_Kestrel", "DA_Weapon_ARX", "DA_Weapon_TP12", "DA_Weapon_Harrow"]
wc.set_editor_property("starting_weapons", [find(D + n) for n in order])
cdo.set_editor_property("arms_mesh_asset", find(f"{K}/Gloves/Meshes/SKM_SciFi_Arms"))
EAL.save_loaded_asset(bp, only_if_is_dirty=False)
log("starting weapons:", [x.get_name() for x in wc.get_editor_property("starting_weapons")])
open(unreal.Paths.project_saved_dir() + "NV_weapons2.txt", "w").write("\n".join(OUT))
