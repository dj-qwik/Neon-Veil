"""PIE: toggle the MetaHuman body (not face) of an NPC. argv[2] = 'Label on|off'"""
import sys, unreal
UES = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
w = UES.get_game_world()
lab, st = sys.argv[2].split()
out = []
for a in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.Character):
    if a.get_actor_label().startswith(lab):
        for cc in a.get_components_by_class(unreal.ChildActorComponent):
            ch = cc.get_editor_property("child_actor")
            for c in ch.get_components_by_class(unreal.SkeletalMeshComponent):
                out.append(f"{c.get_name()} {c.get_skeletal_mesh_asset().get_name() if c.get_skeletal_mesh_asset() else None} lead={c.get_editor_property('leader_pose_component').get_name() if c.get_editor_property('leader_pose_component') else None}")
                if c.get_name() == "Body":
                    c.set_visibility(st == "on")
        for c in a.get_components_by_class(unreal.SkinnedMeshComponent):
            if c.get_name().startswith("Garment"):
                lp = c.get_editor_property("leader_pose_component")
                out.append(f"{c.get_name()} parent={c.get_attach_parent().get_name() if c.get_attach_parent() else None} lead={lp.get_name() if lp else None} vis={c.is_visible()} scale={c.get_editor_property('relative_scale3d')} mats={[m.get_name() if m else None for m in c.get_materials()]}")
        break
open(unreal.Paths.project_saved_dir() + "NV_npc_body.txt", "w").write("\n".join(out))
