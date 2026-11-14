"""List oversized dressing boxes. Report: Saved/NV_l1_probe_big.txt"""
import unreal
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
out = []
for a in EAS.get_all_level_actors():
    if not str(a.get_folder_path()).startswith(("P_", "R_")):
        continue
    s = a.get_actor_scale3d()
    if max(s.x, s.y, s.z) > 120 and isinstance(a, unreal.StaticMeshActor):
        out.append("%s %s scale(%.0f,%.0f,%.0f) at %s mat %s" % (a.get_folder_path(), a.get_actor_label(), s.x, s.y, s.z,
                   a.get_actor_location(), a.static_mesh_component.get_material(0).get_name()))
open(unreal.Paths.project_saved_dir() + "NV_l1_probe_big.txt", "w").write("\n".join(out))
