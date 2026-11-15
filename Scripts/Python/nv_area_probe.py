import sys, unreal
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
O = []
args = sys.argv[2:]
if args and not args[0].lstrip("-").replace(".", "").isdigit():
    lab = args[0]; r = float(args[1])
    for a in EAS.get_all_level_actors():
        if a.get_actor_label() == lab:
            l = a.get_actor_location(); cx, cy, cz = l.x, l.y, l.z
    O.append(f"centre {lab} {cx:.0f},{cy:.0f},{cz:.0f} n_actors {len(EAS.get_all_level_actors())}")
else:
    cx, cy, cz, r = [float(v) for v in args[:4]]
for a in EAS.get_all_level_actors():
    o, e = a.get_actor_bounds(False)
    if abs(o.x - cx) > r + e.x or abs(o.y - cy) > r + e.y or abs(o.z - cz) > r + e.z or e.x > 3000 or e.y > 3000:
        continue
    m = ""
    if isinstance(a, unreal.StaticMeshActor) and a.static_mesh_component.static_mesh:
        c = a.static_mesh_component
        m = f"{c.static_mesh.get_name()} coll {c.get_collision_profile_name()}"
    O.append(f"{a.get_actor_label()} [{a.get_class().get_name()}] {m} x {o.x - e.x:.0f}..{o.x + e.x:.0f} y {o.y - e.y:.0f}..{o.y + e.y:.0f} z {o.z - e.z:.0f}..{o.z + e.z:.0f} loc {a.get_actor_location().x:.0f},{a.get_actor_location().y:.0f},{a.get_actor_location().z:.0f} yaw {a.get_actor_rotation().yaw:.0f}")
    if isinstance(a, unreal.NVObjectiveDoor):
        for n in ("panel_left", "panel_right", "frame"):
            c = a.get_editor_property(n)
            O.append(f"   {n} mesh {c.static_mesh.get_name() if c.static_mesh else None} rel {c.get_editor_property('relative_location')} scl {c.get_editor_property('relative_scale3d')} coll {c.get_collision_profile_name()} en {c.get_collision_enabled()}")
O.sort()
open(unreal.Paths.project_saved_dir() + "NV_area_probe.txt", "w").write("\n".join(O))
