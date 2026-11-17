"""NEON VEIL - sim-suite targets become holographic soldiers / robot soldiers; the head is the weak point.
Run with L_M00_GlassCrown loaded, in two passes:
  py nv_holo_soldiers.py build   -> adds Figure (skeletal, rifle aim pose) + FigureGun to BP_NVTrainingTarget_Test,
                                    hides the collision cylinder, assigns soldier / robot per placed target
  py nv_holo_soldiers.py fit     -> reads the posed head and right hand from a placed target and fits the head
                                    weak point (collision + red holo halo) and the rifle to them
The capsule-ish Body cylinder stays as the (invisible) body hitbox; WeakPoint sphere = head hitbox.
Report: Saved/NV_holo_soldiers.txt"""
import sys
import unreal

REPORT = []
def log(*a):
    msg = " ".join(str(x) for x in a)
    REPORT.append(msg)
    unreal.log("[NV holo soldiers] " + msg)

EAL = unreal.EditorAssetLibrary
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
MEL = unreal.MaterialEditingLibrary
SDS = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
BFL = unreal.SubobjectDataBlueprintFunctionLibrary
AT = unreal.AssetToolsHelpers.get_asset_tools()
V = unreal.Vector
BP_PATH = "/Game/NeonVeil/Tests/BP_NVTrainingTarget_Test"
MATDIR = "/Game/NeonVeil/Materials/Holo"
SOLDIER = "/Game/RetroFuturisticSoldier/Meshes/SKM_Soldier_Manny"
ROBOT = "/Game/Characters/Mannequins/Meshes/SKM_Manny_Simple"
GUN = "/Game/KINEMATION/Sci-fi_FPS_Pack/Weapons/Gepard/SKM_Gepard"
POSE = "/Game/Characters/Mannequins/Anims/Rifle/MF_Rifle_Idle_ADS"
ROBOT_TARGETS = ("C_Target_Shielded0", "C_Target_Shielded1", "C_Target_Concealed1", "C_Target_Moving1")
BODY_SCALE = V(0.55, 0.55, 1.5)     # 55 cm wide, 150 cm tall torso/legs hitbox
BODY_Z = 75.0
HEAD_DIAMETER = 30.0
# Kestrel third-person grip relative to hand_r (from nv_ghost7_weapons_tp.py)
GRIP = unreal.Transform(V(-11.484, 3.823, 7.540), unreal.Rotator(roll=8.95, pitch=2.41, yaw=79.74), V(1, 1, 1))

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

def head_mark_material():
    """Additive red fresnel halo around the head hitbox."""
    name = "M_NV_HoloHeadMark"
    path = f"{MATDIR}/{name}"
    if EAL.does_asset_exist(path):
        m = unreal.load_asset(path)
        MEL.delete_all_material_expressions(m)
    else:
        m = AT.create_asset(name, MATDIR, unreal.Material, unreal.MaterialFactoryNew())
    m.set_editor_property("blend_mode", unreal.BlendMode.BLEND_ADDITIVE)
    m.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    fres = MEL.create_material_expression(m, unreal.MaterialExpressionFresnel, -900, 0)
    fres.set_editor_property("exponent", 2.5)
    fres.set_editor_property("base_reflect_fraction", 0.0)
    k = MEL.create_material_expression(m, unreal.MaterialExpressionConstant, -900, 150)
    k.set_editor_property("r", 0.15)
    add = MEL.create_material_expression(m, unreal.MaterialExpressionAdd, -700, 50)
    MEL.connect_material_expressions(fres, "", add, "A")
    MEL.connect_material_expressions(k, "", add, "B")
    t = MEL.create_material_expression(m, unreal.MaterialExpressionTime, -900, 300)
    s = MEL.create_material_expression(m, unreal.MaterialExpressionSine, -750, 300)
    s.set_editor_property("period", 1.0)
    MEL.connect_material_expressions(t, "", s, "")
    pk = MEL.create_material_expression(m, unreal.MaterialExpressionConstant, -750, 400)
    pk.set_editor_property("r", 0.3)
    pm = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -600, 300)
    MEL.connect_material_expressions(s, "", pm, "A")
    MEL.connect_material_expressions(pk, "", pm, "B")
    one = MEL.create_material_expression(m, unreal.MaterialExpressionConstant, -600, 400)
    one.set_editor_property("r", 1.0)
    pulse = MEL.create_material_expression(m, unreal.MaterialExpressionAdd, -450, 300)
    MEL.connect_material_expressions(pm, "", pulse, "A")
    MEL.connect_material_expressions(one, "", pulse, "B")
    col = MEL.create_material_expression(m, unreal.MaterialExpressionConstant3Vector, -700, -150)
    col.set_editor_property("constant", unreal.LinearColor(3.0, 0.18, 0.06, 1))
    m1 = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -450, 0)
    MEL.connect_material_expressions(add, "", m1, "A")
    MEL.connect_material_expressions(col, "", m1, "B")
    m2 = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -250, 100)
    MEL.connect_material_expressions(m1, "", m2, "A")
    MEL.connect_material_expressions(pulse, "", m2, "B")
    MEL.connect_material_property(m2, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    MEL.recompile_material(m)
    EAL.save_loaded_asset(m)
    return m

def holo():
    m = unreal.load_asset(f"{MATDIR}/M_NV_HoloTarget")
    if not m.get_editor_property("used_with_skeletal_mesh"):
        m.set_editor_property("used_with_skeletal_mesh", True)
        MEL.recompile_material(m)
        EAL.save_loaded_asset(m)
    return m

def dress_figure(fig, mesh_path, mat):
    sk = unreal.load_asset(mesh_path)
    fig.set_skeletal_mesh_asset(sk) if hasattr(fig, "set_skeletal_mesh_asset") else fig.set_editor_property("skeletal_mesh_asset", sk)
    for i in range(len(sk.get_editor_property("materials"))):
        fig.set_material(i, mat)

def setup_figure(fig, mat):
    dress_figure(fig, SOLDIER, mat)
    fig.set_editor_property("animation_mode", unreal.AnimationMode.ANIMATION_SINGLE_NODE)
    data = unreal.SingleAnimationPlayData()
    data.set_editor_property("anim_to_play", unreal.load_asset(POSE))
    data.set_editor_property("saved_looping", True)
    data.set_editor_property("saved_playing", True)
    fig.set_editor_property("animation_data", data)
    try:
        fig.set_editor_property("update_animation_in_editor", True)   # instances only (template refuses it)
    except Exception:
        pass
    fig.set_editor_property("relative_rotation", unreal.Rotator(roll=0, pitch=0, yaw=-90))   # mesh faces +Y; actor faces +X
    fig.set_editor_property("relative_location", V(0, 0, 0))
    fig.set_collision_profile_name("NoCollision")
    fig.set_editor_property("cast_shadow", False)
    fig.set_editor_property("visibility_based_anim_tick_option", unreal.VisibilityBasedAnimTickOption.ALWAYS_TICK_POSE_AND_REFRESH_BONES)

def build():
    mat = holo()
    head_m = head_mark_material()
    bp = unreal.load_asset(BP_PATH)
    hs = handles(bp)
    root_h = hs["Root"][0]
    fig = hs["Figure"][1] if "Figure" in hs else add_comp(bp, root_h, unreal.SkeletalMeshComponent, "Figure")[1]
    setup_figure(fig, mat)
    hs = handles(bp)
    if "FigureGun" not in hs:
        add_comp(bp, hs["Figure"][0], unreal.SkeletalMeshComponent, "FigureGun")
        hs = handles(bp)
    gun = hs["FigureGun"][1]
    kestrel = unreal.load_asset("/Game/NeonVeil/Data/Weapons/DA_Weapon_Kestrel")
    gmesh = unreal.load_asset(GUN)
    log("gun mesh", gmesh.get_path_name() if gmesh else None)
    if gmesh:
        gun.set_editor_property("skeletal_mesh_asset", gmesh)
        for i in range(len(gmesh.get_editor_property("materials"))):
            gun.set_material(i, mat)
    gun.set_collision_profile_name("NoCollision")
    gun.set_editor_property("cast_shadow", False)
    body = hs["Body"][1]
    body.set_editor_property("visible", False)          # stays as the body hitbox
    body.set_editor_property("relative_scale3d", BODY_SCALE)
    body.set_editor_property("relative_location", V(0, 0, BODY_Z))
    wp = hs["WeakPoint"][1]
    wp.set_material(0, head_m)
    wp.set_editor_property("cast_shadow", False)
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    EAL.save_loaded_asset(bp)
    log("bp comps", list(handles(bp).keys()))
    for a in targets():
        lbl = a.get_actor_label()
        comps = {c.get_name(): c for c in a.get_components_by_class(unreal.SceneComponent)}
        if lbl == "C_Target_Drone":
            comps["Figure"].set_visibility(False, True)
            comps["Figure"].set_hidden_in_game(True, True)
            comps["Body"].set_visibility(True)
            continue
        comps["Body"].set_visibility(False)
        comps["Body"].set_editor_property("relative_scale3d", BODY_SCALE)
        comps["Body"].set_editor_property("relative_location", V(0, 0, BODY_Z))
        comps["WeakPoint"].set_material(0, head_m)
        dress_figure(comps["Figure"], ROBOT if lbl in ROBOT_TARGETS else SOLDIER, mat)
        if hasattr(comps["Figure"], "set_update_animation_in_editor"):
            comps["Figure"].set_update_animation_in_editor(True)
        log("target", lbl, "robot" if lbl in ROBOT_TARGETS else "soldier")
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()

def targets():
    return [a for a in EAS.get_all_level_actors() if a.get_actor_label().startswith("C_Target_")]

def fit():
    probe = next(a for a in targets() if a.get_actor_label() == "C_Target_Moving0")
    comps = {c.get_name(): c for c in probe.get_components_by_class(unreal.SceneComponent)}
    fig, body = comps["Figure"], comps["Body"]
    fig.tick_animation(0.5, False) if hasattr(fig, "tick_animation") else None
    fig.refresh_bone_transforms() if hasattr(fig, "refresh_bone_transforms") else None
    head = fig.get_socket_transform("head", unreal.RelativeTransformSpace.RTS_WORLD)
    hand = fig.get_socket_transform("hand_r", unreal.RelativeTransformSpace.RTS_WORLD)
    root_loc = probe.get_actor_location()
    log("head", head.translation - root_loc, "hand_r", hand.translation - root_loc)
    # head centre: a little above the head bone
    head_c = head.translation + V(0, 0, 9.0)
    body_tf = body.get_world_transform()
    wp_rel = body_tf.inverse_transform_location(head_c)
    bs = BODY_SCALE
    wp_scale = V(HEAD_DIAMETER / 100.0 / bs.x, HEAD_DIAMETER / 100.0 / bs.y, HEAD_DIAMETER / 100.0 / bs.z)
    # Lay the rifle along right hand -> left hand (the pose's support hand), stock at the right hand.
    hand_l = fig.get_socket_transform("hand_l", unreal.RelativeTransformSpace.RTS_WORLD)
    fwd = (hand_l.translation - hand.translation)
    fwd = fwd / max(fwd.length(), 0.001)
    # Turn the figure so its aim (right->left hand, flattened) points along the actor's forward (at the player).
    aim = V(fwd.x, fwd.y, 0)
    want = probe.get_actor_forward_vector()
    import math
    delta = math.degrees(math.atan2(want.y, want.x) - math.atan2(aim.y, aim.x))
    delta = (delta + 180.0) % 360.0 - 180.0
    log("aim yaw error", delta)
    if abs(delta) > 2.0:
        new_yaw = fig.get_editor_property("relative_rotation").yaw + delta
        bp = unreal.load_asset(BP_PATH)
        handles(bp)["Figure"][1].set_editor_property("relative_rotation", unreal.Rotator(roll=0, pitch=0, yaw=new_yaw))
        unreal.BlueprintEditorLibrary.compile_blueprint(bp)
        EAL.save_loaded_asset(bp)
        for a in targets():
            c = {x.get_name(): x for x in a.get_components_by_class(unreal.SceneComponent)}
            c["Figure"].set_editor_property("relative_rotation", unreal.Rotator(roll=0, pitch=0, yaw=new_yaw))
        log("figure yaw ->", new_yaw, "; run fit again")
        return
    gmesh = unreal.load_asset(GUN)
    gb = gmesh.get_bounds()
    ext, org = gb.box_extent, gb.origin
    axis = max(("x", "y", "z"), key=lambda k: getattr(ext, k))
    sign = 1.0 if getattr(org, axis) >= 0 else -1.0
    local_yaw = {("x", 1.0): 0.0, ("x", -1.0): 180.0, ("y", 1.0): -90.0, ("y", -1.0): 90.0}.get((axis, sign), 0.0)
    log("gun bounds ext", ext, "origin", org, "long axis", axis, sign)
    world_rot = unreal.MathLibrary.make_rot_from_xz(fwd, V(0, 0, 1))
    local = unreal.Transform(V(0, 0, 0), unreal.Rotator(roll=0, pitch=0, yaw=local_yaw), V(1, 1, 1))
    gun_world = local * unreal.Transform(hand.translation + fwd * 3.0 + V(0, 0, -3.0), world_rot, V(1, 1, 1))
    gun_rel = unreal.MathLibrary.make_relative_transform(gun_world, fig.get_world_transform())
    log("weak point rel", wp_rel, "gun rel", gun_rel.translation, gun_rel.rotation.rotator())
    bp = unreal.load_asset(BP_PATH)
    hs = handles(bp)
    hs["WeakPoint"][1].set_editor_property("relative_location", wp_rel)
    hs["WeakPoint"][1].set_editor_property("relative_scale3d", wp_scale)
    hs["FigureGun"][1].set_editor_property("relative_location", gun_rel.translation)
    hs["FigureGun"][1].set_editor_property("relative_rotation", gun_rel.rotation.rotator())
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    EAL.save_loaded_asset(bp)
    for a in targets():
        if a.get_actor_label() == "C_Target_Drone":
            continue
        c = {x.get_name(): x for x in a.get_components_by_class(unreal.SceneComponent)}
        c["WeakPoint"].set_editor_property("relative_location", wp_rel)
        c["WeakPoint"].set_editor_property("relative_scale3d", wp_scale)
        c["FigureGun"].set_editor_property("relative_location", gun_rel.translation)
        c["FigureGun"].set_editor_property("relative_rotation", gun_rel.rotation.rotator())
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    log("fitted + saved")

try:
    if "fit" in sys.argv:
        fit()
    else:
        build()
except Exception as exc:
    import traceback
    log("ERROR", exc, traceback.format_exc())
finally:
    with open(unreal.Paths.project_saved_dir() + "NV_holo_soldiers.txt", "w", encoding="utf-8") as fh:
        fh.write("\n".join(REPORT))
