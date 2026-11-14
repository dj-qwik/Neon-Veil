"""Temporarily hide/show actors by exact label in the editor (not saved). Args: 0|1 label [label...]"""
import unreal, sys
show = sys.argv[2] == "1"
labels = set(sys.argv[3:])
for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
    if a.get_actor_label() in labels:
        a.set_is_temporarily_hidden_in_editor(not show)
        for c in a.get_components_by_class(unreal.LightComponent):
            c.set_visibility(show)
