"""Shootable lights setup for the open level (runtime: Source/NeonVeil/World/NVLightBreakSubsystem).

Pairs every point / spot / rect light with the light fixture mesh it sits in or under
(lamps, bulbs, sconces, luminaires, light strips within 130 cm; ceiling tiles with their own lamp
material slot within 30 cm), then tags both with a shared "NVLightGroup_<map>_<n>" and the fixture with
"NVLightFixture". The fixture's glowing material slots get component tags "NVLampSlot_<i>" (they go dark when shot).
Fixtures get query-only collision that blocks bullets (Visibility) but never the player.
Skipped: lights driven by NVRoomLightSwitch, lights attached to other actors, fixtures over 4 m, screens and signs.
Also makes MI_NV_LampDead and imports the shatter sound. Idempotent: re-running re-pairs from scratch.
Report: Saved/NV_shootable_<map>.txt"""
import unreal, re, os
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
EAL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary
AT = unreal.AssetToolsHelpers.get_asset_tools()
W = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
V = unreal.Vector
MAP = W.get_name().replace("L_M00_", "")
out = []

# ---------------------------------------------------------------- assets
D = "/Game/NeonVeil/Materials/Fx"
if not EAL.does_asset_exist(D + "/MI_NV_LampDead"):
    m = AT.create_asset("MI_NV_LampDead", D, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    MEL.set_material_instance_parent(m, unreal.load_asset("/Game/NeonVeil/Vehicles/M_NV_CarPaint"))
    MEL.set_material_instance_vector_parameter_value(m, "Paint", unreal.LinearColor(0.012, 0.012, 0.014, 1))
    MEL.set_material_instance_scalar_parameter_value(m, "Metallic", 0.1)
    MEL.set_material_instance_scalar_parameter_value(m, "Roughness", 0.3)
    EAL.save_loaded_asset(m)
    out.append("made MI_NV_LampDead")
SFX = "/Game/NeonVeil/Audio/SFX/SFX_NV_LightShatter"
if not EAL.does_asset_exist(SFX):
    t = unreal.AssetImportTask()
    t.filename = os.path.join(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir()), "RawAssets", "Audio", "SFX_NV_LightShatter.wav")
    t.destination_path = "/Game/NeonVeil/Audio/SFX"; t.automated = True; t.save = True; t.replace_existing = True
    AT.import_asset_tasks([t])
    out.append("imported shatter sound: %s" % EAL.does_asset_exist(SFX))

# ---------------------------------------------------------------- clear old tags
GP = "NVLightGroup_"
for a in EAS.get_all_level_actors():
    tg = [t for t in a.tags if not str(t).startswith(GP) and str(t) != "NVLightFixture"]
    if len(tg) != len(a.tags):
        a.modify(); a.tags = tg
    if isinstance(a, unreal.StaticMeshActor):
        c = a.static_mesh_component
        ct = [t for t in c.component_tags if not str(t).startswith("NVLampSlot_")]
        if len(ct) != len(c.component_tags):
            c.modify(); c.component_tags = ct

# ---------------------------------------------------------------- lights
switched = set()
for a in EAS.get_all_level_actors():
    if a.get_class().get_name() == "NVRoomLightSwitch":
        try:
            for l in a.get_editor_property("lights"):
                if l: switched.add(l.get_name())
        except Exception as e:
            out.append("switch read failed %s" % e)
lights = []
for a in EAS.get_all_level_actors():
    if not isinstance(a, unreal.Light) or a.get_name() in switched or a.get_attach_parent_actor():
        continue
    if isinstance(a, unreal.DirectionalLight) or isinstance(a, unreal.SkyLight):
        continue
    lights.append(a)

# ---------------------------------------------------------------- fixtures
FIX = re.compile(r"lamp|light|bulb|sconce|fixture|led|neon|tube|lantern|flood|spot|downlight|lightbar|strip_?light|chandelier|luminaire", re.I)
NOT = re.compile(r"screen|sign|holo|board|panel_?face|billboard|ad_|advert|window|glass|frame|totem|monitor|display|wall|floor|ceil|switch|arrow", re.I)
GLOW = re.compile(r"glow|emiss|lamp|(^|[_ ])lights?([_ ]|$)|whitelight|bulb|neon|_lit|tube|led|bright", re.I)
SLOTLAMP = re.compile(r"(^|[_ ])lights?([_ ]|$)|lamp|bulb|emiss", re.I)
cands = []
for a in EAS.get_all_level_actors():
    if not isinstance(a, unreal.StaticMeshActor):
        continue
    c = a.static_mesh_component
    m = c.static_mesh
    if not m or not c.is_visible() or a.get_editor_property("hidden"):
        continue
    lab = a.get_actor_label()
    if re.search(r"beacon|emergency|alarm", lab, re.I) or re.search(r"core|monolith|kiosk|holo|orrery", lab + m.get_name(), re.I):
        continue          # alarm beacons and story props keep working
    o, e = a.get_actor_bounds(False)
    if max(e.x, e.y, e.z) * 2 > 400:
        continue
    if FIX.search(lab + " " + m.get_name()) and (not NOT.search(lab) or re.search(r"light|lamp", lab, re.I)):
        cands.append((a, o, e, 130.0))
        continue
    # ceiling tiles with their own lamp material slot (clinic ceilings): only lights right at them
    mats = [x.get_name() if x else "" for x in c.get_materials()]
    lampslots = [i for i, x in enumerate(mats) if SLOTLAMP.search(x)]
    if lampslots and len(lampslots) < len(mats) and re.search(r"ceil", lab, re.I):
        cands.append((a, o, e, 30.0))
out.append("%d lights, %d fixture candidates, %d switch-driven lights skipped" % (len(lights), len(cands), len(switched)))

def dist_to_box(p, o, e):
    dx = max(abs(p.x - o.x) - e.x, 0); dy = max(abs(p.y - o.y) - e.y, 0); dz = max(abs(p.z - o.z) - e.z, 0)
    return (dx * dx + dy * dy + dz * dz) ** 0.5

groups = {}
for l in lights:
    p = l.get_actor_location()
    best, bd = None, 1e9
    for a, o, e, r in cands:
        d = dist_to_box(p, o, e)
        if d <= r and d < bd:
            best, bd = a, d
    if best:
        groups.setdefault(best, []).append(l)

n = 0
for fx, ls in groups.items():
    n += 1
    tag = unreal.Name("%s%s_%d" % (GP, MAP, n))
    fx.modify(); fx.tags = list(fx.tags) + [tag, unreal.Name("NVLightFixture")]
    c = fx.static_mesh_component
    slots = []
    for i, mat in enumerate(c.get_materials()):
        nm = (mat.get_name() if mat else "") + " " + (mat.get_base_material().get_name() if mat and mat.get_base_material() else "")
        if GLOW.search(nm):
            slots.append(i)
    if slots and len(slots) < len(c.get_materials()):
        c.modify(); c.component_tags = list(c.component_tags) + [unreal.Name("NVLampSlot_%d" % i) for i in slots]
    # bullets hit it, the player doesn't
    if c.get_collision_profile_name() in ("NoCollision", "BlockAll", "BlockAllDynamic", "Default") or True:
        prof = c.get_collision_profile_name()
        if prof == "NoCollision":
            c.modify()
            c.set_collision_profile_name("Custom")
            c.set_collision_enabled(unreal.CollisionEnabled.QUERY_ONLY)
            c.set_collision_response_to_all_channels(unreal.CollisionResponseType.ECR_IGNORE)
            c.set_collision_response_to_channel(unreal.CollisionChannel.ECC_VISIBILITY, unreal.CollisionResponseType.ECR_BLOCK)
    for l in ls:
        l.modify(); l.tags = list(l.tags) + [tag]
        rc = l.root_component
        if rc.mobility == unreal.ComponentMobility.STATIC:
            rc.set_mobility(unreal.ComponentMobility.MOVABLE)
    out.append("%-22s %-34s lights %d slots %s" % (str(tag)[len(GP):], fx.get_actor_label(), len(ls), slots or "all"))
out.insert(0, "%d shootable fixtures, %d lights" % (n, sum(len(v) for v in groups.values())))
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
open(unreal.Paths.project_saved_dir() + "NV_shootable_%s.txt" % W.get_name(), "w").write("\n".join(out))
