"""List the meshes each skyline tower design is built from (to find the round ones)."""
import unreal
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
out = []; seen = set()
for a in EAS.get_all_level_actors():
    c = a.get_class().get_name()
    if "Tower" not in c or c in seen: continue
    seen.add(c)
    o, e = a.get_actor_bounds(False)
    meshes = {}
    for comp in a.get_components_by_class(unreal.InstancedStaticMeshComponent):
        m = comp.static_mesh
        if m:
            meshes[m.get_name()] = meshes.get(m.get_name(), 0) + comp.get_instance_count()
    out.append("%s  bounds %s\n  %s" % (c, e, sorted(meshes.items(), key=lambda kv: -kv[1])[:25]))
open(unreal.Paths.project_saved_dir() + "NV_tower_probe.txt", "w").write("\n".join(out))
