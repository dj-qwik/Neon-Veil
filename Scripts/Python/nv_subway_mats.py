"""List the materials used by the tram car pieces and their editable parameters. Report: Saved/NV_subway_mats.txt"""
import unreal
out = []
seen = set()
MEL = unreal.MaterialEditingLibrary
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    if not a.get_actor_label().startswith("T_"):
        continue
    for c in a.get_components_by_class(unreal.StaticMeshComponent):
        if not c.get_editor_property("static_mesh"):
            continue
        for i in range(c.get_num_materials()):
            m = c.get_material(i)
            if not m or m.get_path_name() in seen:
                continue
            seen.add(m.get_path_name())
            line = "%s  [%s]" % (m.get_path_name(), c.get_editor_property("static_mesh").get_name())
            if isinstance(m, unreal.MaterialInstanceConstant):
                line += "\n    parent=%s" % (m.get_editor_property("parent").get_name() if m.get_editor_property("parent") else None)
                for v in m.get_editor_property("scalar_parameter_values"):
                    line += "\n    S %s = %.3f" % (v.parameter_info.name, v.parameter_value)
                for v in m.get_editor_property("vector_parameter_values"):
                    p = v.parameter_value
                    line += "\n    V %s = (%.2f,%.2f,%.2f)" % (v.parameter_info.name, p.r, p.g, p.b)
                for v in m.get_editor_property("texture_parameter_values"):
                    line += "\n    T %s = %s" % (v.parameter_info.name, v.parameter_value.get_name() if v.parameter_value else None)
                try:
                    allv = MEL.get_vector_parameter_names(m.get_editor_property("parent"))
                    alls = MEL.get_scalar_parameter_names(m.get_editor_property("parent"))
                    line += "\n    parent params S%s V%s" % ([str(x) for x in alls], [str(x) for x in allv])
                except Exception as e:
                    line += "\n    (params: %s)" % e
            out.append(line)
open(unreal.Paths.project_saved_dir() + "NV_subway_mats.txt", "w").write("\n".join(out))
