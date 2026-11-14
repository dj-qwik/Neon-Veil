"""PIE: NPC facing check. Report: Saved/NV_npc_facing.txt"""
import unreal
UES = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
w = UES.get_game_world()
out = []
for a in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.Character):
    lab = a.get_actor_label()
    if not lab.startswith("NPC_") and not lab.startswith("G"):
        continue
    v = a.get_velocity()
    line = f"{lab} actor_yaw={a.get_actor_rotation().yaw:.0f} vel_yaw={unreal.MathLibrary.make_rot_from_x(v).yaw:.0f} speed={v.length():.0f}"
    for c in a.get_components_by_class(unreal.SkeletalMeshComponent):
        if c.get_name() == "CharacterMesh0":
            line += f" base={c.get_world_rotation().yaw:.0f}"
    for cc in a.get_components_by_class(unreal.ChildActorComponent):
        ch = cc.get_editor_property("child_actor")
        if ch:
            for c in ch.get_components_by_class(unreal.SkeletalMeshComponent):
                if c.get_name() == "Body":
                    line += f" body={c.get_world_rotation().yaw:.0f} body_rel={c.get_editor_property('relative_rotation').yaw:.0f} child_rel={cc.get_editor_property('relative_rotation').yaw:.0f}"
    out.append(line)
open(unreal.Paths.project_saved_dir() + "NV_npc_facing.txt", "w").write("\n".join(out))
