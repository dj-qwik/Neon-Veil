"""NEON VEIL - Glass Crown atrium centerpiece + sim-suite target restyle.
Run with L_M00_GlassCrown loaded.
 * Replaces the TEMP sculpture (column, rings, light; the dark plinth stays) with a holographic orrery:
   ModularScifiInterior holo table as the projector base, a soft light beam, and BP_NV_CrownOrrery
   (two SM_Hologram_PlanetSystem rings around a glowing planet core) turning on a RotatingMovement.
 * Training targets (BP_NVTrainingTarget_Test): brighter fresnel/scanline hologram body, a camera-facing
   glowing bullseye weak point, and a floor projector disc + ring (hidden on the hovering drone).
Report: Saved/NV_crown_orrery.txt"""
import unreal

REPORT = []
def log(*a):
    msg = " ".join(str(x) for x in a)
    REPORT.append(msg)
    unreal.log("[NV orrery] " + msg)

EAL = unreal.EditorAssetLibrary
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
MEL = unreal.MaterialEditingLibrary
SDS = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
BFL = unreal.SubobjectDataBlueprintFunctionLibrary
AT = unreal.AssetToolsHelpers.get_asset_tools()
V = unreal.Vector
HOLO_RGB = (0.05, 0.6, 1.4)
MATDIR = "/Game/NeonVeil/Materials/Holo"
PROPDIR = "/Game/NeonVeil/Props/GlassCrown"
MSI = "/Game/ModularScifiInterior"
CYL = unreal.load_asset("/Engine/BasicShapes/Cylinder")
SPHERE = unreal.load_asset("/Engine/BasicShapes/Sphere")

# ------------------------------------------------------------------ materials
def fresh_material(name, translucent=False, unlit=True):
    path = f"{MATDIR}/{name}"
    if EAL.does_asset_exist(path):
        m = unreal.load_asset(path)
        MEL.delete_all_material_expressions(m)
    else:
        m = AT.create_asset(name, MATDIR, unreal.Material, unreal.MaterialFactoryNew())
    if translucent:
        m.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
    if unlit:
        m.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    return m

def ex(m, cls, x, y, **props):
    e = MEL.create_material_expression(m, cls, x, y)
    for k, v in props.items():
        e.set_editor_property(k, v)
    return e

def c3(m, rgb, x, y):
    return ex(m, unreal.MaterialExpressionConstant3Vector, x, y, constant=unreal.LinearColor(rgb[0], rgb[1], rgb[2], 1))

def c1(m, v, x, y):
    return ex(m, unreal.MaterialExpressionConstant, x, y, r=v)

def op(m, cls, a, b, x, y):
    e = ex(m, cls, x, y)
    MEL.connect_material_expressions(a, "", e, "A")
    MEL.connect_material_expressions(b, "", e, "B")
    return e

def finish(m):
    MEL.recompile_material(m)
    EAL.save_loaded_asset(m)
    return m

def holo_target_material():
    """Cyan hologram: solid-ish core, bright fresnel rim, scanlines scrolling upward."""
    m = fresh_material("M_NV_HoloTarget", translucent=True)
    m.set_editor_property("two_sided", False)
    fres = ex(m, unreal.MaterialExpressionFresnel, -1200, 0, exponent=2.0, base_reflect_fraction=0.0)
    wp = ex(m, unreal.MaterialExpressionWorldPosition, -1200, 250)
    mask = ex(m, unreal.MaterialExpressionComponentMask, -1000, 250, r=False, g=False, b=True, a=False)
    MEL.connect_material_expressions(wp, "", mask, "")
    t = ex(m, unreal.MaterialExpressionTime, -1200, 400)
    zs = op(m, unreal.MaterialExpressionMultiply, mask, c1(m, 0.08, -1000, 330), -850, 250)
    ts = op(m, unreal.MaterialExpressionMultiply, t, c1(m, -1.2, -1000, 450), -850, 400)
    fr = ex(m, unreal.MaterialExpressionFrac, -550, 300)
    MEL.connect_material_expressions(op(m, unreal.MaterialExpressionAdd, zs, ts, -700, 300), "", fr, "")
    pw = ex(m, unreal.MaterialExpressionPower, -450, 250)
    MEL.connect_material_expressions(fr, "", pw, "Base")
    MEL.connect_material_expressions(c1(m, 6.0, -550, 420), "", pw, "Exp")
    scan = op(m, unreal.MaterialExpressionAdd, op(m, unreal.MaterialExpressionMultiply, pw, c1(m, 1.6, -450, 420), -400, 300),
              c1(m, 0.55, -400, 420), -250, 300)                       # dim body, bright thin scanlines
    rim = op(m, unreal.MaterialExpressionAdd, op(m, unreal.MaterialExpressionMultiply, fres, c1(m, 5.0, -1000, 80), -850, 0),
             c1(m, 0.5, -850, 120), -700, 0)                           # 0.5 .. 5.5
    glow = op(m, unreal.MaterialExpressionMultiply, op(m, unreal.MaterialExpressionMultiply, rim, scan, -100, 100),
              c3(m, HOLO_RGB, -250, -100), 100, 0)
    MEL.connect_material_property(glow, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    opac = ex(m, unreal.MaterialExpressionClamp, 100, 300)
    MEL.connect_material_expressions(op(m, unreal.MaterialExpressionAdd,
                                        op(m, unreal.MaterialExpressionMultiply, fres, c1(m, 0.6, -400, 600), -250, 550),
                                        c1(m, 0.42, -250, 650), -100, 550), "", opac, "")
    MEL.connect_material_property(opac, "", unreal.MaterialProperty.MP_OPACITY)
    return finish(m)

def bullseye_material():
    """Camera-facing rings from dot(view, normal): red / white / red / white / red core, pulsing."""
    m = fresh_material("M_NV_Bullseye")
    cam = ex(m, unreal.MaterialExpressionCameraVectorWS, -1200, 0)
    nrm = ex(m, unreal.MaterialExpressionVertexNormalWS, -1200, 120)
    d = ex(m, unreal.MaterialExpressionDotProduct, -1000, 50)
    MEL.connect_material_expressions(cam, "", d, "A")
    MEL.connect_material_expressions(nrm, "", d, "B")
    sat = ex(m, unreal.MaterialExpressionSaturate, -850, 50)
    MEL.connect_material_expressions(d, "", sat, "")
    fr = ex(m, unreal.MaterialExpressionFrac, -550, 50)
    MEL.connect_material_expressions(op(m, unreal.MaterialExpressionMultiply, sat, c1(m, 2.5, -850, 150), -700, 50), "", fr, "")
    rnd = ex(m, unreal.MaterialExpressionRound, -400, 50)
    MEL.connect_material_expressions(fr, "", rnd, "")
    lerp = ex(m, unreal.MaterialExpressionLinearInterpolate, -200, 0)
    MEL.connect_material_expressions(c3(m, (6.0, 0.35, 0.05), -400, -150), "", lerp, "A")
    MEL.connect_material_expressions(c3(m, (4.0, 3.6, 3.0), -400, -50), "", lerp, "B")
    MEL.connect_material_expressions(rnd, "", lerp, "Alpha")
    t = ex(m, unreal.MaterialExpressionTime, -700, 300)
    s = ex(m, unreal.MaterialExpressionSine, -400, 300, period=0.8)
    MEL.connect_material_expressions(t, "", s, "")
    pulse = op(m, unreal.MaterialExpressionAdd, op(m, unreal.MaterialExpressionMultiply, s, c1(m, 0.25, -400, 400), -250, 300),
               c1(m, 1.0, -250, 400), -100, 300)
    out = op(m, unreal.MaterialExpressionMultiply, lerp, pulse, 50, 100)
    MEL.connect_material_property(out, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    MEL.connect_material_property(c3(m, (0.0, 0.0, 0.0), -200, -250), "", unreal.MaterialProperty.MP_BASE_COLOR)
    return finish(m)

def additive_glow_material(name, rgb, beam=False):
    """Additive unlit hologram glow. beam=True: brighter in the middle, fading toward the top."""
    m = fresh_material(name, translucent=True)
    m.set_editor_property("blend_mode", unreal.BlendMode.BLEND_ADDITIVE)
    m.set_editor_property("two_sided", True)
    col = c3(m, rgb, -600, 0)
    if not beam:
        MEL.connect_material_property(col, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
        return finish(m)
    fres = ex(m, unreal.MaterialExpressionFresnel, -900, 200, exponent=1.5, base_reflect_fraction=0.0)
    inv = ex(m, unreal.MaterialExpressionOneMinus, -750, 200)
    MEL.connect_material_expressions(fres, "", inv, "")
    uv = ex(m, unreal.MaterialExpressionTextureCoordinate, -900, 350)
    v = ex(m, unreal.MaterialExpressionComponentMask, -750, 350, r=False, g=True, b=False, a=False)
    MEL.connect_material_expressions(uv, "", v, "")
    out = op(m, unreal.MaterialExpressionMultiply, op(m, unreal.MaterialExpressionMultiply, inv, v, -600, 250), col, -400, 100)
    MEL.connect_material_property(out, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    return finish(m)

def flat_material(name, base, emissive=None, rough=0.4, metal=0.0, unlit=False):
    m = fresh_material(name, unlit=unlit)
    MEL.connect_material_property(c3(m, base, -400, 0), "", unreal.MaterialProperty.MP_BASE_COLOR)
    if emissive:
        MEL.connect_material_property(c3(m, emissive, -400, 150), "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    if not unlit:
        MEL.connect_material_property(c1(m, rough, -400, 300), "", unreal.MaterialProperty.MP_ROUGHNESS)
        MEL.connect_material_property(c1(m, metal, -400, 400), "", unreal.MaterialProperty.MP_METALLIC)
    return finish(m)

# ------------------------------------------------------------------ blueprint helpers
def handles(bp):
    out = {}
    for h in SDS.k2_gather_subobject_data_for_blueprint(bp):
        obj = BFL.get_object(BFL.get_data(h))
        if obj:
            out[obj.get_name().replace("_GEN_VARIABLE", "")] = (h, obj)
    return out

def add_comp(bp, parent_handle, cls, name):
    h, fail = SDS.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=parent_handle, new_class=cls, blueprint_context=bp))
    if not BFL.is_handle_valid(h):
        raise RuntimeError(f"add {name} failed: {fail}")
    SDS.rename_subobject(h, unreal.Text(name))
    return h, BFL.get_object(BFL.get_data(h))

def mesh_comp(comp, mesh, mat=None, loc=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1), collide=False):
    comp.set_editor_property("static_mesh", mesh)
    if mat:
        comp.set_material(0, mat)
    comp.set_editor_property("relative_location", V(*loc))
    comp.set_editor_property("relative_rotation", unreal.Rotator(roll=rot[0], pitch=rot[1], yaw=rot[2]))
    comp.set_editor_property("relative_scale3d", V(*scale))
    if not collide:
        comp.set_collision_profile_name("NoCollision")
        comp.set_editor_property("can_ever_affect_navigation", False)
    comp.set_editor_property("cast_shadow", False)

# ------------------------------------------------------------------ orrery blueprint
def build_orrery_bp():
    path = f"{PROPDIR}/BP_NV_CrownOrrery"
    if EAL.does_asset_exist(path):
        EAL.delete_asset(path)
    f = unreal.BlueprintFactory()
    f.set_editor_property("parent_class", unreal.Actor)
    bp = AT.create_asset("BP_NV_CrownOrrery", PROPDIR, unreal.Blueprint, f)
    root_h = SDS.k2_gather_subobject_data_for_blueprint(bp)[0]
    ring = unreal.load_asset(f"{MSI}/Meshes/Props/SM_Hologram_PlanetSystem")
    ring_mi = unreal.load_asset(f"{MSI}/Materials/Parents/MI_Hologram_Planets")
    _, a = add_comp(bp, root_h, unreal.StaticMeshComponent, "RingOuter")
    mesh_comp(a, ring, ring_mi, loc=(0, 0, -105), scale=(3.2, 3.2, 3.2))
    _, b = add_comp(bp, root_h, unreal.StaticMeshComponent, "RingInner")
    mesh_comp(b, ring, ring_mi, loc=(0, 0, -45), rot=(22, 8, 140), scale=(1.9, 1.9, 1.4))
    _, core = add_comp(bp, root_h, unreal.StaticMeshComponent, "Core")
    mesh_comp(core, SPHERE, unreal.load_asset(f"{MSI}/Materials/Space/MI_Planet_Blueclouds"), loc=(0, 0, -50), scale=(1.1, 1.1, 1.1))
    _, halo = add_comp(bp, root_h, unreal.StaticMeshComponent, "CoreHalo")
    mesh_comp(halo, SPHERE, unreal.load_asset(f"{MSI}/Materials/Parents/MI_Hologram_Forcefield"), loc=(0, 0, -50), scale=(1.35, 1.35, 1.35))
    _, pl = add_comp(bp, root_h, unreal.PointLightComponent, "CoreLight")
    pl.set_editor_property("intensity_units", unreal.LightUnits.LUMENS)
    pl.set_editor_property("intensity", 4000.0)
    pl.set_editor_property("attenuation_radius", 1400.0)
    pl.set_editor_property("light_color", unreal.Color(r=150, g=225, b=255, a=255))
    pl.set_editor_property("cast_shadows", False)
    pl.set_editor_property("relative_location", V(0, 0, -50))
    _, rm = add_comp(bp, root_h, unreal.RotatingMovementComponent, "Spin")
    rm.set_editor_property("rotation_rate", unreal.Rotator(roll=0, pitch=0, yaw=7.0))
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    EAL.save_loaded_asset(bp)
    log("orrery bp", list(handles(bp).keys()))
    return unreal.EditorAssetLibrary.load_blueprint_class(path)

def by_label(label):
    for a in EAS.get_all_level_actors():
        if a.get_actor_label() == label:
            return a
    return None

def place_mesh_actor(label, mesh, mat, loc, scale, folder):
    a = EAS.spawn_actor_from_class(unreal.StaticMeshActor, V(*loc), unreal.Rotator())
    a.set_actor_label(label)
    a.set_folder_path(folder)
    c = a.static_mesh_component
    c.set_static_mesh(mesh)
    if mat:
        c.set_material(0, mat)
    a.set_actor_scale3d(V(*scale))
    return a

def centerpiece():
    plinth = by_label("B_Sculpture_Plinth")
    folder = plinth.get_folder_path() if plinth else "B_Atrium"
    for lbl in ["B_Sculpture_Column", "B_Sculpture_Light"] + [f"B_Sculpture_Ring{i}" for i in range(4)] + \
               ["B_Orrery_Base", "B_Orrery_Beam", "B_Orrery"]:
        a = by_label(lbl)
        if a:
            EAS.destroy_actor(a)
            log("removed", lbl)
    x, y = 4900, 0
    top = 40.0
    if plinth:
        o, e = plinth.get_actor_bounds(False)
        x, y, top = o.x, o.y, o.z + e.z
    table = unreal.load_asset(f"{MSI}/Meshes/Props/SM_HoloTable")
    base = place_mesh_actor("B_Orrery_Base", table, None, (x, y, top), (2.0, 2.0, 1.4), folder)
    table_top = top + 95.1 * 1.4
    beam = place_mesh_actor("B_Orrery_Beam", CYL, unreal.load_asset(f"{MSI}/Materials/Parents/MI_Hologram_Forcefield"),
                            (x, y, (table_top + 420 + top) / 2 + 30), (1.5, 1.5, (420 + top - table_top) / 100.0 + 0.6), folder)
    beam.static_mesh_component.set_collision_profile_name("NoCollision")
    beam.static_mesh_component.set_editor_property("cast_shadow", False)
    orr = EAS.spawn_actor_from_class(build_orrery_bp(), V(x, y, top + 480), unreal.Rotator())
    orr.set_actor_label("B_Orrery")
    orr.set_folder_path(folder)
    log("centerpiece at", x, y, "plinth top", top, "table top", table_top)

# ------------------------------------------------------------------ targets
def restyle_targets():
    holo = holo_target_material()
    bull = bullseye_material()
    disc_m = flat_material("M_NV_ProjectorDisc", (0.03, 0.035, 0.04), None, 0.25, 1.0)
    ring_m = flat_material("M_NV_ProjectorRing", (0, 0, 0), (0.25, 1.8, 3.0), unlit=True)
    bp = unreal.load_asset("/Game/NeonVeil/Tests/BP_NVTrainingTarget_Test")
    hs = handles(bp)
    log("target comps before", list(hs.keys()))
    body = hs["Body"][1]
    body.set_material(0, holo)
    body.set_editor_property("cast_shadow", False)
    wp = hs["WeakPoint"][1]
    wp.set_editor_property("static_mesh", SPHERE)
    wp.set_material(0, bull)
    wp.set_editor_property("relative_scale3d", V(0.75, 0.75, 0.2))
    # Shield shows only when the target has MaxShield (BeginPlay/Activate set it); hide it in the editor otherwise.
    hs["ShieldMesh"][1].set_editor_property("visible", False)
    root_h = hs["Root"][0]
    if "ProjectorDisc" not in hs:
        _, disc = add_comp(bp, root_h, unreal.StaticMeshComponent, "ProjectorDisc")
    else:
        disc = hs["ProjectorDisc"][1]
    mesh_comp(disc, CYL, disc_m, loc=(0, 0, 2.5), scale=(0.8, 0.8, 0.05))
    if "ProjectorRing" not in hs:
        _, ring = add_comp(bp, root_h, unreal.StaticMeshComponent, "ProjectorRing")
    else:
        ring = hs["ProjectorRing"][1]
    mesh_comp(ring, CYL, ring_m, loc=(0, 0, 1.5), scale=(0.9, 0.9, 0.03))
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    EAL.save_loaded_asset(bp)
    log("target comps after", list(handles(bp).keys()))
    # The hovering drone has no floor projector; refresh instance overrides of materials.
    for a in EAS.get_all_level_actors():
        lbl = a.get_actor_label()
        if not lbl.startswith("C_Target_"):
            continue
        for c in a.get_components_by_class(unreal.StaticMeshComponent):
            n = c.get_name()
            if n == "Body" and lbl != "C_Target_Drone":
                c.set_material(0, holo)
            if n == "WeakPoint":
                c.set_material(0, bull)
                c.set_editor_property("static_mesh", SPHERE)
            if n == "ShieldMesh":
                c.set_visibility(False)
            if n in ("ProjectorDisc", "ProjectorRing") and lbl == "C_Target_Drone":
                c.set_visibility(False)
                c.set_hidden_in_game(True)
        log("target", lbl, [ (c.get_name(), [m.get_name() if m else None for m in c.get_materials()]) for c in a.get_components_by_class(unreal.StaticMeshComponent)])

def orrery_materials():
    ring_m = additive_glow_material("M_NV_OrreryGlow", (0.3, 2.2, 4.5))
    beam_m = additive_glow_material("M_NV_HoloBeam", (0.05, 0.45, 0.9), beam=True)
    bp = unreal.load_asset(f"{PROPDIR}/BP_NV_CrownOrrery")
    hs = handles(bp)
    for n in ("RingOuter", "RingInner"):
        hs[n][1].set_material(0, ring_m)
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    EAL.save_loaded_asset(bp)
    beam = by_label("B_Orrery_Beam")
    beam.static_mesh_component.set_material(0, beam_m)
    orr = by_label("B_Orrery")
    for c in orr.get_components_by_class(unreal.StaticMeshComponent):
        if c.get_name().startswith("Ring"):
            c.set_material(0, ring_m)
            c.set_editor_property("relative_scale3d", c.get_editor_property("relative_scale3d") * 1.0)
        log("orrery comp", c.get_name(), [m.get_name() if m else None for m in c.get_materials()], c.get_num_materials())
    log("orrery materials applied")

def main():
    import sys
    if "tweak" in sys.argv:
        orrery_materials()
        restyle_targets()
        unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
        log("saved (tweak)")
        return
    centerpiece()
    orrery_materials()
    restyle_targets()
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    log("saved")

try:
    main()
except Exception as exc:
    import traceback
    log("ERROR", exc, traceback.format_exc())
finally:
    with open(unreal.Paths.project_saved_dir() + "NV_crown_orrery.txt", "w", encoding="utf-8") as fh:
        fh.write("\n".join(REPORT))
