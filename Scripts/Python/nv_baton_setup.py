"""Shock baton as its own weapon slot.
  SM_NV_ShockBaton   - Geometry Script baton along +Z, origin in the middle of the grip: rubber grip, steel collar
                       and shaft, three glowing coil rings and a glowing tip (~51 cm)
  MI_NV_Baton_*      - grip / steel (M_NV_CarPaint) and coil glow (M_NV_Glow)
  DA_Weapon_Baton    - copy of DA_Weapon_VX9 (pistol-grip arms idle/draw), static mesh, bMelee, no ammo/fire/reload
  BP_NVPlayerCharacter StartingWeapons: baton appended last (sim steps address slots 0/1, so they keep their order)
  L_M00_GlassCrown sim: the "Shock baton {Melee}" step now reads "Close quarters {Melee}" (Melee bashes with the gun)
Geometry Script GC hazard: restart the editor afterwards. Report: Saved/NV_baton_setup.txt"""
import unreal
EAL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary
AT = unreal.AssetToolsHelpers.get_asset_tools()
LES = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
GP = unreal.GeometryScript_Primitives
GA = unreal.GeometryScript_AssetUtils
V = unreal.Vector
OUT = []
D = "/Game/NeonVeil/Weapons/Baton"
W = "/Game/NeonVeil/Data/Weapons"


def mi(name, parent, vec, scal):
    path = f"{D}/{name}"
    m = unreal.load_asset(path) if EAL.does_asset_exist(path) else AT.create_asset(name, D, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    MEL.set_material_instance_parent(m, unreal.load_asset(parent))
    for k, v in vec.items():
        MEL.set_material_instance_vector_parameter_value(m, k, unreal.LinearColor(*v, 1))
    for k, v in scal.items():
        MEL.set_material_instance_scalar_parameter_value(m, k, v)
    EAL.save_loaded_asset(m)
    return m


PAINT = "/Game/NeonVeil/Vehicles/M_NV_CarPaint"
GLOW = "/Game/NeonVeil/Materials/Prologue/M_NV_Glow"
MATS = [
    mi("MI_NV_Baton_Grip", PAINT, {"Paint": (0.012, 0.012, 0.014)}, {"Metallic": 0.0, "Roughness": 0.85}),
    mi("MI_NV_Baton_Steel", PAINT, {"Paint": (0.16, 0.17, 0.19)}, {"Metallic": 0.9, "Roughness": 0.32}),
    mi("MI_NV_Baton_Coil", GLOW, {"Color": (0.2, 0.75, 1.0)}, {"Glow": 6.0}),
]
SLOTS = ["Grip", "Steel", "Coil"]

# (material, radius, z0, z1) along +Z; z = 0 is the middle of the grip
PARTS = [
    (1, 1.95, -8.2, -6.8),     # pommel cap
    (0, 1.7, -6.8, 6.8),       # rubber grip
    (1, 2.15, 6.8, 8.0),       # collar
    (1, 1.2, 8.0, 38.5),       # shaft
    (2, 1.42, 24.5, 25.3),     # coil rings
    (2, 1.42, 28.5, 29.3),
    (2, 1.42, 32.5, 33.3),
    (1, 1.55, 38.5, 39.4),     # tip collar
    (2, 1.35, 39.4, 42.6),     # glowing tip
]
# grip ridges
for i in range(5):
    z = -5.0 + i * 2.5
    PARTS.append((0, 1.82, z, z + 0.7))

m = unreal.new_object(unreal.DynamicMesh, name="NV_ShockBaton_Build")
for mat, r, z0, z1 in PARTS:
    o = unreal.GeometryScriptPrimitiveOptions()
    o.set_editor_property("material_id", mat)
    T = unreal.Transform(V(0, 0, z0), unreal.Rotator(), V(1, 1, 1))
    GP.append_cylinder(m, o, T, r, z1 - z0, 16, 0, True, unreal.GeometryScriptPrimitiveOriginMode.BASE)

path = f"{D}/SM_NV_ShockBaton"
if EAL.does_asset_exist(path):
    sm = unreal.load_asset(path)
    GA.copy_mesh_to_static_mesh(m, sm, unreal.GeometryScriptCopyMeshToAssetOptions(), unreal.GeometryScriptMeshWriteLOD())
else:
    opts = unreal.GeometryScriptCreateNewStaticMeshAssetOptions()
    opts.set_editor_property("enable_recompute_normals", True)
    opts.set_editor_property("enable_nanite", False)
    opts.set_editor_property("enable_collision", False)
    fn = None
    for cls in ("GeometryScript_NewAssetUtils", "GeometryScript_CreateNewAsset", "GeometryScript_AssetUtils"):
        c = getattr(unreal, cls, None)
        if c and hasattr(c, "create_new_static_mesh_asset_from_mesh"):
            fn = c.create_new_static_mesh_asset_from_mesh
            break
    res = fn(m, path, opts)
    sm = res[0] if isinstance(res, tuple) else res
mats = []
for mat, slot in zip(MATS, SLOTS):
    s = unreal.StaticMaterial()
    s.set_editor_property("material_interface", mat)
    s.set_editor_property("material_slot_name", slot)
    mats.append(s)
sm.set_editor_property("static_materials", mats)
EAL.save_loaded_asset(sm)
b = sm.get_bounding_box()
OUT.append(f"baton mesh {path}: {b.min} {b.max}")

# ---- weapon data
dpath = f"{W}/DA_Weapon_Baton"
if not EAL.does_asset_exist(dpath):
    EAL.duplicate_asset(f"{W}/DA_Weapon_VX9", dpath)
d = unreal.load_asset(dpath)
sets = {
    "display_name": unreal.Text("Shock Baton"),
    "melee": True,
    "weapon_mesh": None,
    "weapon_static_mesh": sm,
    "magazine_size": 0,
    "starting_reserve_ammo": 0,
    "weapon_fire_anim": None,
    "weapon_reload_anim": None,
    "arms_fire_anim": None,
    "arms_reload_anim": None,
    "scope_overlay": False,
    "hold_type": unreal.NVWeaponHold.PISTOL,
    # rest pose: hand low on the right, just above the waist; tip pointing forward and out, away from the body
    "viewmodel_hip_offset": V(12.0, 9.0, 12.0),
    "arms_weapon_offset": unreal.Transform(V(0.0, 2.0, -11.0), unreal.Rotator(roll=68.0, pitch=15.0, yaw=0.0), V(1, 1, 1)),
}
for k, v in sets.items():
    try:
        d.set_editor_property(k, v)
    except Exception as e:
        OUT.append(f"  set fail {k}: {e}")
# soft refs copied from the VX9 sometimes survive the first None; clear again and check
for k in ("weapon_mesh", "weapon_fire_anim", "weapon_reload_anim", "arms_fire_anim", "arms_reload_anim"):
    if d.get_editor_property(k):
        d.set_editor_property(k, None)
    OUT.append(f"  {k}: {d.get_editor_property(k)}")
EAL.save_loaded_asset(d, only_if_is_dirty=False)
OUT.append(f"{dpath}: melee={d.get_editor_property('melee')} static={d.get_editor_property('weapon_static_mesh')}")

# ---- loadout
bp_path = "/Game/NeonVeil/Core/BP_NVPlayerCharacter"
bp = unreal.load_asset(bp_path)
cdo = unreal.get_default_object(EAL.load_blueprint_class(bp_path))
wc = cdo.get_editor_property("weapons")
start = list(wc.get_editor_property("starting_weapons"))
if not any(x and x.get_name() == "DA_Weapon_Baton" for x in start):
    start.append(d)
    wc.set_editor_property("starting_weapons", start)
    EAL.save_loaded_asset(bp, only_if_is_dirty=False)
OUT.append("starting weapons: " + ", ".join(x.get_name() for x in start if x))

# ---- sim step wording (GlassCrown), then back to the prologue
cur = unreal.EditorLevelLibrary.get_editor_world().get_path_name()
LES.load_level("/Game/NeonVeil/Maps/M00/L_M00_GlassCrown")
for a in EAS.get_all_level_actors():
    if isinstance(a, unreal.NVSimulationDirector):
        steps = list(a.get_editor_property("steps"))
        n = 0
        for s in steps:
            t = str(s.get_editor_property("instruction"))
            if t.startswith("Shock baton"):
                s.set_editor_property("instruction", unreal.Text("Close quarters {Melee}: strike, then strike again while it staggers"))
                n += 1
        if n:
            a.set_editor_property("steps", steps)
            LES.save_current_level()
        OUT.append(f"sim steps reworded: {n}")
LES.load_level("/Game/NeonVeil/Maps/M00/L_M00_Prologue")
OUT.append("was on " + cur)
open(unreal.Paths.project_saved_dir() + "NV_baton_setup.txt", "w").write("\n".join(OUT))
del m
