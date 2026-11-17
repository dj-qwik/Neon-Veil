"""NEON VEIL - fill the Crown Line ride (L_M00_GlassCrown): timed comms / inner monologue and a police pursuit beside
the tram (NVTramRideDirector, build ga39+). Imports the synthesised siren / hover-engine loops from
Art/Audio/Chase, makes the tracer / light-bar / patrol-paint materials and a wide attenuation, then places or
updates R_RideDirector. Idempotent. Report: Saved/NV_ride_director.txt"""
import os
import unreal

OUT = []
def log(*a):
    OUT.append(" ".join(str(x) for x in a))

EAL = unreal.EditorAssetLibrary
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
MEL = unreal.MaterialEditingLibrary
AT = unreal.AssetToolsHelpers.get_asset_tools()
AUD = "/Game/NeonVeil/Audio/Chase"
MAT = "/Game/NeonVeil/Materials/Chase"
SRC = os.path.join(unreal.Paths.project_dir(), "Art", "Audio", "Chase")

def T(s):
    return unreal.Text(s)

def line(t, speaker, text, dur=3.8, comms=False, channel="", priority=False):
    l = unreal.NVSubtitleLine()
    l.set_editor_property("speaker", T(speaker))
    l.set_editor_property("text", T(text))
    l.set_editor_property("duration", dur)
    if comms:
        l.set_editor_property("as_comms", True)
        l.set_editor_property("channel", T(channel))
    tl = unreal.NVTimedLine()
    tl.set_editor_property("time", t)
    tl.set_editor_property("line", l)
    return tl

# Ride ~51 s; the pursuit starts at 13 s (cars from behind), spotlight 17.6-21.8, firefight 23-28.6, crash ~31.4.
LINES = [
    line(0.8, "Station PA", "Crown Line express. Next and final stop: the Glass Crown.", 4.0, True, "Crown Line"),
    line(5.2, "Ghost-7", "Forty floors of glass up there, and they still make you ride the rail in.", 4.2),
    line(9.8, "Ops Monitor", "You're green on the board, Ghost-7. Sit back. Enjoy the view.", 3.6, True, "Directorate Ops"),
    line(13.4, "Ops Monitor", "Heads up. Patrol unit in pursuit, crossing the Crown Line on your left. Stay in the car.", 4.4, True, "Directorate Ops"),
    line(18.2, "Ghost-7", "Easy. I'm on your side.", 3.0),
    line(22.4, "CPD Unit 7", "Suspect is armed! Engaging, engaging!", 2.8, True, "CPD Band 4"),
    line(26.0, "CPD Unit 7", "Taking fire, I'm hit, I'm hi-", 2.4, True, "CPD Band 4"),
    line(32.6, "Ghost-7", "That was a patrol car.", 2.8),
    line(36.0, "AION", "Incident contained. There is nothing to see, Ghost-7.", 3.6, True, "Secure"),
    line(40.2, "Ghost-7", "There's always nothing to see up here.", 3.4),
    line(44.0, "Crown News", "Crown Sector marks a fourteenth consecutive quarter without a recorded incident.", 4.2, True, "Public Feed"),
    line(48.6, "Station PA", "Arriving: the Glass Crown. Please stand clear of the doors.", 3.6, True, "Crown Line"),
]

def import_wav(name):
    path = f"{AUD}/{name}"
    t = unreal.AssetImportTask()
    t.filename = os.path.join(SRC, name + ".wav")
    t.destination_path = AUD
    t.destination_name = name
    t.replace_existing = True
    t.automated = True
    t.save = False
    AT.import_asset_tasks([t])
    w = unreal.load_asset(path)
    w.set_editor_property("looping", True)
    EAL.save_loaded_asset(w, only_if_is_dirty=False)
    return w

def material(name):
    path = f"{MAT}/{name}"
    if EAL.does_asset_exist(path):
        m = unreal.load_asset(path)
        MEL.delete_all_material_expressions(m)
    else:
        m = AT.create_asset(name, MAT, unreal.Material, unreal.MaterialFactoryNew())
    return m

def glow(name, rgb, additive=True):
    m = material(name)
    if additive:
        m.set_editor_property("blend_mode", unreal.BlendMode.BLEND_ADDITIVE)
    m.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    c = MEL.create_material_expression(m, unreal.MaterialExpressionConstant3Vector, -300, 0)
    c.set_editor_property("constant", unreal.LinearColor(rgb[0], rgb[1], rgb[2], 1))
    MEL.connect_material_property(c, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    MEL.recompile_material(m)
    EAL.save_loaded_asset(m)
    return m

def police_paint():
    path = f"{MAT}/MI_NV_CarPaint_Patrol"
    mi = unreal.load_asset(path) if EAL.does_asset_exist(path) else AT.create_asset(
        "MI_NV_CarPaint_Patrol", MAT, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    MEL.set_material_instance_parent(mi, unreal.load_asset("/Game/NeonVeil/Vehicles/M_NV_CarPaint"))
    MEL.set_material_instance_vector_parameter_value(mi, "Paint", unreal.LinearColor(0.012, 0.02, 0.05, 1))
    MEL.set_material_instance_scalar_parameter_value(mi, "Metallic", 0.8)
    MEL.set_material_instance_scalar_parameter_value(mi, "Roughness", 0.25)
    MEL.update_material_instance(mi)
    EAL.save_loaded_asset(mi, only_if_is_dirty=False)
    return mi

def attenuation():
    path = f"{AUD}/ATT_NV_Chase"
    a = unreal.load_asset(path) if EAL.does_asset_exist(path) else AT.create_asset(
        "ATT_NV_Chase", AUD, unreal.SoundAttenuation, unreal.SoundAttenuationFactory())
    s = a.get_editor_property("attenuation")
    s.set_editor_property("attenuation_shape_extents", unreal.Vector(600, 0, 0))
    s.set_editor_property("falloff_distance", 16000.0)
    a.set_editor_property("attenuation", s)
    EAL.save_loaded_asset(a, only_if_is_dirty=False)
    return a

def main():
    siren, engine = import_wav("SW_NV_PoliceSiren"), import_wav("SW_NV_HoverEngine")
    att = attenuation()
    ride = next(a for a in EAS.get_all_level_actors() if isinstance(a, unreal.NVTramRide))
    d = next((a for a in EAS.get_all_level_actors() if a.get_actor_label() == "R_RideDirector"), None)
    if not d:
        d = EAS.spawn_actor_from_class(unreal.NVTramRideDirector, unreal.Vector(0, 0, 0), unreal.Rotator())
        d.set_actor_label("R_RideDirector")
        d.set_folder_path("R_CrownLine")
    sp = d.set_editor_property
    sp("ride", ride)
    sp("lines", LINES)
    sp("chase_start", 13.0)
    sp("side", 1.0)
    sp("suspect_mesh", unreal.load_asset("/Game/NeonVeil/Vehicles/SM_NV_HoverCar_Wedge"))
    sp("suspect_paint", unreal.load_asset("/Game/NeonVeil/Vehicles/MI_NV_CarPaint_Crimson"))
    sp("police_mesh", unreal.load_asset("/Game/NeonVeil/Vehicles/SM_NV_HoverCar"))
    sp("police_paint", police_paint())
    sp("tracer_mesh", unreal.load_asset("/Engine/BasicShapes/Cylinder"))
    sp("police_tracer", glow("M_NV_TracerBlue", (0.6, 2.5, 12.0)))
    sp("suspect_tracer", glow("M_NV_TracerRed", (14.0, 1.6, 0.4)))
    sp("light_bar_red", glow("M_NV_LightBarRed", (40.0, 0.5, 0.5), additive=False))
    sp("light_bar_blue", glow("M_NV_LightBarBlue", (0.8, 3.0, 45.0), additive=False))
    N = "/Game/NiagaraExamples"
    sp("explosion_fx", unreal.load_asset(f"{N}/FX_Explosions/NS_Explosion"))
    sp("fire_fx", unreal.load_asset(f"{N}/FX_Misc/NS_Fire"))
    sp("smoke_fx", unreal.load_asset(f"{N}/FX_Smoke/NS_Smoke_Plume"))
    sp("sparks_fx", unreal.load_asset(f"{N}/FX_Sparks/NS_Spark_Burst"))
    sp("siren_sound", siren)
    sp("engine_sound", engine)
    shots = [unreal.load_asset(f"/Game/Sci-Fi_Shots_Pack2_Game_Of_Weapons/Wave/SciFi_Shot_P2__{i}_") for i in (8, 9, 87, 88, 89)]
    sp("shot_sounds", [s for s in shots if s])
    sp("explosion_sound", unreal.load_asset("/Game/FreeWeaponSFX/Cue/GrenadeLauncher/sfx_wpn_gl_explosion_Cue"))
    sp("attenuation", att)
    log("ride duration %.1f s, path %.0f cm" % (ride.get_ride_duration(), ride.get_path_length()))
    log("director set: %d lines, %d shot sounds" % (len(LINES), len(shots)))
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    log("saved")

try:
    main()
except Exception:
    import traceback
    log(traceback.format_exc())
finally:
    open(unreal.Paths.project_saved_dir() + "NV_ride_director.txt", "w").write("\n".join(OUT))
