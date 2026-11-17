"""Glass Crown atrium: make the room genuinely dim (so it reads dim from the sky bridge too) instead of darkening the
camera on entry, then add low floor lighting for the walkways and patrolling guards.
- B_AtriumMood: drops the -1.3 EV bias / vignette; instead pins auto-exposure to the bright end (EV100 = PIN) so the eye
  doesn't open up inside and the room looks the same from the bridge and from within.
- The 4 ceiling point lights x LIGHTS; atrium-only copies (*_Atrium) of the wall / ceiling / floor / luminaire
  materials with brightness and glow scaled down. Shared materials elsewhere are untouched.
- B_Atrium/FloorLights: a grid of soft, unshadowed downlights hung low that pool on the floor.
Idempotent. Args: [pin EV100, default 4.0]. Report: Saved/NV_atrium_dim.txt"""
import sys
import unreal
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
EAL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary
AT = unreal.AssetToolsHelpers.get_asset_tools()
V = unreal.Vector
OUT = []
def log(*a): OUT.append(" ".join(str(x) for x in a))
args = [a for a in sys.argv[1:] if not a.endswith(".py")]
PIN = float(args[0]) if args else 4.0
LIGHTS = 0.45
ATRIUM = (3500, 6300, -1100, 1100)
DST = "/Game/NeonVeil/Materials/Atrium"
# scalar -> scale, per source material (missing params are skipped)
SCALE = {
    "MI_Wall_D1": {"Brightness": 0.45, "GlowIntensity_1": 0.5, "GlowIntensity_2": 0.5},
    "MI_Wall_D2": {"Brightness": 0.45, "GlowIntensity_1": 0.5, "GlowIntensity_2": 0.5},
    "MI_Ceiling_A": {"Brightness": 0.45, "GlowIntensity_1": 0.4, "GlowIntensity_2": 0.4},
    "MI_Ceiling_B": {"Brightness": 0.45, "GlowIntensity_1": 0.4, "GlowIntensity_2": 0.4},
    "MI_Floor_A": {"Brightness": 0.55, "GlowIntensity_1": 0.6, "GlowIntensity_2": 0.6},
    "MI_Floor_B": {"Brightness": 0.55, "GlowIntensity_1": 0.6, "GlowIntensity_2": 0.6},
    "MI_DIR_CeramicPanel": {"Brightness": 0.5},
    "MI_DIR_Titanium": {"Brightness": 0.6},
    "MI_DIR_PolishedStone": {"Brightness": 0.6},
    "MI_DIR_WhiteLight": {"EmissiveStrength": 0.35},
}

def in_atrium(l):
    return ATRIUM[0] <= l.x <= ATRIUM[1] and ATRIUM[2] <= l.y <= ATRIUM[3]

def atrium_mi(src):
    name = src.get_name() + "_Atrium"
    path = f"{DST}/{name}"
    mi = unreal.load_asset(path) if EAL.does_asset_exist(path) else AT.create_asset(
        name, DST, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    MEL.set_material_instance_parent(mi, src)
    names = [str(n) for n in MEL.get_scalar_parameter_names(src)]
    for p, k in SCALE[src.get_name()].items():
        if p in names:
            v = MEL.get_material_instance_scalar_parameter_value(src, p) if isinstance(src, unreal.MaterialInstance) else 1.0
            MEL.set_material_instance_scalar_parameter_value(mi, p, v * k)
    MEL.update_material_instance(mi)
    EAL.save_loaded_asset(mi, only_if_is_dirty=False)
    return mi

def materials():
    made, n = {}, 0
    for a in EAS.get_all_level_actors():
        for c in a.get_components_by_class(unreal.StaticMeshComponent):
            if not in_atrium(c.get_world_location()):
                continue
            for i in range(c.get_num_materials()):
                m = c.get_material(i)
                if not m or m.get_name() not in SCALE:
                    continue
                if m.get_name() not in made:
                    made[m.get_name()] = atrium_mi(m)
                c.set_material(i, made[m.get_name()])
                n += 1
    log("atrium material slots swapped:", n, "materials:", sorted(made))

def lights():
    for a in EAS.get_all_level_actors():
        if a.get_actor_label() in ("B_Light0", "B_Light1", "B_Light2", "B_Light3"):
            if "nv_atrium_dim" in [str(t) for t in a.tags]:
                log("already dimmed", a.get_actor_label()); continue
            for c in a.get_components_by_class(unreal.PointLightComponent):
                v = c.get_editor_property("intensity")
                c.set_editor_property("intensity", v * LIGHTS)
                log("light", a.get_actor_label(), round(v), "->", round(v * LIGHTS))
            a.tags = list(a.tags) + [unreal.Name("nv_atrium_dim")]

def mood():
    ppv = next(a for a in EAS.get_all_level_actors() if a.get_actor_label() == "B_AtriumMood")
    s = ppv.get_editor_property("settings")
    s.set_editor_property("override_auto_exposure_bias", False)
    s.set_editor_property("override_vignette_intensity", False)
    s.set_editor_property("override_auto_exposure_min_brightness", True)
    s.set_editor_property("override_auto_exposure_max_brightness", True)
    s.set_editor_property("auto_exposure_min_brightness", PIN)
    s.set_editor_property("auto_exposure_max_brightness", PIN)
    ppv.set_editor_property("settings", s)
    ppv.set_editor_property("blend_radius", 400.0)
    log("B_AtriumMood: bias/vignette off, exposure pinned at EV100", PIN)

def floor_lights():
    for a in EAS.get_all_level_actors():
        if str(a.get_folder_path()) == "B_Atrium/FloorLights":
            a.destroy_actor()
    floor = next((a for a in EAS.get_all_level_actors() if a.get_actor_label() == "B_Floor"), None)
    fz = floor.get_actor_bounds(False)[0].z + floor.get_actor_bounds(False)[1].z if floor else 0.0
    base = next((a for a in EAS.get_all_level_actors() if a.get_actor_label() == "B_Orrery_Base"), None)
    bc = base.get_actor_location() if base else V(4900, 0, 0)
    n = 0
    xs = [3850 + i * 540 for i in range(5)]
    ys = [-780, -260, 260, 780]
    for x in xs:
        for y in ys:
            if abs(x - bc.x) < 450 and abs(y - bc.y) < 450:
                continue
            l = EAS.spawn_actor_from_class(unreal.SpotLight, V(x, y, fz + 430), unreal.Rotator(roll=0, pitch=-90, yaw=0))
            l.set_actor_label("B_FloorLight_%d" % n)
            l.set_folder_path("B_Atrium/FloorLights")
            c = l.get_component_by_class(unreal.SpotLightComponent)
            c.set_editor_property("intensity_units", unreal.LightUnits.LUMENS)
            c.set_editor_property("intensity", 1300.0)
            c.set_editor_property("attenuation_radius", 950.0)
            c.set_editor_property("inner_cone_angle", 22.0)
            c.set_editor_property("outer_cone_angle", 52.0)
            c.set_editor_property("light_color", unreal.Color(r=190, g=220, b=255, a=255))
            c.set_editor_property("cast_shadows", False)
            c.set_editor_property("volumetric_scattering_intensity", 0.0)
            c.set_editor_property("specular_scale", 0.6)
            n += 1
    log("floor lights:", n, "at z", fz + 430)

try:
    materials()
    lights()
    mood()
    floor_lights()
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    log("saved")
except Exception:
    import traceback
    log(traceback.format_exc())
open(unreal.Paths.project_saved_dir() + "NV_atrium_dim.txt", "w").write("\n".join(OUT))
