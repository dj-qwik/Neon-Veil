"""Probe the guard clothing materials actually used by BP_Guard's clothing meshes."""
import unreal
out = []
MEL = unreal.MaterialEditingLibrary
for p in ["/Game/NeonVeil/Characters/GuardMH/Guard/Clothing/MHC_Guard_Outfits",
          "/Game/NeonVeil/Characters/GuardMH/Guard/Clothing/MHC_Guard_Outfits_2"]:
    m = unreal.load_asset(p)
    out.append(p)
    for i, sm in enumerate(m.get_editor_property("materials")):
        mi = sm.get_editor_property("material_interface")
        out.append("  slot%d %s -> %s" % (i, sm.get_editor_property("material_slot_name"), mi.get_path_name() if mi else None))
        if isinstance(mi, unreal.MaterialInstance):
            for v in MEL.get_vector_parameter_names(mi):
                out.append("     V %s = %s" % (v, MEL.get_material_instance_vector_parameter_value(mi, v)))
            for t in MEL.get_texture_parameter_names(mi):
                tv = MEL.get_material_instance_texture_parameter_value(mi, t)
                out.append("     T %s = %s" % (t, tv.get_name() if tv else None))
            par = mi.get_editor_property("parent")
            out.append("     parent %s" % (par.get_path_name() if par else None))
        if isinstance(mi, unreal.Material):
            n = MEL.get_material_property_input_node(mi, unreal.MaterialProperty.MP_BASE_COLOR)
            out.append("     basecolor node %s" % (n.get_class().get_name() if n else None))
open(unreal.Paths.project_saved_dir() + "NV_nv_guard_mat_probe.txt", "w").write("\n".join(out))
