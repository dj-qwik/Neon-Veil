"""Orrery rings: use the pack's hologram material (its sprite sheet masks the planet cards to circles) tinted cyan,
instead of the flat additive glow that lit each planet card up as a square. Saved/NV_orrery_rings_mi.txt"""
import unreal
EAL = unreal.EditorAssetLibrary
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
MEL = unreal.MaterialEditingLibrary
SDS = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
BFL = unreal.SubobjectDataBlueprintFunctionLibrary
out = []
try:
    path = "/Game/NeonVeil/Materials/Holo/MI_NV_OrreryPlanets"
    if EAL.does_asset_exist(path):
        mi = unreal.load_asset(path)
    else:
        mi = unreal.AssetToolsHelpers.get_asset_tools().create_asset("MI_NV_OrreryPlanets", "/Game/NeonVeil/Materials/Holo",
                                                                     unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    MEL.set_material_instance_parent(mi, unreal.load_asset("/Game/ModularScifiInterior/Materials/Parents/M_Hologram"))
    MEL.set_material_instance_scalar_parameter_value(mi, "Intensity", 30.0)
    MEL.set_material_instance_scalar_parameter_value(mi, "OpacityScale", 4.92)
    MEL.set_material_instance_vector_parameter_value(mi, "Color 1", unreal.LinearColor(0.08, 0.75, 1.0, 1.0))
    MEL.set_material_instance_vector_parameter_value(mi, "Color 3", unreal.LinearColor(0.0, 0.3, 1.0, 1.0))
    MEL.update_material_instance(mi)
    EAL.save_loaded_asset(mi, only_if_is_dirty=False)
    bp = unreal.load_asset("/Game/NeonVeil/Props/GlassCrown/BP_NV_CrownOrrery")
    for h in SDS.k2_gather_subobject_data_for_blueprint(bp):
        o = BFL.get_object(BFL.get_data(h))
        if o and o.get_name().replace("_GEN_VARIABLE", "").startswith("Ring"):
            o.set_material(0, mi)
            out.append("bp " + o.get_name())
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    EAL.save_loaded_asset(bp, only_if_is_dirty=False)
    orr = next(a for a in EAS.get_all_level_actors() if a.get_actor_label() == "B_Orrery")
    for c in orr.get_components_by_class(unreal.StaticMeshComponent):
        if c.get_name().startswith("Ring"):
            c.set_material(0, mi)
            out.append("level " + c.get_name())
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    out.append("saved")
except Exception:
    import traceback; out.append(traceback.format_exc())
open(unreal.Paths.project_saved_dir() + "NV_orrery_rings_mi.txt", "w").write("\n".join(out))
