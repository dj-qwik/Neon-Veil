"""Lobby + lift lit like a public building at night, and rain only heard outside.
Prologue: brighter neutral-white lobby ceiling lights and cab light, a Lobby_Interior_PP volume (above the street
night grade) and the Lift_PostProcess with their own fixed interior exposure and neutral white balance; every
rain / open-air ambient sound is tagged NVOutdoorAmb and an NVAmbienceZone fades it down (with a low-pass) once the
player is off the street (lobby, lift, station). Glass Crown: the city-rain beds inside the crown are cut to a
whisper; the tram ride plays rain on the cabin roof (NVTramRide RainSound) that dies away as it docks.
args: [lobby_ev] [lift_ev] [lobby_cd]   Idempotent; saves both maps. Report: Saved/NV_interior_light_audio.txt"""
import sys, unreal
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
LES = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
V = unreal.Vector
args = [float(a) for a in sys.argv[2:5]] if len(sys.argv) > 2 else []
LOBBY_EV = args[0] if len(args) > 0 else 3.0
LIFT_EV = args[1] if len(args) > 1 else 3.0
LOBBY_CD = args[2] if len(args) > 2 else 320.0
ZS = -12000.0
X0, X1, Y0, Y1 = 5846, 8246, -4924, -6524
OUT = []
RAIN = "/Game/SoulCity/Sound/Cue/AmbientLooping/Rain_Heavy_Ext_Cue"
def pp(s, name, val):
    s.set_editor_property(name, val)
    s.set_editor_property("override_" + name, True)
def interior_grade(p, ev):
    s = p.get_editor_property("settings")
    pp(s, "auto_exposure_bias", 0.0)
    pp(s, "auto_exposure_min_brightness", ev)
    pp(s, "auto_exposure_max_brightness", ev + 0.5)
    pp(s, "white_temp", 6300.0)
    pp(s, "white_tint", 0.0)
    pp(s, "bloom_intensity", 0.55)
    pp(s, "vignette_intensity", 0.3)
    for k in ("color_saturation", "color_contrast", "color_gain", "color_gamma"):
        pp(s, k, unreal.Vector4(1.0, 1.0, 1.0, 1.0))
    pp(s, "color_contrast", unreal.Vector4(1.04, 1.04, 1.04, 1.0))
    p.set_editor_property("settings", s)
def light(a, cd, radius, color):
    c = a.get_component_by_class(unreal.LocalLightComponent)
    c.set_editor_property("intensity_units", unreal.LightUnits.CANDELAS)
    c.set_editor_property("intensity", cd)
    c.set_editor_property("attenuation_radius", radius)
    c.set_editor_property("light_color", unreal.Color(r=int(color[0] * 255), g=int(color[1] * 255), b=int(color[2] * 255), a=255))
    c.set_editor_property("max_draw_distance", 0.0)

# ------------------------------------------------------------------ prologue
LES.load_level("/Game/NeonVeil/Maps/M00/L_M00_Prologue")
actors = list(EAS.get_all_level_actors())
by = {a.get_actor_label(): a for a in actors}
WHITE = (0.94, 0.97, 1.0)
nl = 0
for lab, a in by.items():
    if lab.startswith("Lobby_PL_"):
        light(a, LOBBY_CD, 1200.0, WHITE); nl += 1
    elif lab.startswith("Lobby_Lamp_") and lab.endswith("_L"):
        light(a, 60.0, 600.0, (1.0, 0.8, 0.6)); nl += 1
    elif lab == "Lobby_LiftGlow":
        light(a, 90.0, 800.0, (0.35, 0.85, 1.0)); nl += 1
    elif lab == "Cab_Light":
        light(a, 160.0, 520.0, WHITE); nl += 1
OUT.append(f"lights retuned: {nl}")
# extra fill along the lobby's long axis so no corner falls into the dark
for i, y in enumerate((-5124, -5724, -6324)):
    for j, x in enumerate((6146, 7946)):
        lab = f"Lobby_Fill_{i}_{j}"
        a = by.get(lab) or EAS.spawn_actor_from_class(unreal.PointLight, V(x, y, ZS + 330), unreal.Rotator())
        a.set_actor_label(lab); a.set_folder_path("P_Lobby")
        a.point_light_component.set_mobility(unreal.ComponentMobility.MOVABLE)
        a.point_light_component.set_editor_property("cast_shadows", False)
        a.point_light_component.set_editor_property("volumetric_scattering_intensity", 0.0)
        light(a, LOBBY_CD * 0.5, 900.0, WHITE)
# the lift cab rides the whole shaft: a second, upward-facing glow so the cab interior reads lit
lab = "Cab_Fill"
cab = by.get("Cab_Light")
a = by.get(lab) or EAS.spawn_actor_from_class(unreal.PointLight, V(7046, -4572, ZS + 120), unreal.Rotator())
a.set_actor_label(lab); a.set_folder_path(str(cab.get_folder_path()) if cab else "P_Lift")
a.point_light_component.set_mobility(unreal.ComponentMobility.MOVABLE)
a.point_light_component.set_editor_property("cast_shadows", False)
light(a, 70.0, 380.0, WHITE)
lift_actor = by.get("B_Lift")
if lift_actor:
    parts = list(lift_actor.get_editor_property("cab_parts"))
    if a not in parts:
        parts.append(a)
        lift_actor.set_editor_property("cab_parts", parts)
    OUT.append(f"Cab_Fill rides with B_Lift ({len(parts)} cab parts)")

# interior exposure: lobby volume (above the street night PP), lift volume retuned
p = by.get("Lobby_Interior_PP") or EAS.spawn_actor_from_class(unreal.PostProcessVolume, V(7046, (Y0 + Y1) / 2, ZS + 200), unreal.Rotator())
p.set_actor_label("Lobby_Interior_PP"); p.set_folder_path("P_Lobby")
p.set_actor_location(V(7046, (Y0 + Y1) / 2 + 40, ZS + 200), False, False)
p.set_actor_scale3d(V((X1 - X0) / 200.0, (abs(Y1 - Y0) - 80) / 200.0, 420 / 200.0))
p.set_editor_property("priority", 4.0)
p.set_editor_property("blend_radius", 250.0)
p.set_editor_property("unbound", False)
interior_grade(p, LOBBY_EV)
lift = by.get("Lift_PostProcess")
if lift:
    lift.set_editor_property("priority", 4.5)
    interior_grade(lift, LIFT_EV)
OUT.append(f"PP: lobby EV {LOBBY_EV}, lift EV {LIFT_EV}")

# rain only outside
tagged = []
for a in actors:
    if isinstance(a, unreal.AmbientSound):
        snd = a.get_editor_property("audio_component").get_editor_property("sound")
        sp = snd.get_path_name() if snd else ""
        lab = a.get_actor_label()
        outdoor = "Rain" in sp or lab in ("Street_RainAmb", "Street_CityAmb")
        tags = [t for t in a.tags if str(t) != "NVOutdoorAmb"]
        if outdoor:
            tags.append(unreal.Name("NVOutdoorAmb")); tagged.append(lab)
        a.tags = tags
        OUT.append(f"  sound {lab}: {sp.split('/')[-1]} {'OUTDOOR' if outdoor else ''}")
z = by.get("Street_AmbienceZone") or EAS.spawn_actor_from_class(unreal.NVAmbienceZone, V(7046, -12000, ZS + 300), unreal.Rotator())
z.set_actor_label("Street_AmbienceZone"); z.set_folder_path("P_Street")
z.set_editor_property("outdoor", [unreal.Box(V(-20000, -60000, ZS - 3000), V(34000, -6620, ZS + 6000))])
z.set_editor_property("blend_distance", 450.0)
z.set_editor_property("indoor_volume", 0.05)
z.set_editor_property("indoor_low_pass_hz", 650.0)
OUT.append(f"outdoor-tagged: {tagged}")
LES.save_current_level()
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)

# ------------------------------------------------------------------ Glass Crown
LES.load_level("/Game/NeonVeil/Maps/M00/L_M00_GlassCrown")
rain = unreal.load_asset(RAIN)
for a in EAS.get_all_level_actors():
    lab = a.get_actor_label()
    if isinstance(a, unreal.AmbientSound) and lab.startswith("AMB_CityRain"):
        ac = a.get_editor_property("audio_component")
        ac.set_editor_property("volume_multiplier", 0.05)
        ac.set_editor_property("enable_low_pass_filter", True)
        ac.set_editor_property("low_pass_filter_frequency", 600.0)
        OUT.append(f"crown {lab}: 0.05, LP 600")
    if isinstance(a, unreal.NVTramRide):
        a.set_editor_property("rain_sound", rain)
        a.set_editor_property("rain_volume", 0.5)
        a.set_editor_property("rain_low_pass_hz", 2600.0)
        a.set_editor_property("rain_fade_distance", 5000.0)
        OUT.append(f"tram ride {lab}: rain on the roof")
LES.save_current_level()
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
LES.load_level("/Game/NeonVeil/Maps/M00/L_M00_Prologue")
open(unreal.Paths.project_saved_dir() + "NV_interior_light_audio.txt", "w").write("\n".join(OUT))
