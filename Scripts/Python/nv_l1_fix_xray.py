"""X-ray checkpoint: the FBX import produced texture-less legacy Phong materials (rendered plain white).
Build a small PBR master (BaseColor/Normal/Metallic/Roughness/Emissive texture params) and one instance per slot
with the imported textures, then assign them on the mesh. Report: Saved/NV_l1_fix_xray.txt"""
import unreal
EAL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary
AT = unreal.AssetToolsHelpers.get_asset_tools()
OUT = []
def log(*a):
    OUT.append(" ".join(str(x) for x in a))

D = "/Game/NeonVeil/Art/XRay"
TX = D + "/Textures"
MASTER = "/Game/NeonVeil/Materials/Common/M_NV_PBR_Tex"

def tex(name):
    t = unreal.load_asset(f"{TX}/{name}")
    if not t:
        log("missing texture", name)
    return t

if not EAL.does_asset_exist(MASTER):
    m = AT.create_asset("M_NV_PBR_Tex", "/Game/NeonVeil/Materials/Common", unreal.Material, unreal.MaterialFactoryNew())
    def tp(name, x, y, sampler=None):
        e = MEL.create_material_expression(m, unreal.MaterialExpressionTextureSampleParameter2D, x, y)
        e.set_editor_property("parameter_name", name)
        if sampler:
            e.set_editor_property("sampler_type", sampler)
        return e
    bc = tp("BaseColor", -700, -300)
    nm = tp("Normal", -700, 0, unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
    mt = tp("Metallic", -700, 300, unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_GRAYSCALE)
    rf = tp("Roughness", -700, 600, unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_GRAYSCALE)
    em = tp("Emissive", -700, 900)
    es = MEL.create_material_expression(m, unreal.MaterialExpressionScalarParameter, -450, 1100)
    es.set_editor_property("parameter_name", "EmissiveStrength"); es.set_editor_property("default_value", 4.0)
    emul = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -250, 950)
    MEL.connect_material_expressions(em, "RGB", emul, "A")
    MEL.connect_material_expressions(es, "", emul, "B")
    MEL.connect_material_property(bc, "RGB", unreal.MaterialProperty.MP_BASE_COLOR)
    MEL.connect_material_property(nm, "RGB", unreal.MaterialProperty.MP_NORMAL)
    MEL.connect_material_property(mt, "R", unreal.MaterialProperty.MP_METALLIC)
    MEL.connect_material_property(rf, "R", unreal.MaterialProperty.MP_ROUGHNESS)
    MEL.connect_material_property(emul, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    MEL.recompile_material(m)
    EAL.save_loaded_asset(m)
    log("master created")
master = unreal.load_asset(MASTER)

SETS = {
    "MI_NV_XRay_Machine": ("Security_Machine_LP_Security_X-Ray_", ("BaseCol", "Normal_", "Metalli", "Roughne", "Emissiv")),
    "MI_NV_XRay_Scanner": ("Security_Luggage_LP_Property_Scanner_", ("BaseC", "Norma", "Metal", "Rough", "Emiss")),
}
mis = {}
for name, (prefix, suf) in SETS.items():
    path = f"{D}/{name}"
    mi = unreal.load_asset(path) if EAL.does_asset_exist(path) else AT.create_asset(name, D, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    MEL.set_material_instance_parent(mi, master)
    for param, s in zip(("BaseColor", "Normal", "Metallic", "Roughness", "Emissive"), suf):
        t = tex(prefix + s)
        if not t:
            continue
        if param == "Normal":
            t.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_NORMALMAP)
            t.set_editor_property("srgb", False)
        elif param in ("Metallic", "Roughness"):
            t.set_editor_property("srgb", False)
        EAL.save_loaded_asset(t)
        MEL.set_material_instance_texture_parameter_value(mi, param, t)
    MEL.set_material_instance_scalar_parameter_value(mi, "EmissiveStrength", 6.0)
    MEL.update_material_instance(mi)
    EAL.save_loaded_asset(mi)
    mis[name] = mi
    log("instance", name)

mesh = unreal.load_asset(f"{D}/Security_Checkpoint")
mesh.set_material(0, mis["MI_NV_XRay_Machine"])
mesh.set_material(1, mis["MI_NV_XRay_Scanner"])
EAL.save_loaded_asset(mesh)
log("mesh slots:", [s.material_interface.get_name() for s in mesh.static_materials])
open(unreal.Paths.project_saved_dir() + "NV_l1_fix_xray.txt", "w").write("\n".join(OUT))
