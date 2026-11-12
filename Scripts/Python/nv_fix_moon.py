import unreal
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for a in EAS.get_all_level_actors():
    if a.get_actor_label() == "MoonKey":
        a.light_component.set_editor_property("forward_shading_priority", 1)
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
