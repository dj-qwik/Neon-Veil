"""Put the free MetaOutfits Casual Male outfit on the Director (replaces the default T-shirt/shorts), charcoal tones,
then re-assemble. Report: Saved/NV_mh_outfit_apply.txt"""
import unreal
out = []
def log(*a):
    out.append(" ".join(str(x) for x in a)); unreal.log("[NV outfit] " + out[-1])
MEL = unreal.MaterialEditingLibrary
EAL = unreal.EditorAssetLibrary
TONES = {"Shirt": unreal.LinearColor(0.045, 0.048, 0.054, 1), "Pant": unreal.LinearColor(0.022, 0.023, 0.026, 1),
         "Slippers": unreal.LinearColor(0.015, 0.014, 0.014, 1)}
try:
    for key, col in TONES.items():
        for p in EAL.list_assets("/Game/Outfits/CasualMale", recursive=True):
            if key in p and "/Materials/" in p and p.split(".")[0].split("/")[-1].startswith("MI_"):
                mi = unreal.load_asset(p.split(".")[0])
                if not isinstance(mi, unreal.MaterialInstanceConstant):
                    continue
                names = [str(n) for n in MEL.get_vector_parameter_names(mi)]
                log(mi.get_name(), "vector params", names)
                for n in names:
                    s = n.lower()
                    if any(k in s for k in ("color", "tint", "albedo", "diffuse")) and not any(k in s for k in ("spec", "sheen", "emiss", "subsurface", "fuzz")):
                        MEL.set_material_instance_vector_parameter_value(mi, n, col)
                        log("   set", n)
                EAL.save_loaded_asset(mi, only_if_is_dirty=False)
    S = unreal.get_editor_subsystem(unreal.MetaHumanCharacterEditorSubsystem)
    ch = unreal.load_asset("/Game/NeonVeil/Characters/Director/MHC_Director")
    S.try_add_object_to_edit(ch)
    colx = ch.get_editor_property("internal_collection")
    wi = unreal.load_asset("/Game/Outfits/CasualMale/WI_Casual_M_Outfit")
    k = colx.try_add_item_from_wardrobe_item("Outfits", wi)
    log("added item key", k)
    inst = colx.get_editor_property("default_instance")
    if k is not None:
        inst.set_single_slot_selection("Outfits", k)
        log("selected in Outfits slot")
    EAL.save_loaded_asset(ch, only_if_is_dirty=False)
    log("can build:", S.can_build_meta_human(ch, True))
finally:
    with open(unreal.Paths.project_saved_dir() + "NV_mh_outfit_apply.txt", "w", encoding="utf-8") as fh:
        fh.write("\n".join(out))
