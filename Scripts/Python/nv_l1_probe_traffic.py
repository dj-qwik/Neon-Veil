"""Traffic + sky + beacons setup in the open map. Report: Saved/NV_l1_probe_traffic.txt"""
import unreal
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
out = []
for a in EAS.get_all_level_actors():
    c = a.get_class().get_name()
    if c in ("NVTrafficStream",):
        props = {}
        for n in ("lane_length", "lane_spread", "vehicles_per_direction", "speed_range", "vehicle_scale", "two_way", "seed",
                  "vehicle_mesh", "forward_material", "reverse_material"):
            try:
                v = a.get_editor_property(n)
                props[n] = v.get_path_name() if hasattr(v, "get_path_name") else str(v)
            except Exception as e:
                props[n] = "ERR"
        out.append("%s %s rot %s %s" % (a.get_actor_label(), a.get_actor_location(), a.get_actor_rotation(), props))
    if c in ("SkyAtmosphere", "ExponentialHeightFog", "DirectionalLight", "SkyLight", "VolumetricCloud") or "Beacon" in a.get_actor_label():
        out.append("ENV %s %s" % (c, a.get_actor_label()))
open(unreal.Paths.project_saved_dir() + "NV_l1_probe_traffic.txt", "w").write("\n".join(out))
