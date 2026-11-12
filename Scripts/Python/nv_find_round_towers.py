"""Find tall round towers (spiralling-window report): actors/ISM instances whose mesh is tall and ~circular in plan.
Report: Saved/NV_find_round_towers.txt"""
import unreal
out = []
seen = {}
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    for c in a.get_components_by_class(unreal.StaticMeshComponent):
        m = c.get_editor_property("static_mesh")
        if not m:
            continue
        b = m.get_bounding_box()
        e = (b.max - b.min)
        if e.z < 3000 or e.x < 500:
            continue
        round_ = abs(e.x - e.y) / max(e.x, e.y) < 0.08
        key = m.get_path_name()
        if key not in seen:
            mats = [c.get_material(i).get_path_name() if c.get_material(i) else None for i in range(c.get_num_materials())]
            n = c.get_instance_count() if isinstance(c, unreal.InstancedStaticMeshComponent) else 1
            seen[key] = [round_, e, a.get_actor_label(), a.get_class().get_name(), mats, n, 0]
        seen[key][6] += 1
for k, (r, e, lab, cls, mats, n, cnt) in sorted(seen.items(), key=lambda kv: -kv[1][0]):
    out.append("%s %s  %.0fx%.0fx%.0f  uses=%d  e.g. %s (%s)\n    mats %s" % ("ROUND" if r else "     ", k, e.x, e.y, e.z, cnt, lab, cls, mats))
open(unreal.Paths.project_saved_dir() + "NV_find_round_towers.txt", "w").write("\n".join(out))
