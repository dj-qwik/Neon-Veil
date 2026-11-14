"""Collision settings of every BP_Tram component in the open map vs a fresh BP_Tram. Report: Saved/NV_l1_probe_tramcol.txt"""
import unreal
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
out = []
def dump(a, tag):
    for c in a.get_components_by_class(unreal.PrimitiveComponent):
        m = c.static_mesh.get_name() if isinstance(c, unreal.StaticMeshComponent) and c.static_mesh else ""
        out.append("%s %s %s %s profile=%s enabled=%s" % (tag, c.get_name(), c.get_class().get_name(), m,
                   c.get_collision_profile_name(), c.get_collision_enabled()))
cls = None
for a in EAS.get_all_level_actors():
    if a.get_class().get_name() == "BP_Tram_C":
        dump(a, "LEVEL"); cls = a.get_class()
if cls:
    f = EAS.spawn_actor_from_class(cls, unreal.Vector(0, 0, -50000))
    dump(f, "FRESH"); EAS.destroy_actor(f)
open(unreal.Paths.project_saved_dir() + "NV_l1_probe_tramcol.txt", "w").write("\n".join(out))
