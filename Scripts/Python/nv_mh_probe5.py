"""Probe Director wardrobe instance parameters (garment variants). Report: Saved/NV_mh_probe5.txt"""
import unreal
out = []
ch = unreal.load_asset("/Game/NeonVeil/Characters/Director/MHC_Director")
col = ch.get_editor_property("internal_collection")
out.append(f"collection {col}")
for n in dir(col):
    if not n.startswith("_") and n not in dir(unreal.Object):
        out.append(f"  attr {n}")
try:
    inst = col.get_editor_property("default_instance")
    out.append(f"default_instance {inst}")
    IBL = unreal.MetaHumanCharacterInstanceBlueprintLibrary
    params = IBL.get_instance_parameters(inst)
    out.append(f"params {len(params)}")
    for p in params:
        out.append(f"  {p}")
except Exception as e:
    out.append(f"instance err {e}")
try:
    keys = unreal.MetaHumanCollectionBlueprintLibrary.get_all_item_keys(col)
    for k in keys:
        out.append(f"item {unreal.MetaHumanCollectionBlueprintLibrary.get_item_display_name(col, k)} slot={unreal.MetaHumanCollectionBlueprintLibrary.get_item_slot_name(col, k) if hasattr(unreal.MetaHumanCollectionBlueprintLibrary,'get_item_slot_name') else ''}")
    out.append("slots " + str(unreal.MetaHumanCollectionBlueprintLibrary.get_slot_names(col)))
except Exception as e:
    out.append(f"collection err {e}")
wi = unreal.load_asset("/MetaHumanCharacter/Optional/Clothing/WI_DefaultGarment")
out.append(f"WI {wi}")
for n in dir(wi):
    if not n.startswith("_") and n not in dir(unreal.Object):
        out.append(f"  wi attr {n}")
with open(unreal.Paths.project_saved_dir() + "NV_mh_probe5.txt", "w", encoding="utf-8") as fh:
    fh.write("\n".join(out))
