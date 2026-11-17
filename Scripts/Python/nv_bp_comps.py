import unreal
SDS = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
BFL = unreal.SubobjectDataBlueprintFunctionLibrary
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
out = []
bp = unreal.load_asset("/Game/NeonVeil/Tests/BP_NVTrainingTarget_Test")
out.append("status before %s" % bp.get_editor_property("status"))
unreal.BlueprintEditorLibrary.compile_blueprint(bp)
out.append("status after %s" % bp.get_editor_property("status"))
a = [x for x in EAS.get_all_level_actors() if x.get_actor_label() == "C_Target_Moving0"][0]
out.append("class %s" % a.get_class().get_path_name())
out.append("instance: " + ", ".join(c.get_name() for c in a.get_components_by_class(unreal.ActorComponent)))
open(unreal.Paths.project_saved_dir() + "NV_bp_comps.txt", "w").write("\n".join(out))
