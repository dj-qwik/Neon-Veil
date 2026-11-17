import unreal
MEL = unreal.MaterialEditingLibrary
out = []
for n in ("M_NV_HoloTarget", "M_NV_Bullseye", "M_NV_OrreryGlow", "M_NV_HoloBeam"):
    m = unreal.load_asset("/Game/NeonVeil/Materials/Holo/" + n)
    st = MEL.get_statistics(m)
    out.append("%s exprs=%d blend=%s model=%s px=%s vs=%s" % (n, MEL.get_num_material_expressions(m), m.get_editor_property("blend_mode"),
               m.get_editor_property("shading_model"), st.num_pixel_shader_instructions, st.num_vertex_shader_instructions))
    for p in (unreal.MaterialProperty.MP_EMISSIVE_COLOR, unreal.MaterialProperty.MP_OPACITY):
        e = MEL.get_material_property_input_node(m, p)
        out.append("   %s <- %s" % (p, e.get_name() if e else None))
open(unreal.Paths.project_saved_dir() + "NV_mat_check.txt", "w").write("\n".join(out))
