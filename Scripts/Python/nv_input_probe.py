"""Report IMC_NV_Combat mappings for holster/view and the player CDO input slots. Report: Saved/NV_input_probe.txt"""
import unreal
OUT = []
imc = unreal.load_asset("/Game/NeonVeil/Input/IMC_NV_Combat")
for m in imc.get_editor_property("default_key_mappings").get_editor_property("mappings") if hasattr(imc, "get_editor_property") else []:
    pass
try:
    maps = imc.get_editor_property("default_key_mappings").get_editor_property("mappings")
except Exception as e:
    try:
        maps = imc.get_editor_property("mappings")
    except Exception as e2:
        maps = []; OUT.append(f"no mappings prop: {e} / {e2}")
for m in maps:
    a = m.get_editor_property("action")
    k = m.get_editor_property("key")
    OUT.append(f"{a.get_name() if a else None} -> {k.export_text() if hasattr(k,'export_text') else k}")
cdo = unreal.get_default_object(unreal.EditorAssetLibrary.load_blueprint_class("/Game/NeonVeil/Core/BP_NVPlayerCharacter"))
for p in ("holster_action", "toggle_view_action", "ability1_action"):
    OUT.append(f"cdo {p} = {cdo.get_editor_property(p)}")
open(unreal.Paths.project_saved_dir() + "NV_input_probe.txt", "w").write("\n".join(OUT))
