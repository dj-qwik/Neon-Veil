"""NEON VEIL - Milestone 3a editor setup: cyberware abilities + shock baton input.

Creates or updates:
  /Game/NeonVeil/Input/Actions      IA_NV_Melee, IA_NV_Ability1..3 (added to IMC_NV_Combat)
  /Game/NeonVeil/Data/Abilities     DA_Ability_OpticalDisruption, DA_Ability_KineticShield, DA_Ability_DroneUplink
  /Game/NeonVeil/Core               BP_NVPlayerCharacter: new input actions + ability slots

Bindings: Melee V / R3. Abilities Q / D-pad Left, G / D-pad Right, T / D-pad Up.
Safe to re-run: existing mappings are not duplicated.
"""
import unreal

REPORT = []
def log(*a):
    msg = " ".join(str(x) for x in a)
    REPORT.append(msg)
    unreal.log("[NV M3a] " + msg)

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

# ------------------------------------------------------------------ input
IN = "/Game/NeonVeil/Input/Actions"
ia = {}
for n in ["IA_NV_Melee", "IA_NV_Ability1", "IA_NV_Ability2", "IA_NV_Ability3"]:
    a = get_or_create(n, IN, unreal.InputAction, unreal.InputAction_Factory())
    a.set_editor_property("value_type", unreal.InputActionValueType.BOOLEAN)
    EAL.save_loaded_asset(a)
    ia[n] = a

imc = unreal.load_asset("/Game/NeonVeil/Input/IMC_NV_Combat")
def imc_mappings(imc):
    # UE 5.8 keeps the default mappings in DefaultKeyMappings.Mappings; older builds in Mappings.
    try:
        return list(imc.get_editor_property("default_key_mappings").get_editor_property("mappings"))
    except Exception:
        return list(imc.get_editor_property("mappings"))
existing = set()
for m in imc_mappings(imc):
    act = m.get_editor_property("action")
    existing.add((act.get_name() if act else "", m.get_editor_property("key").get_editor_property("key_name")))
BINDINGS = [
    ("IA_NV_Melee", ["V", "Gamepad_RightThumbstick"]),
    ("IA_NV_Ability1", ["Q", "Gamepad_DPad_Left"]),
    ("IA_NV_Ability2", ["G", "Gamepad_DPad_Right"]),
    ("IA_NV_Ability3", ["T", "Gamepad_DPad_Up"]),
]
imc.modify()  # mark the package dirty so the save below actually writes it
added = 0
for action_name, keys in BINDINGS:
    for k in keys:
        if (action_name, k) in existing:
            continue
        imc.map_key(ia[action_name], key(k))
        added += 1
saved = EAL.save_loaded_asset(imc, only_if_is_dirty=False)
log("IMC_NV_Combat saved:", saved)
log("IMC_NV_Combat: added", added, "mappings; total", len(imc_mappings(imc)))

# ------------------------------------------------------------------ ability data (Bible §9: all available in M00)
DATA = "/Game/NeonVeil/Data/Abilities"
f = unreal.DataAssetFactory()
f.set_editor_property("data_asset_class", unreal.NVAbilityData)
ABILITIES = [
    ("DA_Ability_OpticalDisruption", dict(
        ability_tag=tag("NV.Ability.OpticalDisruption"), display_name=unreal.Text("Optical Disruption"),
        short_label=unreal.Text("OD"), duration=6.0, cooldown=12.0, breaks_on_attack=True)),
    ("DA_Ability_KineticShield", dict(
        ability_tag=tag("NV.Ability.KineticShield"), display_name=unreal.Text("Kinetic Shield"),
        short_label=unreal.Text("KS"), duration=4.0, cooldown=10.0, damage_reduction=1.0)),
    ("DA_Ability_DroneUplink", dict(
        ability_tag=tag("NV.Ability.DroneUplink"), display_name=unreal.Text("Drone Uplink"),
        short_label=unreal.Text("DU"), duration=8.0, cooldown=14.0, drone_range=2500.0, scan_radius=1500.0, mark_duration=12.0)),
]
assets = []
for name, props in ABILITIES:
    path = f"{DATA}/{name}"
    if EAL.does_asset_exist(path):
        d = unreal.load_asset(path)
    else:
        ensure_dir(DATA)
        d = AT.create_asset(name, DATA, unreal.NVAbilityData, f)
        log("created", path)
    for k, v in props.items():
        # bBreaksOnAttack is exposed to Python without the b prefix
        d.set_editor_property(k, v)
    EAL.save_loaded_asset(d, only_if_is_dirty=False)
    assets.append(d)

# ------------------------------------------------------------------ player blueprint
PATH = "/Game/NeonVeil/Core/BP_NVPlayerCharacter"
pbp = unreal.load_asset(PATH)
unreal.BlueprintEditorLibrary.compile_blueprint(pbp)
pcls = EAL.load_blueprint_class(PATH)
pcdo = unreal.get_default_object(pcls)
pcdo.set_editor_property("melee_action", ia["IA_NV_Melee"])
pcdo.set_editor_property("ability1_action", ia["IA_NV_Ability1"])
pcdo.set_editor_property("ability2_action", ia["IA_NV_Ability2"])
pcdo.set_editor_property("ability3_action", ia["IA_NV_Ability3"])
abil = pcdo.get_editor_property("abilities")
abil.set_editor_property("abilities", assets)
baton = pcdo.get_editor_property("baton_mesh")
gun_mat = unreal.load_asset("/Game/NeonVeil/Tests/Materials/TEMP_M_Gunmetal")
if gun_mat:
    baton.set_material(0, gun_mat)
EAL.save_loaded_asset(pbp, only_if_is_dirty=False)
log("BP_NVPlayerCharacter: abilities", [a.get_name() for a in abil.get_editor_property("abilities")])

with open(unreal.Paths.project_saved_dir() + "NV_setup_m3a.txt", "w", encoding="utf-8") as fh:
    fh.write("\n".join(REPORT))
