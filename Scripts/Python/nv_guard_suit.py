"""Guard body slots (arms/torso skin of the sleeveless merc) -> dark carbon compression undersuit.
Keeps the pack's normal map (form/folds) but replaces the skin albedo with flat black and drops the tint masks."""
import unreal

eat = unreal.EditorAssetLibrary
mel = unreal.MaterialEditingLibrary
out = []
BLACK = unreal.load_asset("/Engine/EngineResources/Black")
for name in ["MI_NV_Guard_Body", "MI_NV_Guard_Body_Toptank"]:
    mi = unreal.load_asset("/Game/NeonVeil/Characters/Guard/" + name)
    before = {str(t): mel.get_material_instance_texture_parameter_value(mi, t) for t in mel.get_texture_parameter_names(mi)}
    out.append("%s before %s" % (name, {k: (v.get_name() if v else None) for k, v in before.items()}))
    if name == "MI_NV_Guard_Body":
        mel.set_material_instance_texture_parameter_value(mi, "BaseColor", BLACK)
        mel.set_material_instance_texture_parameter_value(mi, "IDmask_01", BLACK)
        mel.set_material_instance_texture_parameter_value(mi, "IDmask_02", BLACK)
    eat.save_loaded_asset(mi)
open(unreal.Paths.project_saved_dir() + "NV_nv_guard_suit.txt", "w").write("\n".join(out))
