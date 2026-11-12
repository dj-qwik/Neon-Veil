"""Tall, ~round-in-plan meshes using world scale (incl. ISM instance scales). Report: Saved/NV_find_round_towers2.txt"""
import unreal
out = []
seen = {}
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    for c in a.get_components_by_class(unreal.StaticMeshComponent):
        m = c.get_editor_property("static_mesh")
        if not m:
            continue
        b = m.get_bounding_box(); e = b.max - b.min
        scales = []
        if isinstance(c, unreal.InstancedStaticMeshComponent):
            for i in range(min(c.get_instance_count(), 400)):
                scales.append(c.get_instance_transform(i, True).scale3d)
        else:
            scales.append(c.get_world_scale())
        for s in scales:
            ex, ey, ez = abs(e.x * s.x), abs(e.y * s.y), abs(e.z * s.z)
            if ez < 4000:
                continue
            r = abs(ex - ey) / max(ex, ey, 1) < 0.12
            k = (m.get_path_name(), r)
            if k not in seen:
                mats = [c.get_material(i).get_path_name() if c.get_material(i) else None for i in range(c.get_num_materials())]
                seen[k] = ["%.0fx%.0fx%.0f" % (ex, ey, ez), a.get_actor_label(), a.get_class().get_name(), c.get_name(), mats, 0]
            seen[k][5] += 1
for (path, r), v in sorted(seen.items(), key=lambda kv: not kv[0][1]):
    out.append("%s %s %s uses=%d  %s/%s (%s)\n    mats %s" % ("ROUND" if r else "     ", path, v[0], v[5], v[1], v[3], v[2], v[4]))
out.append("total %d" % len(seen))
open(unreal.Paths.project_saved_dir() + "NV_find_round_towers2.txt", "w").write("\n".join(out))
