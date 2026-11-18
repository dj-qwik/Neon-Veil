"""List sofas / seating and doors in the current level. Report: Saved/NV_probe_sofa.txt"""
import unreal
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
UES = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
OUT = [UES.get_editor_world().get_path_name()]
for a in EAS.get_all_level_actors():
    n = a.get_actor_label(); m = ""
    if isinstance(a, unreal.StaticMeshActor) and a.static_mesh_component.static_mesh:
        m = a.static_mesh_component.static_mesh.get_name()
    key = (n + m).lower()
    if any(k in key for k in ("sofa", "couch", "chair", "bench", "lounge", "door", "table", "holo")):
        o, e = a.get_actor_bounds(False)
        r = a.get_actor_rotation()
        OUT.append("%s [%s] %s loc=(%d,%d,%d) yaw=%d bo=(%d,%d,%d) be=(%d,%d,%d) folder=%s" % (n, a.get_class().get_name(), m,
            a.get_actor_location().x, a.get_actor_location().y, a.get_actor_location().z, r.yaw, o.x, o.y, o.z, e.x, e.y, e.z, a.get_folder_path()))
open(unreal.Paths.project_saved_dir() + "NV_probe_sofa.txt", "w", encoding="utf-8").write("\n".join(OUT))
