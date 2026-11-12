"""Layered weapon audio from free packs: SoundLab1 'Free Weapon Sound Effects' (realistic shots, tails, reload foley)
+ ShashiRaj 'Sci-Fi Shots Pack2' accent layer (picked offline: ~0.2 s, <7 ms attack, 3.6-4.4 kHz centroid, tonal).
Report: Saved/NV_weapon_audio.txt"""
import unreal
W = "/Game/FreeWeaponSFX/Wav/"
S = "/Game/Sci-Fi_Shots_Pack2_Game_Of_Weapons/Wave/SciFi_Shot_P2__%d_"
out = []

def snd(p):
    a = unreal.load_asset(p)
    if a is None:
        raise RuntimeError("missing " + p)
    return a

def seq(steps):
    arr = []
    for path, t, vol in steps:
        try:
            ts = unreal.NVTimedSound(sound=snd(path), time=t, volume=vol)
        except Exception:
            ts = unreal.NVTimedSound()
            ts.import_text('(Sound="%s",Time=%f,Volume=%f)' % (snd(path).get_path_name(), t, vol))
        arr.append(ts)
    return arr

CFG = {
    "DA_Weapon_VX9": dict(
        shots=[W + "Handgun/Gunshots/sfx_wpn_hgn_gunshot_0%d" % i for i in (1, 2, 3)], vol=0.9, pitch=(0.97, 1.03),
        tails=[W + "Handgun/Gunshots/sfx_wpn_hgn_tail_0%d" % i for i in (1, 2)], tail_vol=0.55, tail_max=3,
        layers=[S % n for n in (145, 97, 133, 53)], layer_vol=0.22,
        reload=[(W + "Handgun/Reload/sfx_wpn_hgn_reload_02_magOut", 0.05, 1.0),
                (W + "Handgun/Reload/sfx_wpn_hgn_reload_03_magDraw", 0.30, 1.0),
                (W + "Handgun/Reload/sfx_wpn_hgn_reload_04_magIn", 0.52, 1.0),
                (W + "Handgun/Reload/sfx_wpn_hgn_reload_01_slideLock", 0.78, 0.9)],
        equip=W + "Handgun/Foley/sfx_wpn_hgn_foley_equip_01", dry=W + "Handgun/Foley/sfx_wpn_hgn_foley_aim_01"),
    "DA_Weapon_Kestrel": dict(
        shots=[W + "AssaultRifle/Gunshots/sfx_wpn_ar_gunshot_0%d" % i for i in (1, 2, 3)], vol=0.8, pitch=(1.08, 1.15),
        tails=[W + "AssaultRifle/Gunshots/sfx_wpn_ar_tail_0%d" % i for i in (1, 2)], tail_vol=0.4, tail_max=2,
        layers=[S % n for n in (105, 153, 98, 129)], layer_vol=0.18,
        reload=[(W + "AssaultRifle/Reload/sfx_wpn_ar_reload_01_magOut", 0.06, 1.0),
                (W + "AssaultRifle/Reload/sfx_wpn_ar_reload_02_magDraw", 0.32, 1.0),
                (W + "AssaultRifle/Reload/sfx_wpn_ar_reload_03_magIn", 0.55, 1.0),
                (W + "AssaultRifle/Reload/sfx_wpn_ar_reload_04_charge", 0.78, 0.9)],
        equip=W + "AssaultRifle/Foley/sfx_wpn_ar_foley_equip_01", dry=W + "AssaultRifle/Foley/sfx_wpn_ar_foley_aim_01"),
    "DA_Weapon_Harrow": dict(
        shots=[W + "AssaultRifle/Gunshots/sfx_wpn_ar_gunshot_0%d" % i for i in (1, 2, 3)], vol=1.0, pitch=(0.82, 0.88),
        tails=[W + "Shotgun/Gunshots/sfx_wpn_sgn_tail_0%d" % i for i in (1, 2)], tail_vol=0.7, tail_max=2,
        layers=[S % n for n in (142, 46, 131)], layer_vol=0.25,
        reload=[(W + "AssaultRifle/Reload/sfx_wpn_ar_reload_01_magOut", 0.06, 1.0),
                (W + "AssaultRifle/Reload/sfx_wpn_ar_reload_03_magIn", 0.50, 1.0),
                (W + "Handgun/Reload/sfx_wpn_hgn_reload_05_charge", 0.76, 1.0)],
        equip=W + "AssaultRifle/Foley/sfx_wpn_ar_foley_equip_02", dry=W + "AssaultRifle/Foley/sfx_wpn_ar_foley_aim_02"),
}
for name, c in CFG.items():
    w = unreal.load_asset("/Game/NeonVeil/Data/Weapons/" + name)
    w.set_editor_property("fire_sound_variants", [snd(p) for p in c["shots"]])
    w.set_editor_property("fire_volume", c["vol"])
    w.set_editor_property("fire_pitch_range", unreal.Vector2D(*c["pitch"]))
    w.set_editor_property("fire_tail_variants", [snd(p) for p in c["tails"]])
    w.set_editor_property("fire_tail_volume", c["tail_vol"])
    w.set_editor_property("max_fire_tail_voices", c["tail_max"])
    w.set_editor_property("fire_layer_variants", [snd(p) for p in c["layers"]])
    w.set_editor_property("fire_layer_volume", c["layer_vol"])
    w.set_editor_property("reload_sequence", seq(c["reload"]))
    w.set_editor_property("equip_sound", snd(c["equip"]))
    w.set_editor_property("dry_fire_sound", snd(c["dry"]))
    unreal.EditorAssetLibrary.save_loaded_asset(w, only_if_is_dirty=False)
    out.append("%s: %d shots, %d tails, %d layers, %d reload steps" % (
        name, len(c["shots"]), len(c["tails"]), len(c["layers"]), len(c["reload"])))
open(unreal.Paths.project_saved_dir() + "NV_weapon_audio.txt", "w").write("\n".join(out))
