"""List skyline actors with world bounds and plan roundness. Report: Saved/NV_skyline_list.txt"""
import unreal
out = []
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    o, e = a.get_actor_bounds(False)
    if e.z < 3000:
        continue
    comps = a.get_components_by_class(unreal.PrimitiveComponent)
    cn = {}
    for c in comps:
        cn[c.get_class().get_name()] = cn.get(c.get_class().get_name(), 0) + 1
    r = abs(e.x - e.y) / max(e.x, e.y, 1)
    out.append("%.2f %s (%s) folder=%s at (%.0f,%.0f,%.0f) ext %.0fx%.0fx%.0f comps=%s" % (
        r, a.get_actor_label(), a.get_class().get_name(), a.get_folder_path(), o.x, o.y, o.z, e.x, e.y, e.z, cn))
out.sort()
open(unreal.Paths.project_saved_dir() + "NV_skyline_list.txt", "w").write("\n".join(out))
