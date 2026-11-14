"""Holster (unarmed) and first/third-person view inputs: IA_NV_Holster (H, D-pad down) and IA_NV_ToggleView
(B, gamepad View/Share button), mapped in IMC_NV_Combat and assigned on BP_NVPlayerCharacter.
Report: Saved/NV_input_holster_view.txt"""
import unreal
EAL = unreal.EditorAssetLibrary
AT = unreal.AssetToolsHelpers.get_asset_tools()
OUT = []
IN = "/Game/NeonVeil/Input/Actions"
def get_or_create(name):
    path = f"{IN}/{name}"
    a = unreal.load_asset(path) if EAL.does_asset_exist(path) else AT.create_asset(name, IN, unreal.InputAction, unreal.InputAction_Factory())
    a.set_editor_property("value_type", unreal.InputActionValueType.BOOLEAN)
    EAL.save_loaded_asset(a)
    return a
def key(n):
    k = unreal.Key(); k.import_text(n); return k
hol, view = get_or_create("IA_NV_Holster"), get_or_create("IA_NV_ToggleView")
imc = unreal.load_asset("/Game/NeonVeil/Input/IMC_NV_Combat")
# remove our own mappings first so reruns don't duplicate them
for a in (hol, view):
    try:
        imc.unmap_all_keys_from_action(a)
    except Exception as e:
        OUT.append(f"unmap skipped: {e}")
existing = set()
for a, keys in ((hol, ["H", "Gamepad_DPad_Down"]), (view, ["B", "Gamepad_Special_Left"])):
    for k in keys:
        if (a.get_name(), k) not in existing:
            imc.map_key(a, key(k)); OUT.append(f"mapped {a.get_name()} -> {k}")
EAL.save_loaded_asset(imc)
BP = "/Game/NeonVeil/Core/BP_NVPlayerCharacter"
bp = unreal.load_asset(BP)
unreal.BlueprintEditorLibrary.compile_blueprint(bp)
cdo = unreal.get_default_object(EAL.load_blueprint_class(BP))
cdo.set_editor_property("holster_action", hol)
cdo.set_editor_property("toggle_view_action", view)
EAL.save_loaded_asset(bp)
OUT.append(f"cdo holster={cdo.get_editor_property('holster_action')} view={cdo.get_editor_property('toggle_view_action')}")
open(unreal.Paths.project_saved_dir() + "NV_input_holster_view.txt", "w").write("\n".join(OUT))
