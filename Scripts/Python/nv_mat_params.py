"""List a material instance's parameters. Args: asset path. Report: Saved/NV_mat_params.txt"""
import unreal, sys
p = sys.argv[2] if len(sys.argv) > 2 else "/Game/SciFiTramStation/Materials/MI_Trim_B"
m = unreal.load_object(None, p + "." + p.split("/")[-1]) or unreal.EditorAssetLibrary.load_asset(p)
if m is None:
    raise RuntimeError("cannot load " + p)
OUT = [f"{p} parent={m.get_editor_property('parent').get_path_name() if m.get_editor_property('parent') else None}"]
MEL = unreal.MaterialEditingLibrary
for kind, names, getter in (("scalar", MEL.get_scalar_parameter_names(m), MEL.get_material_instance_scalar_parameter_value),
                            ("vector", MEL.get_vector_parameter_names(m), MEL.get_material_instance_vector_parameter_value),
                            ("texture", MEL.get_texture_parameter_names(m), MEL.get_material_instance_texture_parameter_value)):
    for n in names:
        try:
            v = getter(m, n)
        except Exception as e:
            v = e
        OUT.append(f"{kind} {n} = {v.get_path_name() if hasattr(v, 'get_path_name') else v}")
open(unreal.Paths.project_saved_dir() + "NV_mat_params.txt", "w").write("\n".join(OUT))
