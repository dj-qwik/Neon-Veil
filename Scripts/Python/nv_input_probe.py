"""Dumps every InputMappingContext under /Game/NeonVeil/Input. Report: Saved/NV_input_probe.txt"""
import unreal
O = []
for p in unreal.EditorAssetLibrary.list_assets("/Game/NeonVeil/Input", True, False):
    a = unreal.load_asset(p)
    if isinstance(a, unreal.InputMappingContext):
        O.append(p)
        for m in a.get_editor_property("default_key_mappings").get_editor_property("mappings") if hasattr(a, "default_key_mappings") else a.get_editor_property("mappings"):
            act = m.get_editor_property("action"); k = m.get_editor_property("key")
            O.append(f"  {act.get_name() if act else None}: {k.get_editor_property('key_name')}")
open(unreal.Paths.project_saved_dir() + "NV_input_probe.txt", "w").write("\n".join(O))
