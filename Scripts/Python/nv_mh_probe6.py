"""Director outfit instance parameters. Report: Saved/NV_mh_probe6.txt"""
import unreal
out = []
ch = unreal.load_asset("/Game/NeonVeil/Characters/Director/MHC_Director")
inst = ch.get_editor_property("internal_collection").get_editor_property("default_instance")
IBL = unreal.MetaHumanCharacterInstanceBlueprintLibrary
paths = IBL.get_instance_parameter_item_paths(inst)
out.append(f"item paths {len(paths)}")
for p in paths:
    out.append(f"== {p}")
    try:
        for prm in IBL.get_instance_parameters(inst, p):
            out.append(f"   {prm}")
    except Exception as e:
        out.append(f"   err {e}")
with open(unreal.Paths.project_saved_dir() + "NV_mh_probe6.txt", "w", encoding="utf-8") as fh:
    fh.write("\n".join(out))
