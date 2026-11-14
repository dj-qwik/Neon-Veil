"""PIE: hide bones on an NPC's MetaHuman body. argv[2] = 'Label bone1,bone2,...'"""
import sys, unreal
UES = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
w = UES.get_game_world()
lab, bones = sys.argv[2].split()
for a in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.Character):
    if a.get_actor_label().startswith(lab):
        for cc in a.get_components_by_class(unreal.ChildActorComponent):
            ch = cc.get_editor_property("child_actor")
            for c in ch.get_components_by_class(unreal.SkeletalMeshComponent):
                if c.get_name() == "Body":
                    for b in bones.split(","):
                        c.hide_bone_by_name(b, unreal.PhysBodyOp.PBO_NONE)
        break
