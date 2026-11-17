"""Hologram targets: rifles use the same hologram material as the bodies (they were on the brighter additive orrery
glow and stood out). Saved/NV_holo_gun_match.txt"""
import unreal
EAL = unreal.EditorAssetLibrary
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
SDS = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
BFL = unreal.SubobjectDataBlueprintFunctionLibrary
out = []
try:
    holo = unreal.load_asset("/Game/NeonVeil/Materials/Holo/M_NV_HoloTarget")
    bp = unreal.load_asset("/Game/NeonVeil/Tests/BP_NVTrainingTarget_Test")
    for h in SDS.k2_gather_subobject_data_for_blueprint(bp):
        o = BFL.get_object(BFL.get_data(h))
        if o and o.get_name().replace("_GEN_VARIABLE", "") == "FigureGun":
            for i in range(o.get_num_materials()):
                o.set_material(i, holo)
            out.append("bp gun slots %d" % o.get_num_materials())
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    EAL.save_loaded_asset(bp, only_if_is_dirty=False)
    for a in EAS.get_all_level_actors():
        if not a.get_actor_label().startswith("C_Target_"):
            continue
        for c in a.get_components_by_class(unreal.SkeletalMeshComponent):
            if c.get_name() == "FigureGun":
                for i in range(c.get_num_materials()):
                    c.set_material(i, holo)
                out.append("%s gun -> holo" % a.get_actor_label())
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    out.append("saved")
except Exception:
    import traceback; out.append(traceback.format_exc())
open(unreal.Paths.project_saved_dir() + "NV_holo_gun_match.txt", "w").write("\n".join(out))
