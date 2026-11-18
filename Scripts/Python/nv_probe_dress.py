"""Probe for the prologue dressing pass: hub sign occluders, crew-pass blockers, NPC floor traces,
screen materials, departure board material, and the prop catalogue of the station kits.
Report: Saved/NV_probe_dress.txt"""
import unreal

OUT = []
def log(*a):
    OUT.append(" ".join(str(x) for x in a))

EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
LES = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
MAP = "/Game/NeonVeil/Maps/M00/L_M00_Prologue"
UES = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
if not UES.get_editor_world().get_path_name().startswith(MAP):
    LES.load_level(MAP)
W = UES.get_editor_world()
ACTORS = list(EAS.get_all_level_actors())

def fmt(v):
    return "(%d,%d,%d)" % (v.x, v.y, v.z)

def desc(a):
    o, e = a.get_actor_bounds(False)
    mesh = ""
    if isinstance(a, unreal.StaticMeshActor):
        sm = a.static_mesh_component.static_mesh
        mesh = sm.get_path_name() if sm else ""
        mats = [m.get_name() if m else "-" for m in a.static_mesh_component.get_materials()]
        mesh += " mats=" + ",".join(mats)
    return "%s [%s] folder=%s loc=%s rot=%s scale=%s bounds o=%s e=%s %s" % (
        a.get_actor_label(), a.get_class().get_name(), a.get_folder_path(), fmt(a.get_actor_location()),
        a.get_actor_rotation(), a.get_actor_scale3d(), fmt(o), fmt(e), mesh)

def in_box(a, lo, hi):
    o, e = a.get_actor_bounds(False)
    if e.x > 20000 or e.y > 20000:
        return False
    return (o.x + e.x >= lo[0] and o.x - e.x <= hi[0] and o.y + e.y >= lo[1] and o.y - e.y <= hi[1]
            and o.z + e.z >= lo[2] and o.z - e.z <= hi[2])

def find(label):
    for a in ACTORS:
        if a.get_actor_label() == label:
            return a
    return None

# ---- hub sign
for lab in ("S_Hub", "S_Hub2", "S_LobbyLift"):
    s = find(lab)
    if s:
        log("SIGN", desc(s))
s = find("S_Hub")
if s:
    p = s.get_actor_location()
    log("== occluders around hub sign")
    for a in ACTORS:
        if a is s:
            continue
        if in_box(a, (p.x - 1100, p.y - 900, p.z - 900), (p.x + 1100, p.y + 40, p.z + 500)):
            log("  ", desc(a))

# ---- hub entrance (street side) dressing context
log("== hub entrance area (street level)")
for a in ACTORS:
    if in_box(a, (6000, -6900, -12050), (8100, -6300, -11500)):
        log("  ", desc(a))

# ---- crew pass
cp = find("I_CrewPass")
if cp:
    p = cp.get_actor_location()
    log("CREWPASS", desc(cp))
    for a in ACTORS:
        if a is cp:
            continue
        if in_box(a, (p.x - 700, p.y - 700, p.z - 50), (p.x + 700, p.y + 700, p.z + 400)):
            log("  ", desc(a))

# ---- characters / NPCs
log("== characters")
for a in ACTORS:
    if isinstance(a, unreal.Character):
        l = a.get_actor_location()
        hit = unreal.SystemLibrary.line_trace_single(W, l, l - unreal.Vector(0, 0, 3000), unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,
                                                     False, [a], unreal.DrawDebugTrace.NONE, True)
        hs = ""
        if hit:
            t = hit.to_tuple()
            # (blocking_hit, initial_overlap, time, distance, location, impact_point, normal, impact_normal, phys_mat, hit_actor, hit_component, ...)
            hs = "hit d=%.0f actor=%s comp=%s" % (t[3], t[9].get_actor_label() if t[9] else None, t[10].get_name() if t[10] else None)
        else:
            hs = "NO FLOOR"
        cap = a.capsule_component.get_scaled_capsule_half_height()
        log("  CHAR", a.get_actor_label(), a.get_class().get_name(), fmt(l), "half", cap, hs)

# ---- screens / monitors
log("== screen-like materials in level")
seen = {}
for a in ACTORS:
    for c in a.get_components_by_class(unreal.StaticMeshComponent):
        sm = c.static_mesh
        if not sm:
            continue
        for i, m in enumerate(c.get_materials()):
            if not m:
                continue
            n = m.get_name()
            if any(k in n.lower() for k in ("screen", "monitor", "display", "warning", "offline", "holo", "billboard", "ad_", "map")):
                key = (sm.get_name(), n)
                seen.setdefault(key, []).append((a.get_actor_label(), fmt(c.get_world_location()), i))
for (smn, mn), lst in sorted(seen.items()):
    log("  ", smn, mn, len(lst), lst[:6])

# ---- material params for interesting materials
def mparams(m):
    try:
        out = []
        if isinstance(m, unreal.MaterialInstance):
            for tp in m.get_editor_property("texture_parameter_values"):
                out.append("T:%s=%s" % (tp.parameter_info.name, tp.parameter_value.get_path_name() if tp.parameter_value else None))
            for sp in m.get_editor_property("scalar_parameter_values"):
                out.append("S:%s=%s" % (sp.parameter_info.name, sp.parameter_value))
            par = m.get_editor_property("parent")
            out.append("parent=" + (par.get_path_name() if par else "None"))
        else:
            out.append("BASE " + m.get_path_name())
        names = unreal.MaterialEditingLibrary.get_texture_parameter_names(m if isinstance(m, unreal.Material) else m.get_base_material())
        out.append("texparams=" + ",".join(str(x) for x in names))
        return " ".join(out)
    except Exception as e:
        return "ERR %s" % e

done = set()
for (smn, mn), lst in seen.items():
    for a in ACTORS:
        if a.get_actor_label() == lst[0][0]:
            for c in a.get_components_by_class(unreal.StaticMeshComponent):
                for m in c.get_materials():
                    if m and m.get_name() == mn and mn not in done:
                        done.add(mn)
                        log("MAT", m.get_path_name(), mparams(m))
            break

b = find("I_DepartureBoard")
if b:
    log("BOARD", desc(b))
    for c in b.get_components_by_class(unreal.StaticMeshComponent):
        for m in c.get_materials():
            if m:
                log("  BOARDMAT", m.get_path_name(), mparams(m))

# ---- prop catalogue
AR = unreal.AssetRegistryHelpers.get_asset_registry()
for root in ("/Game/SciFiTramStation", "/Game/ModularScifiInterior", "/Game/SciFiLightPack", "/Game/Sci-Fi_Light_Pack",
             "/Game/SciFiHallway", "/Game/Sci_Fi_Hallway", "/Game/MedicalClinicSciFi", "/Game/HologramShader", "/Game/CityStreet"):
    assets = AR.get_assets(unreal.ARFilter(package_paths=[root], recursive_paths=True,
                                           class_paths=[unreal.TopLevelAssetPath("/Script/Engine", "StaticMesh")]))
    if not assets:
        continue
    log("== MESHES", root, len(assets))
    for ad in assets:
        log("   ", str(ad.package_name))
log("== content roots")
for p in sorted(set(str(x) for x in AR.get_sub_paths("/Game", False))):
    log("   ", p)

open(unreal.Paths.project_saved_dir() + "NV_probe_dress.txt", "w").write("\n".join(OUT))
