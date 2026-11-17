"""NEON VEIL - Glass Crown follow-ups (L_M00_GlassCrown loaded):
 * Orrery: much larger (fills the atrium between the mezzanine rail and the glazing), cyan rings fixed on the
   Blueprint itself, beam stretched to meet it; atrium lights dimmed so it reads.
 * Sentry drone target restored: SimDrone body visible again and its glowing core lens back as the weak point
   (the sim-target restyle had turned the core into a 4 m bullseye sphere and hidden the body).
Args: [dim factor, default 0.35]. Report: Saved/NV_crown_fixes.txt"""
import sys
import unreal

OUT = []
def log(*a):
    OUT.append(" ".join(str(x) for x in a))

EAL = unreal.EditorAssetLibrary
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
SDS = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
BFL = unreal.SubobjectDataBlueprintFunctionLibrary
V = unreal.Vector
args = [a for a in sys.argv[1:] if not a.endswith(".py")]
DIM = float(args[0]) if args else 0.35
SCALE = 1.75
ATRIUM = (3500, 6300, -1100, 1100)

def by_label(label):
    return next((a for a in EAS.get_all_level_actors() if a.get_actor_label() == label), None)

def trace_up(x, y, z):
    w = unreal.EditorLevelLibrary.get_editor_world()
    hit = unreal.SystemLibrary.line_trace_single(w, V(x, y, z), V(x, y, z + 3000), unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,
                                                 True, [], unreal.DrawDebugTrace.NONE, True)
    if not hit:
        return None
    t = hit.to_tuple()
    vecs = [v for v in t if isinstance(v, unreal.Vector)]
    return vecs[0].z if vecs else None

def orrery():
    glow = unreal.load_asset("/Game/NeonVeil/Materials/Holo/M_NV_OrreryGlow")
    bp = unreal.load_asset("/Game/NeonVeil/Props/GlassCrown/BP_NV_CrownOrrery")
    for h in SDS.k2_gather_subobject_data_for_blueprint(bp):
        o = BFL.get_object(BFL.get_data(h))
        if o and o.get_name().replace("_GEN_VARIABLE", "").startswith("Ring"):
            o.set_material(0, glow)
        if o and o.get_name().replace("_GEN_VARIABLE", "") == "CoreLight":
            o.set_editor_property("attenuation_radius", 2600.0)
            o.set_editor_property("intensity", 9000.0)
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    EAL.save_loaded_asset(bp, only_if_is_dirty=False)
    orr, beam, base = by_label("B_Orrery"), by_label("B_Orrery_Beam"), by_label("B_Orrery_Base")
    x, y = orr.get_actor_location().x, orr.get_actor_location().y
    ceiling = trace_up(x, y, 700) or 1200.0
    log("ceiling above orrery", ceiling)
    # outer ring spans actor z -105*s*... : mesh 0..66.5 at scale 3.2 from rel z -105 -> actor-relative -105..+108, times SCALE
    z = min(ceiling - 120.0 - 110.0 * SCALE, 760.0)
    orr.set_actor_scale3d(V(SCALE, SCALE, SCALE))
    orr.set_actor_location(V(x, y, z), False, False)
    for c in orr.get_components_by_class(unreal.StaticMeshComponent):
        if c.get_name().startswith("Ring"):
            c.set_material(0, glow)
    for c in orr.get_components_by_class(unreal.PointLightComponent):
        c.set_editor_property("attenuation_radius", 2600.0)
        c.set_editor_property("intensity", 9000.0)
    o, e = orr.get_actor_bounds(False)
    log("orrery z", z, "bounds centre", o, "extent", e)
    table_top = base.get_actor_bounds(False)[0].z + base.get_actor_bounds(False)[1].z
    planet_bottom = z - 50.0 * SCALE - 55.0 * SCALE
    beam.set_actor_location(V(x, y, (table_top + planet_bottom) / 2.0), False, False)
    beam.set_actor_scale3d(V(2.2, 2.2, max(planet_bottom - table_top, 50.0) / 100.0))
    log("beam", table_top, "->", planet_bottom)

def dim_lights():
    n = 0
    for a in EAS.get_all_level_actors():
        if a.get_actor_label() == "B_Orrery":
            continue
        loc = a.get_actor_location()
        if not (ATRIUM[0] <= loc.x <= ATRIUM[1] and ATRIUM[2] <= loc.y <= ATRIUM[3]):
            continue
        for c in a.get_components_by_class(unreal.LightComponent):
            if isinstance(c, (unreal.SkyLightComponent, unreal.DirectionalLightComponent)):
                continue
            before = c.get_editor_property("intensity")
            c.set_editor_property("intensity", before * DIM)
            n += 1
            log("dim", a.get_actor_label(), c.get_class().get_name(), round(before, 1), "->", round(before * DIM, 1))
    log("lights dimmed", n)

def drone():
    d = by_label("C_Target_Drone")
    c = {x.get_name(): x for x in d.get_components_by_class(unreal.SceneComponent)}
    body, core = c["Body"], c["WeakPoint"]
    log("drone before: body vis", body.is_visible(), "mesh", body.static_mesh.get_name() if body.static_mesh else None,
        "scale", body.get_editor_property("relative_scale3d"), "| core mesh", core.static_mesh.get_name() if core.static_mesh else None,
        "scale", core.get_editor_property("relative_scale3d"))
    core.set_static_mesh(unreal.load_asset("/Game/NeonVeil/Fab/SimDrone/SM_SimDrone_Core"))
    core.set_editor_property("override_materials", [])
    core.set_editor_property("relative_scale3d", V(1, 1, 1))
    core.set_editor_property("relative_rotation", unreal.Rotator(0, 0, 0))
    core.set_editor_property("relative_location", V(0, 0, 0))
    body.set_visibility(True)
    core.set_visibility(True)
    for n in ("Figure", "FigureGun", "ProjectorDisc", "ProjectorRing"):
        if n in c:
            c[n].set_visibility(False)
            c[n].set_hidden_in_game(True)
    log("drone after: body vis", body.is_visible(), "core", core.static_mesh.get_name(), [m.get_name() if m else None for m in core.get_materials()])

try:
    orrery()
    dim_lights()
    drone()
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    log("saved")
except Exception:
    import traceback
    log(traceback.format_exc())
finally:
    open(unreal.Paths.project_saved_dir() + "NV_crown_fixes.txt", "w").write("\n".join(OUT))
