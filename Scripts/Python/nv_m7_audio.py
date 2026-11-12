"""NEON VEIL - M7 audio pass for M00 (Bible §4 sound brief).

 - Imports the original, procedurally generated ambience/score (RawAssets/Audio, see
   generate_m00_audio.py) as looping sound waves.
 - Places room-scale, non-spatialised ambient beds with box attenuation:
     HVAC in every space, city/rain wash by the skybridge and atrium glazing, the industrial pulse
     in the sim suite (softer in the atrium), and the score bed over A-D whose box ends before the
     antechamber, so the music drops out before the handshake (Bible §4).
 - Wires one-shot SFX from the free Fab audio packs into the existing data hooks: interactables,
   doors, abilities, volley emitter, training targets, baton, and weapons.
Re-runnable (folder Audio cleared first). Report: Saved/NV_m7_audio.txt
"""
import os
import unreal

REPORT = []
def log(*a):
    msg = " ".join(str(x) for x in a)
    REPORT.append(msg)
    unreal.log("[NV M7 audio] " + msg)

AT = unreal.AssetToolsHelpers.get_asset_tools()
EAL = unreal.EditorAssetLibrary
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
LES = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
V = unreal.Vector
FOLDER = "Audio"
AUD = "/Game/NeonVeil/Audio"

def ensure_dir(p):
    if not EAL.does_directory_exist(p):
        EAL.make_directory(p)

def import_wav(fname, dest):
    name = os.path.splitext(fname)[0]
    path = f"{dest}/{name}"
    if not EAL.does_asset_exist(path):
        ensure_dir(dest)
        t = unreal.AssetImportTask()
        t.set_editor_property("filename", os.path.abspath(os.path.join(unreal.Paths.project_dir(), "RawAssets", "Audio", fname)))
        t.set_editor_property("destination_path", dest)
        t.set_editor_property("replace_existing", True)
        t.set_editor_property("automated", True)
        t.set_editor_property("save", True)
        AT.import_asset_tasks([t])
    w = unreal.load_asset(path)
    w.set_editor_property("looping", True)
    EAL.save_loaded_asset(w, only_if_is_dirty=False)
    log("sound", path)
    return w

def bed(label, sound, x0, x1, y0, y1, z0, z1, volume, falloff=400.0):
    c = V((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)
    a = EAS.spawn_actor_from_class(unreal.AmbientSound, c, unreal.Rotator())
    ac = a.get_editor_property("audio_component")
    ac.set_editor_property("sound", sound)
    ac.set_editor_property("volume_multiplier", volume)
    ac.set_editor_property("override_attenuation", True)
    ao = ac.get_editor_property("attenuation_overrides")
    ao.set_editor_property("attenuate", True)
    ao.set_editor_property("spatialize", False)
    ao.set_editor_property("attenuation_shape", unreal.AttenuationShape.BOX)
    ao.set_editor_property("attenuation_shape_extents", V((x1 - x0) / 2, (y1 - y0) / 2, (z1 - z0) / 2))
    ao.set_editor_property("falloff_distance", falloff)
    ac.set_editor_property("attenuation_overrides", ao)
    a.set_actor_label(label)
    a.set_folder_path(FOLDER)
    return a

def cue(path):
    s = unreal.load_asset(path)
    if s is None:
        log("MISSING", path)
    return s

def setp(obj, prop, val, what=""):
    if obj is None or val is None:
        return
    try:
        obj.set_editor_property(prop, val)
    except Exception as e:
        log("skip", what, prop, str(e)[:80])

def main():
    for a in EAS.get_all_level_actors():
        if str(a.get_folder_path()) == FOLDER:
            EAS.destroy_actor(a)

    hvac = import_wav("SFX_AMB_Crown_HVAC.wav", f"{AUD}/Ambience")
    pulse = import_wav("SFX_AMB_Crown_IndustrialPulse.wav", f"{AUD}/Ambience")
    city = import_wav("SFX_AMB_Crown_CityRain.wav", f"{AUD}/Ambience")
    music = import_wav("MUS_M00_CrownBed.wav", f"{AUD}/Music")

    # ---------------- beds (room boxes from the M00 layout)
    rooms = {"A": (-1500, 3500, -320, 320, 0, 480), "B": (3500, 6300, -1100, 1100, 0, 1200),
             "C": (6300, 10300, -1500, 1500, 0, 900), "D": (10300, 14800, -400, 400, 0, 500),
             "E": (14800, 16400, -700, 700, 0, 600)}
    for k, (x0, x1, y0, y1, z0, z1) in rooms.items():
        bed(f"AMB_HVAC_{k}", hvac, x0, x1, y0, y1, z0, z1, 0.32 if k != "E" else 0.2, 300.0)
    bed("AMB_CityRain_A", city, -1500, 3500, -320, 320, 0, 480, 0.55, 300.0)
    bed("AMB_CityRain_B", city, 3500, 6300, 200, 1100, 0, 1200, 0.45, 900.0)
    bed("AMB_Pulse_C", pulse, 6300, 10300, -1500, 1500, 0, 900, 0.55, 300.0)
    bed("AMB_Pulse_B", pulse, 3500, 6300, -1100, 1100, 0, 1200, 0.2, 300.0)
    # score: A..D, fades over the last 9 m of the gallery, silent in the antechamber
    bed("MUS_CrownBed", music, -1500, 13900, -1600, 1600, -200, 1400, 0.4, 900.0)
    log("ambient beds placed")

    # ---------------- one-shots
    C = "/Game/Cues"
    S = "/Game/SciFiUISFX/Cues"
    use = cue(f"{C}/TerminalFeedback/Positive/PosArpLow/UIBeep_PositiveArpLowA_HA_TerminalUI_03_Cue")
    door = cue(f"{C}/Whooshes/UIMvmt_Whoosh_HA_TerminalUI_33_Cue")
    for a in EAS.get_all_level_actors():
        if isinstance(a, unreal.NVInteractableActor):
            setp(a, "use_sound", use, a.get_actor_label())
        elif isinstance(a, unreal.NVObjectiveDoor):
            setp(a, "open_sound", door, a.get_actor_label())
        elif isinstance(a, unreal.NVSimVolleyEmitter):
            setp(a, "shot_sound", cue(f"{S}/Impacts/Impact_1_Low_Cue"), "volley")
            setp(a, "warning_sound", cue(f"{C}/TerminalFeedback/Negative/NegHigh/UIBeep_NegativeHighB_HA_TerminalUI_03_Cue"), "volley")
    # abilities
    ad = "/Game/NeonVeil/Data/Abilities"
    endc = cue(f"{S}/FX_Sounds/Air_FX_Pitched_Down_Cue")
    for n, act in (("DA_Ability_OpticalDisruption", f"{S}/Glitches/Glitch_5_Cue"),
                   ("DA_Ability_KineticShield", f"{S}/Rings/Reverse_Ring_2_Low_Cue"),
                   ("DA_Ability_DroneUplink", f"{S}/FX_Sounds/Air_FX_Pitched_Up_Cue")):
        d = unreal.load_asset(f"{ad}/{n}")
        if d:
            setp(d, "activate_sound", cue(act), n)
            setp(d, "end_sound", endc, n)
            EAL.save_loaded_asset(d, only_if_is_dirty=False)
    # training targets (blueprint defaults + placed instances)
    tcls = EAL.load_blueprint_class("/Game/NeonVeil/Tests/BP_NVTrainingTarget_Test")
    cleared = cue(f"{C}/TerminalFeedback/Positive/PosHigh/UIBeep_PositiveHighA_HA_TerminalUI_04_Cue")
    shieldb = cue(f"{S}/Impacts/Impact_2_Reso_Cue")
    if tcls:
        cdo = unreal.get_default_object(tcls)
        setp(cdo, "cleared_sound", cleared, "target cdo")
        setp(cdo, "shield_break_sound", shieldb, "target cdo")
        EAL.save_loaded_asset(unreal.load_asset("/Game/NeonVeil/Tests/BP_NVTrainingTarget_Test"), only_if_is_dirty=False)
    for a in EAS.get_all_level_actors():
        if isinstance(a, unreal.NVTrainingTarget):
            setp(a, "cleared_sound", cleared, a.get_actor_label())
            setp(a, "shield_break_sound", shieldb, a.get_actor_label())
    # player: baton
    pbp = unreal.load_asset("/Game/NeonVeil/Core/BP_NVPlayerCharacter")
    pcdo = unreal.get_default_object(EAL.load_blueprint_class("/Game/NeonVeil/Core/BP_NVPlayerCharacter"))
    melee = pcdo.get_editor_property("melee")
    setp(melee, "swing_sound", cue(f"{C}/Whooshes/UIMvmt_Whoosh_HA_TerminalUI_04_Cue"), "melee")
    setp(melee, "hit_sound", cue(f"{S}/Impacts/Impact_1_Cue"), "melee")
    EAL.save_loaded_asset(pbp, only_if_is_dirty=False)
    # weapons
    fire = cue("/Game/Clinic/Demo/FirstPerson/Audio/FirstPersonTemplateWeaponFire02")
    dry = cue(f"{S}/Clicks/Click_Low_Cue")
    rel = cue(f"{C}/Mechanical/Buttons/VCR/MACHAppl_VCRButton_HA_TerminalUI_08_Cue")
    for n in ("DA_Weapon_VX9", "DA_Weapon_Kestrel", "DA_Weapon_Harrow"):
        w = unreal.load_asset(f"/Game/NeonVeil/Data/Weapons/{n}")
        if w:
            setp(w, "fire_sound", fire, n)
            setp(w, "dry_fire_sound", dry, n)
            setp(w, "reload_sound", rel, n)
            EAL.save_loaded_asset(w, only_if_is_dirty=False)
    log("one-shot SFX wired")
    LES.save_current_level()

try:
    main()
finally:
    with open(unreal.Paths.project_saved_dir() + "NV_m7_audio.txt", "w", encoding="utf-8") as fh:
        fh.write("\n".join(REPORT))
