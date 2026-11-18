"""Light covers: give every indoor light that has no visible fixture a small lamp the player can see and shoot.

For each point / spot / rect light in the open level that is not already a shootable group (nv_shootable_lights.py),
not driven by a room switch, not an alarm, story or sign light and not attached to anything:
  ceiling within 1.6 m above and no floor within 1.5 m below -> a 50 cm glowing panel in a 56 cm dark rim, flush under the ceiling
  else a floor within 45 cm below and the light is named as an up-light (Floor/Up/Step/Path...)
                                 -> a 24 cm floor puck in a 30 cm rim (low fill lights get nothing)
  else a wall within 0.7 m       -> a 36 x 14 cm wall sconce (glowing bar in a rim) on that wall at light height
  else (open-air fill light, or an under-floor light behind a grille) -> skipped
Panels glow in the light's own colour family (warm, white, cyan, red, magenta). They are markers only: no shadows,
no Lumen bounce or emissive light, query-only collision that blocks nothing but bullets (a hit on the panel breaks
its light). Everything goes in folder
Light_Covers with tag NVLIGHTCOVER; re-running removes and rebuilds them. Then run nv_shootable_lights.py so the
new panels become the lights' fixtures.
Args: "report" = list only. Report: Saved/NV_covers_<map>.txt"""
import unreal, sys, re, math
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
EAL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary
AT = unreal.AssetToolsHelpers.get_asset_tools()
W = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
V = unreal.Vector
REPORT = "report" in sys.argv
TAG, FOLDER = "NVLIGHTCOVER", "Light_Covers"
CUBE = unreal.load_asset("/Engine/BasicShapes/Cube")
D = "/Game/NeonVeil/Materials/Fx"
TQ = unreal.TraceTypeQuery.TRACE_TYPE_QUERY1
out = []

def mi(name, parent, vec=None, scal=None):
    path = f"{D}/{name}"
    m = unreal.load_asset(path) if EAL.does_asset_exist(path) else AT.create_asset(name, D, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    MEL.set_material_instance_parent(m, unreal.load_asset(parent))
    for k, v in (vec or {}).items():
        MEL.set_material_instance_vector_parameter_value(m, k, unreal.LinearColor(*v, 1))
    for k, v in (scal or {}).items():
        MEL.set_material_instance_scalar_parameter_value(m, k, v)
    EAL.save_loaded_asset(m)
    return m

GLOW = "/Game/NeonVeil/Materials/Prologue/M_NV_Glow"
PAINT = "/Game/NeonVeil/Vehicles/M_NV_CarPaint"
FAMS = {  # name: (reference colour, panel colour)
    "Warm":    ((1.0, 0.62, 0.30), (1.0, 0.70, 0.42)),
    "White":   ((1.0, 1.0, 1.0),   (0.92, 0.96, 1.0)),
    "Cyan":    ((0.25, 0.85, 1.0), (0.35, 0.90, 1.0)),
    "Red":     ((1.0, 0.12, 0.10), (1.0, 0.22, 0.18)),
    "Magenta": ((0.95, 0.25, 0.85), (1.0, 0.35, 0.90)),
}
if not REPORT:
    PANEL = {k: mi("MI_NV_LampPanel_" + k, GLOW, {"Color": c[1]}, {"Glow": 3.0}) for k, c in FAMS.items()}
    RIM = mi("MI_NV_LampRim", PAINT, {"Paint": (0.035, 0.037, 0.042)}, {"Metallic": 0.85, "Roughness": 0.35})

def family(col):
    r, g, b = col.r, col.g, col.b
    m = max(r, g, b, 1e-4); r, g, b = r / m, g / m, b / m
    return min(FAMS, key=lambda k: sum((x - y) ** 2 for x, y in zip((r, g, b), FAMS[k][0])))

# clear old covers
old = [a for a in EAS.get_all_level_actors() if TAG in [str(t) for t in a.tags]]
if not REPORT:
    for a in old:
        EAS.destroy_actor(a)

# groups whose fixture is a real lamp (not one of our covers): those lights are already visible and shootable
real_groups = set()
for a in EAS.get_all_level_actors():
    tg = [str(t) for t in a.tags]
    if "NVLightFixture" in tg and TAG not in tg:
        real_groups.update(t for t in tg if t.startswith("NVLightGroup_"))
switched = set()
for a in EAS.get_all_level_actors():
    if a.get_class().get_name() == "NVRoomLightSwitch":
        for l in a.get_editor_property("lights"):
            if l: switched.add(l.get_name())
SKIP = re.compile(r"beacon|emergency|alarm|core|holo|orrery|sign|screen|neon|fill|bounce|rim|key|ambient|accent|sky|sun|moon|city|window|"
                  r"car|tram|train|cab|glow|lantern|spill|brief|search|monolith|kiosk|director|console|evac|tube|portrait|face|eye|muzzle|flash|fx|rain|fog|reflect", re.I)

def tr(s, e):
    h = unreal.SystemLibrary.line_trace_single(W, s, e, TQ, True, [], unreal.DrawDebugTrace.NONE, True)
    return h.to_tuple() if h else None

def spawn(label, loc, rot, size, mat, coll_vis):
    a = EAS.spawn_actor_from_object(CUBE, loc, rot)
    a.set_actor_label(label); a.set_folder_path(FOLDER); a.tags = [unreal.Name(TAG)]
    a.set_actor_scale3d(V(size[0] / 100.0, size[1] / 100.0, size[2] / 100.0))
    c = a.static_mesh_component
    c.set_material(0, mat)
    # markers only: no shadows, no bounce or emissive light into Lumen, so the room's lighting is unchanged
    c.set_editor_property("cast_shadow", False)
    c.set_editor_property("affect_dynamic_indirect_lighting", False)
    c.set_editor_property("affect_distance_field_lighting", False)
    c.set_collision_profile_name("Custom")
    c.set_collision_enabled(unreal.CollisionEnabled.QUERY_ONLY)
    c.set_collision_response_to_all_channels(unreal.CollisionResponseType.ECR_IGNORE)
    if coll_vis:
        c.set_collision_response_to_channel(unreal.CollisionChannel.ECC_VISIBILITY, unreal.CollisionResponseType.ECR_BLOCK)
    return a

n = {"ceiling": 0, "floor": 0, "wall": 0, "skipped": 0}
for l in EAS.get_all_level_actors():
    if not isinstance(l, unreal.Light) or isinstance(l, (unreal.DirectionalLight, unreal.SkyLight)):
        continue
    lab = l.get_actor_label()
    if (l.get_name() in switched or l.get_attach_parent_actor() or SKIP.search(lab)
            or any(str(t) in real_groups for t in l.tags) or not l.root_component.is_visible()):
        continue
    p = l.get_actor_location()
    lc = l.get_editor_property("light_component")
    col = lc.get_editor_property("light_color")
    fam = family(unreal.LinearColor(col.r / 255.0, col.g / 255.0, col.b / 255.0, 1))
    up = tr(p, p + V(0, 0, 160))
    dn = tr(p, p - V(0, 0, 150))
    if up and up[9] and dn and dn[9] and dn[4].z > p.z - 60:
        # a surface just above and a floor right below: an under-floor / in-pit light, already behind a grille
        n["skipped"] += 1
        out.append("skip    %-30s under-floor light" % lab)
        continue
    if up and up[9] and up[4].z > p.z + 5 and not (dn and dn[9]):
        z = up[4].z
        out.append("ceiling %-30s %-7s %.0f cm above" % (lab, fam, z - p.z))
        n["ceiling"] += 1
        if not REPORT:
            yaw = l.get_actor_rotation().yaw if isinstance(l, unreal.RectLight) else 0.0
            spawn("CoverRim_" + lab, V(p.x, p.y, z - 1.5), unreal.Rotator(0, yaw, 0), (56, 56, 3), RIM, False)
            spawn("LampCover_" + lab, V(p.x, p.y, z - 3.3), unreal.Rotator(0, yaw, 0), (50, 50, 1.2), PANEL[fam], True)
        continue
    dn = tr(p, p - V(0, 0, 45))
    if dn and dn[9] and dn[4].z < p.z - 1 and not (up and up[9]) and re.search(r"floor|uplight|_up|ground|step|path|plinth", lab, re.I):
        z = dn[4].z
        out.append("floor   %-30s %-7s %.0f cm up" % (lab, fam, p.z - z))
        n["floor"] += 1
        if not REPORT:
            spawn("CoverRim_" + lab, V(p.x, p.y, z + 0.6), unreal.Rotator(0, 0, 0), (30, 30, 1.2), RIM, False)
            spawn("LampCover_" + lab, V(p.x, p.y, z + 1.4), unreal.Rotator(0, 0, 0), (24, 24, 0.8), PANEL[fam], True)
        continue
    best = None
    for k in range(8):
        ang = math.radians(k * 45)
        d = V(math.cos(ang), math.sin(ang), 0)
        h = tr(p, p + d * 70)
        if h and h[9] and (best is None or h[3] < best[0][3]):
            best = (h, d)
    if best:
        h, d = best
        nrm = h[6] if hasattr(h[6], "x") else V(-d.x, -d.y, 0)
        yaw = math.degrees(math.atan2(nrm.y, nrm.x))
        hp = h[4]
        out.append("wall    %-30s %-7s %.0f cm from wall" % (lab, fam, (hp - p).length()))
        n["wall"] += 1
        if not REPORT:
            spawn("CoverRim_" + lab, hp + nrm * 1.5, unreal.Rotator(0, yaw, 0), (3, 40, 18), RIM, False)
            spawn("LampCover_" + lab, hp + nrm * 3.4, unreal.Rotator(0, yaw, 0), (1.2, 34, 12), PANEL[fam], True)
        continue
    n["skipped"] += 1
    out.append("skip    %-30s open-air light" % lab)

out.insert(0, "covers: %d ceiling panels, %d floor pucks, %d wall sconces, %d open-air lights skipped (%d old covers removed)%s"
           % (n["ceiling"], n["floor"], n["wall"], n["skipped"], len(old), "  [report only]" if REPORT else ""))
if not REPORT:
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
open(unreal.Paths.project_saved_dir() + "NV_covers_%s.txt" % W.get_name(), "w").write("\n".join(out))
