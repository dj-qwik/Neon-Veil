"""List MI_Hologram_Planets parameters (and its parent) so the orrery rings can be tinted cyan without losing the
textures' alpha (the flat glow material turned every planet sprite into a square). Saved/NV_holo_planets_probe.txt"""
import unreal
out = []
try:
    mi = unreal.load_asset("/Game/ModularScifiInterior/Materials/Parents/MI_Hologram_Planets")
    out.append("parent %s" % mi.get_editor_property("parent").get_path_name())
    for key in ("scalar_parameter_values", "vector_parameter_values", "texture_parameter_values"):
        for p in mi.get_editor_property(key):
            out.append("%s %s = %s" % (key.split("_")[0], p.get_editor_property("parameter_info").get_editor_property("name"), p.get_editor_property("parameter_value")))
    par = mi.get_editor_property("parent")
    MEL = unreal.MaterialEditingLibrary
    out.append("parent vectors %s" % MEL.get_vector_parameter_names(par))
    out.append("parent scalars %s" % MEL.get_scalar_parameter_names(par))
    out.append("parent textures %s" % MEL.get_texture_parameter_names(par))
    out.append("blend %s" % par.get_editor_property("blend_mode"))
except Exception:
    import traceback; out.append(traceback.format_exc())
open(unreal.Paths.project_saved_dir() + "NV_holo_planets_probe.txt", "w").write("\n".join(out))
