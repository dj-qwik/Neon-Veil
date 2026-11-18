"""Editor: everything around the crew-room entrance (x 6450..7050, y 3650..4000). Saved/NV_probe_crewdoor.txt"""
import unreal
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
out = []
for a in EAS.get_all_level_actors():
    o, e = a.get_actor_bounds(False)
    if e.x > 3000 or e.y > 3000:
        continue
    if o.x + e.x >= 6450 and o.x - e.x <= 7050 and o.y + e.y >= 3650 and o.y - e.y <= 4000 and o.z + e.z >= 410 and o.z - e.z <= 620:
        cols = []
        for c in a.get_components_by_class(unreal.PrimitiveComponent):
            if c.get_collision_enabled() != unreal.CollisionEnabled.NO_COLLISION:
                cols.append("%s:%s pawn=%s vis=%s" % (c.get_name(), c.get_collision_profile_name(),
                            c.get_collision_response_to_channel(unreal.CollisionChannel.ECC_PAWN),
                            c.get_collision_response_to_channel(unreal.CollisionChannel.ECC_VISIBILITY)))
        sm = ""
        if isinstance(a, unreal.StaticMeshActor) and a.static_mesh_component.static_mesh:
            sm = a.static_mesh_component.static_mesh.get_name()
        out.append("%s [%s] %s o=(%d,%d,%d) e=(%d,%d,%d) hidden=%s %s" % (a.get_actor_label(), a.get_class().get_name(), sm, o.x, o.y, o.z, e.x, e.y, e.z,
                                                                   a.is_hidden_ed(), cols))
open(unreal.Paths.project_saved_dir() + "NV_probe_crewdoor.txt", "w").write("\n".join(out))
