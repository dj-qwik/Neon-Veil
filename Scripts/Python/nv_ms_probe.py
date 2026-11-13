"""Which level actors use the Crown surface MIs (biggest first) + current MI texture params. Report: Saved/NV_ms_probe.txt"""
import unreal
out = []
targets = ["MI_DIR_PolishedStone", "MI_DIR_CeramicPanel", "MI_DIR_ArchConcrete", "MI_DIR_Titanium"]
for t in targets:
    mi = unreal.load_asset("/Game/NeonVeil/Materials/Art/" + t)
    out.append("%s textures: %s" % (t, [(str(v.parameter_info.name), v.parameter_value.get_path_name() if v.parameter_value else None) for v in mi.get_editor_property("texture_parameter_values")]))
use = {t: [] for t in targets}
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    for c in a.get_components_by_class(unreal.StaticMeshComponent):
        for i in range(c.get_num_materials()):
            m = c.get_material(i)
            if m and m.get_name() in use:
                o, e = a.get_actor_bounds(False)
                use[m.get_name()].append((e.x * e.y + e.y * e.z + e.x * e.z, a.get_actor_label(), o, e))
for t, l in use.items():
    l.sort(key=lambda r: -r[0])
    out.append("%s used by %d actors" % (t, len(l)))
    for s, lab, o, e in l[:6]:
        out.append("   %s c(%.0f,%.0f,%.0f) e(%.0f,%.0f,%.0f)" % (lab, o.x, o.y, o.z, e.x, e.y, e.z))
open(unreal.Paths.project_saved_dir() + "NV_ms_probe.txt", "w").write("\n".join(out))
