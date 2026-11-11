"""NEON VEIL - Milestone 1 editor setup (combat core test range).

Creates (or updates, if they already exist):
  /Game/NeonVeil/Input          IA_NV_* actions + IMC_NV_Combat
  /Game/NeonVeil/Data/Weapons   DA_Weapon_VX9, DA_Weapon_Kestrel, DA_Weapon_Harrow
  /Game/NeonVeil/Data/Missions  DA_Mission_Test_CombatCore
  /Game/NeonVeil/Core           BP_NVPlayerCharacter, BP_NVGameMode
  /Game/NeonVeil/Tests          TEMP_ materials, BP_NVTrainingTarget_Test, BP_NVTerminal_Test
  /Game/NeonVeil/Maps/Tests     L_Test_CombatCore

Everything visual made here is TEMP (prefixed TEMP_) and is replaced in the art milestones.
Writes a report to Saved/NV_setup_m1.txt.
"""
import unreal

REPORT = []
def log(*a):
    msg = " ".join(str(x) for x in a)
    REPORT.append(msg)
    unreal.log("[NV M1] " + msg)

AT = unreal.AssetToolsHelpers.get_asset_tools()
EAL = unreal.EditorAssetLibrary

def ensure_dir(path):
    if not EAL.does_directory_exist(path):
        EAL.make_directory(path)

def get_or_create(name, folder, asset_class, factory):
    path = f"{folder}/{name}"
    if EAL.does_asset_exist(path):
        return unreal.load_asset(path)
    ensure_dir(folder)
    asset = AT.create_asset(name, folder, asset_class, factory)
    log("created", path)
    return asset

def key(name):
    k = unreal.Key()
    k.import_text(name)
    return k

def tag(name):
    t = unreal.GameplayTag()
    t.import_text(f'(TagName="{name}")')
    return t

def text(s):
    return unreal.Text(s)

# ------------------------------------------------------------------ input
IN = "/Game/NeonVeil/Input/Actions"
ACTIONS = {
    "IA_NV_Sprint": unreal.InputActionValueType.BOOLEAN,
    "IA_NV_Crouch": unreal.InputActionValueType.BOOLEAN,
    "IA_NV_Fire": unreal.InputActionValueType.BOOLEAN,
    "IA_NV_Aim": unreal.InputActionValueType.BOOLEAN,
    "IA_NV_Reload": unreal.InputActionValueType.BOOLEAN,
    "IA_NV_Interact": unreal.InputActionValueType.BOOLEAN,
    "IA_NV_NextWeapon": unreal.InputActionValueType.BOOLEAN,
    "IA_NV_PrevWeapon": unreal.InputActionValueType.BOOLEAN,
}
ia = {}
for n, vt in ACTIONS.items():
    a = get_or_create(n, IN, unreal.InputAction, unreal.InputAction_Factory())
    a.set_editor_property("value_type", vt)
    EAL.save_loaded_asset(a)
    ia[n] = a

imc = get_or_create("IMC_NV_Combat", "/Game/NeonVeil/Input", unreal.InputMappingContext, unreal.InputMappingContext_Factory())
imc.unmap_all()
BINDINGS = [
    ("IA_NV_Sprint", ["LeftShift", "Gamepad_LeftThumbstick"]),
    ("IA_NV_Crouch", ["LeftControl", "C", "Gamepad_FaceButton_Right"]),
    ("IA_NV_Fire", ["LeftMouseButton", "Gamepad_RightTrigger"]),
    ("IA_NV_Aim", ["RightMouseButton", "Gamepad_LeftTrigger"]),
    ("IA_NV_Reload", ["R", "Gamepad_FaceButton_Left"]),
    ("IA_NV_Interact", ["E", "F", "Gamepad_FaceButton_Top"]),
    ("IA_NV_NextWeapon", ["MouseScrollUp", "Gamepad_RightShoulder"]),
    ("IA_NV_PrevWeapon", ["MouseScrollDown", "Gamepad_LeftShoulder"]),
]
for action_name, keys in BINDINGS:
    for k in keys:
        imc.map_key(ia[action_name], key(k))
EAL.save_loaded_asset(imc)
log("IMC_NV_Combat mappings:", sum(len(k) for _, k in BINDINGS))

# ------------------------------------------------------------------ TEMP materials
MAT = "/Game/NeonVeil/Tests/Materials"
MEL = unreal.MaterialEditingLibrary

def make_material(name, base, emissive, roughness=0.4, metallic=0.0):
    path = f"{MAT}/{name}"
    if EAL.does_asset_exist(path):
        return unreal.load_asset(path)
    m = get_or_create(name, MAT, unreal.Material, unreal.MaterialFactoryNew())
    bc = MEL.create_material_expression(m, unreal.MaterialExpressionConstant3Vector, -400, 0)
    bc.set_editor_property("constant", unreal.LinearColor(*base, 1))
    MEL.connect_material_property(bc, "", unreal.MaterialProperty.MP_BASE_COLOR)
    if emissive:
        em = MEL.create_material_expression(m, unreal.MaterialExpressionConstant3Vector, -400, 200)
        em.set_editor_property("constant", unreal.LinearColor(*emissive, 1))
        MEL.connect_material_property(em, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    r = MEL.create_material_expression(m, unreal.MaterialExpressionConstant, -400, 400)
    r.set_editor_property("r", roughness)
    MEL.connect_material_property(r, "", unreal.MaterialProperty.MP_ROUGHNESS)
    mt = MEL.create_material_expression(m, unreal.MaterialExpressionConstant, -400, 500)
    mt.set_editor_property("r", metallic)
    MEL.connect_material_property(mt, "", unreal.MaterialProperty.MP_METALLIC)
    MEL.recompile_material(m)
    EAL.save_loaded_asset(m)
    return m

m_holo = make_material("TEMP_M_HoloTarget", (0.02, 0.05, 0.06), (0.4, 2.2, 3.0), 0.3)
m_weak = make_material("TEMP_M_WeakPoint", (0.1, 0.05, 0.0), (6.0, 2.4, 0.3), 0.3)
m_shield = make_material("TEMP_M_Shield", (0.05, 0.08, 0.12), (0.6, 0.9, 2.0), 0.1)
m_gun = make_material("TEMP_M_Gunmetal", (0.03, 0.03, 0.035), None, 0.35, 1.0)
m_terminal = make_material("TEMP_M_Terminal", (0.05, 0.05, 0.06), (0.2, 1.0, 1.4), 0.25, 0.5)

CUBE = unreal.load_asset("/Engine/BasicShapes/Cube")
CYL = unreal.load_asset("/Engine/BasicShapes/Cylinder")
SPHERE = unreal.load_asset("/Engine/BasicShapes/Sphere")
PLANE = unreal.load_asset("/Engine/BasicShapes/Plane")

# ------------------------------------------------------------------ weapons
WD = "/Game/NeonVeil/Data/Weapons"
def weapon(name, **props):
    f = unreal.DataAssetFactory()
    f.set_editor_property("data_asset_class", unreal.NVWeaponData)
    w = get_or_create(name, WD, unreal.NVWeaponData, f)
    for k, v in props.items():
        w.set_editor_property(k, v)
    EAL.save_loaded_asset(w)
    return w

# Values follow Bible §7; tuning targets, not final balance.
vx9 = weapon("DA_Weapon_VX9",
    display_name=text("VX-9 Service Pistol"), damage=24.0, damage_type=tag("NV.Damage.Training"),
    fire_mode=unreal.NVFireMode.SEMI_AUTO, rounds_per_minute=420.0, magazine_size=12, starting_reserve_ammo=48,
    reload_time=1.45, hip_spread_deg=1.1, ads_spread_deg=0.15, spread_per_shot_deg=0.35, max_bloom_deg=2.2,
    recoil_pitch=0.9, recoil_yaw_random=0.25, ads_time=0.17, ads_fov=78.0, ads_sensitivity_scale=0.8,
    weapon_static_mesh=CUBE, viewmodel_scale=unreal.Vector(0.18, 0.03, 0.06),
    viewmodel_hip_offset=unreal.Vector(48, 14, -15), viewmodel_ads_offset=unreal.Vector(38, 0, -6.6))
kestrel = weapon("DA_Weapon_Kestrel",
    display_name=text("Kestrel SMG"), damage=14.0, damage_type=tag("NV.Damage.Training"),
    fire_mode=unreal.NVFireMode.FULL_AUTO, rounds_per_minute=850.0, magazine_size=30, starting_reserve_ammo=120,
    reload_time=2.1, hip_spread_deg=2.0, ads_spread_deg=0.45, spread_per_shot_deg=0.18, max_bloom_deg=3.5,
    recoil_pitch=0.55, recoil_yaw_random=0.35, recoil_recovery_fraction=0.45, ads_time=0.21, ads_fov=72.0,
    ads_sensitivity_scale=0.75, ads_move_speed_scale=0.65,
    weapon_static_mesh=CUBE, viewmodel_scale=unreal.Vector(0.34, 0.04, 0.075),
    viewmodel_hip_offset=unreal.Vector(55, 15, -17), viewmodel_ads_offset=unreal.Vector(42, 0, -7.6))
harrow = weapon("DA_Weapon_Harrow",
    display_name=text("Harrow Precision Rifle"), damage=70.0, weak_point_bonus=1.5, damage_type=tag("NV.Damage.Ballistic"),
    fire_mode=unreal.NVFireMode.SEMI_AUTO, rounds_per_minute=70.0, magazine_size=8, starting_reserve_ammo=24,
    reload_time=2.6, hip_spread_deg=3.0, ads_spread_deg=0.02, recoil_pitch=2.6, ads_time=0.25, ads_fov=40.0,
    ads_sensitivity_scale=0.45, ads_move_speed_scale=0.5,
    weapon_static_mesh=CUBE, viewmodel_scale=unreal.Vector(0.6, 0.04, 0.08),
    viewmodel_hip_offset=unreal.Vector(60, 15, -17), viewmodel_ads_offset=unreal.Vector(45, 0, -7.8))
for w in (vx9, kestrel, harrow):
    log("weapon", w.get_name(), "mag", w.get_editor_property("magazine_size"))

# ------------------------------------------------------------------ mission (test)
MD = "/Game/NeonVeil/Data/Missions"
f = unreal.DataAssetFactory()
f.set_editor_property("data_asset_class", unreal.NVMissionData)
mission = get_or_create("DA_Mission_Test_CombatCore", MD, unreal.NVMissionData, f)
o1 = unreal.NVObjectiveDef()
o1.set_editor_property("objective_id", "TEST-O01")
o1.set_editor_property("display_text", text("Run combat suite diagnostics"))
o1.set_editor_property("completion_event_tag", tag("NV.Event.M00.CalibrationComplete"))
o2 = unreal.NVObjectiveDef()
o2.set_editor_property("objective_id", "TEST-O02")
o2.set_editor_property("display_text", text("Review the range report"))
o2.set_editor_property("prerequisites", ["TEST-O01"])
o2.set_editor_property("completion_event_tag", tag("NV.Event.M00.HoloTableReviewed"))
mission.set_editor_property("mission_id", "TEST")
mission.set_editor_property("mission_title", text("Combat core test"))
mission.set_editor_property("objectives", [o1, o2])
EAL.save_loaded_asset(mission)

# ------------------------------------------------------------------ blueprints
def make_bp(name, folder, parent):
    path = f"{folder}/{name}"
    if EAL.does_asset_exist(path):
        bp = unreal.load_asset(path)
    else:
        bf = unreal.BlueprintFactory()
        bf.set_editor_property("parent_class", parent)
        ensure_dir(folder)
        bp = AT.create_asset(name, folder, unreal.Blueprint, bf)
        log("created", path)
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    cls = unreal.EditorAssetLibrary.load_blueprint_class(path)
    return bp, cls, unreal.get_default_object(cls)

CORE = "/Game/NeonVeil/Core"
pbp, pcls, pcdo = make_bp("BP_NVPlayerCharacter", CORE, unreal.NVPlayerCharacter)
pcdo.set_editor_property("mapping_contexts", [
    imc,
    unreal.load_asset("/Game/Input/IMC_Default"),
    unreal.load_asset("/Game/Input/IMC_MouseLook"),
])
pcdo.set_editor_property("move_action", unreal.load_asset("/Game/Input/Actions/IA_Move"))
pcdo.set_editor_property("look_action", unreal.load_asset("/Game/Input/Actions/IA_Look"))
pcdo.set_editor_property("mouse_look_action", unreal.load_asset("/Game/Input/Actions/IA_MouseLook"))
pcdo.set_editor_property("jump_action", unreal.load_asset("/Game/Input/Actions/IA_Jump"))
pcdo.set_editor_property("sprint_action", ia["IA_NV_Sprint"])
pcdo.set_editor_property("crouch_action", ia["IA_NV_Crouch"])
pcdo.set_editor_property("fire_action", ia["IA_NV_Fire"])
pcdo.set_editor_property("aim_action", ia["IA_NV_Aim"])
pcdo.set_editor_property("reload_action", ia["IA_NV_Reload"])
pcdo.set_editor_property("interact_action", ia["IA_NV_Interact"])
pcdo.set_editor_property("next_weapon_action", ia["IA_NV_NextWeapon"])
pcdo.set_editor_property("prev_weapon_action", ia["IA_NV_PrevWeapon"])
pcdo.set_editor_property("body_mesh_asset", unreal.load_asset("/Game/Characters/Mannequins/Meshes/SKM_Manny_Simple"))
pcdo.set_editor_property("body_anim_class", unreal.load_object(None, "/Game/Characters/Mannequins/Anims/Unarmed/ABP_Unarmed.ABP_Unarmed_C"))
weapons_comp = pcdo.get_editor_property("weapons")
weapons_comp.set_editor_property("starting_weapons", [vx9, kestrel])
static_vm = pcdo.get_editor_property("weapon_static_mesh")
static_vm.set_material(0, m_gun)
EAL.save_loaded_asset(pbp)
log("BP_NVPlayerCharacter configured; starting weapons:", [w.get_name() for w in weapons_comp.get_editor_property("starting_weapons")])

gbp, gcls, gcdo = make_bp("BP_NVGameMode", CORE, unreal.NVGameMode)
gcdo.set_editor_property("default_pawn_class", pcls)
gcdo.set_editor_property("mission", mission)
EAL.save_loaded_asset(gbp)
log("BP_NVGameMode configured")

TESTS = "/Game/NeonVeil/Tests"
tbp, tcls, tcdo = make_bp("BP_NVTrainingTarget_Test", TESTS, unreal.NVTrainingTarget)
body = tcdo.get_editor_property("body")
body.set_static_mesh(CYL)
body.set_editor_property("relative_scale3d", unreal.Vector(0.45, 0.45, 1.6))
body.set_editor_property("relative_location", unreal.Vector(0, 0, 80))
body.set_material(0, m_holo)
weak = tcdo.get_editor_property("weak_point")
weak.set_static_mesh(SPHERE)
weak.set_editor_property("relative_scale3d", unreal.Vector(0.55, 0.55, 0.14))
weak.set_editor_property("relative_location", unreal.Vector(0, 0, 58))
weak.set_material(0, m_weak)
shield = tcdo.get_editor_property("shield_mesh")
shield.set_static_mesh(CYL)
shield.set_editor_property("relative_scale3d", unreal.Vector(1.35, 1.35, 1.15))
shield.set_material(0, m_shield)
EAL.save_loaded_asset(tbp)

ibp, icls, icdo = make_bp("BP_NVTerminal_Test", TESTS, unreal.NVInteractableActor)
mesh = icdo.get_editor_property("mesh")
mesh.set_static_mesh(CUBE)
mesh.set_editor_property("relative_scale3d", unreal.Vector(0.5, 0.8, 1.1))
mesh.set_material(0, m_terminal)
EAL.save_loaded_asset(ibp)

# ------------------------------------------------------------------ test map
MAP = "/Game/NeonVeil/Maps/Tests/L_Test_CombatCore"
LES = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
ensure_dir("/Game/NeonVeil/Maps/Tests")
if EAL.does_asset_exist(MAP):
    LES.load_level(MAP)
    for a in EAS.get_all_level_actors():
        if a.get_actor_label().startswith("NV_"):
            EAS.destroy_actor(a)
else:
    LES.new_level(MAP)

def spawn(cls, label, loc, rot=(0, 0, 0)):
    # rot is (pitch, yaw, roll). unreal.Rotator's positional order is (roll, pitch, yaw), so name them.
    a = EAS.spawn_actor_from_class(cls, unreal.Vector(*loc), unreal.Rotator(pitch=rot[0], yaw=rot[1], roll=rot[2]))
    a.set_actor_label(label)
    return a

def spawn_mesh(label, mesh, loc, scale, mat=None, rot=(0, 0, 0)):
    a = spawn(unreal.StaticMeshActor, label, loc, rot)
    c = a.static_mesh_component
    c.set_static_mesh(mesh)
    a.set_actor_scale3d(unreal.Vector(*scale))
    if mat:
        c.set_material(0, mat)
    return a

floor_mat = unreal.load_asset("/Game/LevelPrototyping/Materials/MI_PrototypeGrid_Gray")
wall_mat = unreal.load_asset("/Game/LevelPrototyping/Materials/MI_PrototypeGrid_TopDark")
spawn_mesh("NV_Floor", CUBE, (1500, 0, -50), (40, 24, 1), floor_mat)
spawn_mesh("NV_Wall_Back", CUBE, (3500, 0, 300), (1, 24, 7), wall_mat)
spawn_mesh("NV_Wall_L", CUBE, (1500, -1200, 300), (40, 1, 7), wall_mat)
spawn_mesh("NV_Wall_R", CUBE, (1500, 1200, 300), (40, 1, 7), wall_mat)
# Cover blocks at vault heights (0.6, 0.9, 1.2 m) and one too-high block (1.6 m)
spawn_mesh("NV_Cover_60", CUBE, (700, -400, 30), (0.6, 2.0, 0.6), wall_mat)
spawn_mesh("NV_Cover_90", CUBE, (700, 0, 45), (0.6, 2.0, 0.9), wall_mat)
spawn_mesh("NV_Cover_120", CUBE, (700, 400, 60), (0.6, 2.0, 1.2), wall_mat)
spawn_mesh("NV_Cover_160", CUBE, (700, 800, 80), (0.6, 2.0, 1.6), wall_mat)
# Upper catwalk + ramp for traversal checks
spawn_mesh("NV_Catwalk", CUBE, (2300, -900, 250), (12, 3, 0.2), wall_mat)
spawn_mesh("NV_Ramp", CUBE, (1500, -900, 120), (6, 3, 0.2), wall_mat, (0, 0, 0))
EAS.get_all_level_actors()

ps = spawn(unreal.PlayerStart, "NV_PlayerStart", (0, 0, 100))
sun = spawn(unreal.DirectionalLight, "NV_Sun", (0, 0, 800), (-42, 35, 0))
sun.light_component.set_intensity(8.0)
sun.light_component.set_editor_property("atmosphere_sun_light", True)
spawn(unreal.SkyLight, "NV_SkyLight", (0, 0, 900)).light_component.set_editor_property("real_time_capture", True)
spawn(unreal.SkyAtmosphere, "NV_SkyAtmosphere", (0, 0, 0))
spawn(unreal.ExponentialHeightFog, "NV_Fog", (0, 0, 0))
ppv = spawn(unreal.PostProcessVolume, "NV_PostProcess", (0, 0, 0))
ppv.set_editor_property("unbound", True)

# Targets: 2 static, 2 moving, 1 shielded
TARGETS = [
    ("NV_Target_Static_A", (2200, -300, 0), None, 0.0),
    ("NV_Target_Static_B", (2200, 300, 0), None, 0.0),
    ("NV_Target_Moving_A", (2800, -800, 0), (0, -900, 0), 0.0),
    ("NV_Target_Moving_B", (3100, 800, 0), (0, 900, 0), 0.0),
    ("NV_Target_Shielded", (2600, 0, 0), None, 60.0),
]
for label, loc, patrol, shield_hp in TARGETS:
    t = spawn(tcls, label, loc, (0, 180, 0))
    t.set_editor_property("start_active", True)
    if patrol:
        t.set_editor_property("patrol_offset", unreal.Vector(*patrol))
    h = t.get_editor_property("health")
    h.set_editor_property("max_shield", shield_hp)

term1 = spawn(icls, "NV_Terminal_Diagnostics", (400, -700, 55), (0, 90, 0))
term1.set_editor_property("prompt", text("Run diagnostics"))
term1.set_editor_property("hold_duration", 0.8)
term1.set_editor_property("completion_event_tag", tag("NV.Event.M00.CalibrationComplete"))
term2 = spawn(icls, "NV_Terminal_Report", (400, 700, 55), (0, -90, 0))
term2.set_editor_property("prompt", text("Review range report"))
term2.set_editor_property("completion_event_tag", tag("NV.Event.M00.HoloTableReviewed"))

world = unreal.EditorLevelLibrary.get_editor_world()
world.get_world_settings().set_editor_property("default_game_mode", gcls)
LES.save_current_level()
log("map saved", MAP, "actors:", len(EAS.get_all_level_actors()))

with open(unreal.Paths.project_saved_dir() + "NV_setup_m1.txt", "w", encoding="utf-8") as fh:
    fh.write("\n".join(REPORT))
log("done")
