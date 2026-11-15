"""Performance pass for the prologue level (6 GB GPU target). Baseline (PIE, street spawn): 42 ms frame, GPU-bound
(game thread mostly waiting), 281 local lights (60 shadow-casting station spots with 164 m radii that reach the street
123 m below), 3,750 shadow-casting meshes, video memory ~300 MB over budget.
  Lights: station spots get a sensible radius (they light a 4-8 m tall hall), only every 4th spot keeps a shadow, all
  local lights fade out with distance, small point lights stop feeding volumetric fog.
  Shadows: emissive/glow dressing, windows, tunnel ribs, neon outlines, small props and far skyline stop casting.
Idempotent; saves the level. Report: Saved/NV_optimize.txt"""
import math, unreal, collections
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
OUT = []
C = collections.Counter()
HUB = unreal.Vector(7046, -11400, -12000)

# ------------------------------------------------------------------ lights
spots = []
for a in EAS.get_all_level_actors():
    for c in a.get_components_by_class(unreal.LocalLightComponent):
        l = c.get_world_location()
        station = l.z > -500
        r = c.get_editor_property("attenuation_radius")
        if isinstance(c, unreal.SpotLightComponent) and station and r > 1500:
            c.set_editor_property("attenuation_radius", 1500.0); C["spot radius 16384->1500"] += 1
        if isinstance(c, unreal.PointLightComponent) and c.get_editor_property("volumetric_scattering_intensity") > 0 and r < 1500:
            c.set_editor_property("volumetric_scattering_intensity", 0.0); C["point fog off"] += 1
        # fade out with distance: station interiors are short sight lines; street lights a little further
        dd = 4500.0 if station else 9000.0
        if r > 3000:
            dd = 20000.0
        c.set_editor_property("max_draw_distance", dd)
        c.set_editor_property("max_distance_fade_range", dd * 0.2)
        C["distance-faded"] += 1
        if isinstance(c, unreal.SpotLightComponent) and station and a.get_actor_label().startswith("SpotLight"):
            spots.append((a.get_actor_label(), c))     # the station kit's spots (all shadowed originally)
spots.sort(key=lambda s: s[0])
for i, (lab, c) in enumerate(spots):
    keep = (i % 4 == 0)
    c.set_editor_property("cast_shadows", keep)
    C["spot shadow kept" if keep else "spot shadow off"] += 1

# ------------------------------------------------------------------ shadow casters
DECOR = ("HB_Win", "HB_Crown_", "Tun_", "TunT_", "Gate_", "Hub_Band", "Hub_Edge", "HB_Step_Edge", "HB_Fin_", "HB_Parapet_Glow",
         "Low_", "Mega_", "Spire_", "Sky_", "Crown_", "Moon", "Search_", "Skybridge_", "Blade", "Roof_", "RoofFrame_", "Shaft_Band")
# (results, PIE at the street spawn: frame 42.1 -> 19.3 ms, GPU 41.1 -> 13.9 ms, draw calls 1390 -> 830;
#  standalone 1280x720: 16.7 ms frame (vsync), GPU 12.0 ms, game thread 11.5 ms, no video-memory-over-budget warning)
def is_glow(m):
    while m is not None:
        n = m.get_name()
        if "Glow" in n or n.startswith(("M_NV_TrafficCar", "M_NV_Hologram")):
            return True
        m = m.get_editor_property("parent") if isinstance(m, unreal.MaterialInstance) else None
    return False
for a in EAS.get_all_level_actors():
    lab = a.get_actor_label()
    if a.get_class().get_name().startswith("BPP_"):
        continue      # packed-level buildings rebuild their instances from the blueprint: changes here don't stick
    for c in a.get_components_by_class(unreal.StaticMeshComponent):
        if not c.get_editor_property("cast_shadow"):
            continue
        reason = None
        try:
            mats = [c.get_material(i) for i in range(c.get_num_materials())]
        except Exception:
            mats = []
        if mats and all(is_glow(m) for m in mats if m):
            reason = "emissive"
        elif lab.startswith(DECOR):
            reason = "decor"
        else:
            o, e, _ = unreal.SystemLibrary.get_component_bounds(c)
            if max(e.x, e.y, e.z) < 120:
                reason = "small prop"
            elif (o - HUB).length() > 30000 and o.z < 0 and max(e.x, e.y) > 0:
                reason = "far skyline"
        if reason:
            c.set_editor_property("cast_shadow", False)
            C[f"shadow off: {reason}"] += 1
# ------------------------------------------------------------------ sky light: no real-time capture (there is no sky
# atmosphere to capture; it recaptured the scene every frame and printed an on-screen warning)
for a in EAS.get_all_level_actors():
    for c in a.get_components_by_class(unreal.SkyLightComponent):
        if c.get_editor_property("real_time_capture"):
            c.set_editor_property("real_time_capture", False); C["sky light real-time capture off"] += 1

# ------------------------------------------------------------------ station FX only run while the player is near
fx = []
for a in EAS.get_all_level_actors():
    if a.get_class().get_name() == "Emitter" and a.get_actor_location().z > -500:
        if unreal.Name("NVZoneFX") not in a.tags:
            a.tags = list(a.tags) + [unreal.Name("NVZoneFX")]
        fx.append(a)
if hasattr(unreal, "NVZoneActivator") and fx:
    for a in list(EAS.get_all_level_actors()):
        if a.get_actor_label() == "Zone_StationFX":
            EAS.destroy_actor(a)
    xs = [a.get_actor_location() for a in fx]
    z = EAS.spawn_actor_from_class(unreal.NVZoneActivator, unreal.Vector(0, 0, 400))
    z.set_actor_label("Zone_StationFX"); z.set_folder_path("P_Optim")
    z.set_editor_property("region_min", unreal.Vector(min(v.x for v in xs) - 500, min(v.y for v in xs) - 500, -300))
    z.set_editor_property("region_max", unreal.Vector(max(v.x for v in xs) + 500, max(v.y for v in xs) + 500, 1200))
    z.set_editor_property("margin", 1500.0)
    C[f"station FX zone-managed"] = len(fx)

# ------------------------------------------------------------------ far traffic lanes: fewer cars (instances re-uploaded every frame)
FAR = {"Sky_View_A": 55, "Sky_View_B": 45, "Sky_View_C": 40, "Sky_View_D": 35, "Sky_Far_A": 40}
for a in EAS.get_all_level_actors():
    n = FAR.get(a.get_actor_label())
    if n and isinstance(a, unreal.NVTrafficStream):
        a.set_editor_property("vehicles_per_direction", n); C["far lanes thinned"] += 1

for k, v in sorted(C.items()):
    OUT.append(f"{k}: {v}")
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)   # lights/meshes live in external actor packages
open(unreal.Paths.project_saved_dir() + "NV_optimize.txt", "w").write("\n".join(OUT))
