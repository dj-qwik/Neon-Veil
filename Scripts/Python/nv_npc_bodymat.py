"""Masked MetaHuman body material for the dressed citizens.
The crowd pack hides the body under clothing with per-garment body-mask textures (its own renderer applies them);
on our actors the full body was drawn and broke through the clothes. M_NV_BodyMasked samples the body's baked
textures and clips (opacity mask) wherever any worn garment's body mask covers. One instance per body+outfit.
Usage: imported by nv_npcs.py -> body_material(body_mesh, garments). Assets under /Game/NeonVeil/Characters/NPC."""
import unreal
EAL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary
AT = unreal.AssetToolsHelpers.get_asset_tools()
AR = unreal.AssetRegistryHelpers.get_asset_registry()
D = "/Game/NeonVeil/Characters/NPC"
MASTER = D + "/M_NV_BodyMasked2"
VT_COLOR = unreal.MaterialSamplerType.SAMPLERTYPE_VIRTUAL_COLOR
VT_NORMAL = unreal.MaterialSamplerType.SAMPLERTYPE_VIRTUAL_NORMAL

def master():
    if EAL.does_asset_exist(MASTER):
        return unreal.load_asset(MASTER)
    m = AT.create_asset("M_NV_BodyMasked2", D, unreal.Material, unreal.MaterialFactoryNew())
    m.set_editor_property("blend_mode", unreal.BlendMode.BLEND_MASKED)
    m.set_editor_property("two_sided", False)
    m.set_editor_property("used_with_skeletal_mesh", True)
    def tp(name, x, y, sampler):
        e = MEL.create_material_expression(m, unreal.MaterialExpressionTextureSampleParameter2D, x, y)
        e.set_editor_property("parameter_name", name)
        e.set_editor_property("sampler_type", sampler)
        return e
    bc = tp("BodyBC", -900, -300, VT_COLOR)
    nm = tp("BodyN", -900, 0, VT_NORMAL)
    masks = [tp(n, -900, 300 + k * 260, unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR) for k, n in enumerate(("MaskTop", "MaskBottom", "MaskShoes"))]
    # masks use different channels per garment: anything non-black in any channel hides the body there
    add1 = MEL.create_material_expression(m, unreal.MaterialExpressionAdd, -600, 400)
    MEL.connect_material_expressions(masks[0], "RGB", add1, "A")
    MEL.connect_material_expressions(masks[1], "RGB", add1, "B")
    add2 = MEL.create_material_expression(m, unreal.MaterialExpressionAdd, -480, 500)
    MEL.connect_material_expressions(add1, "", add2, "A")
    MEL.connect_material_expressions(masks[2], "RGB", add2, "B")
    one3 = MEL.create_material_expression(m, unreal.MaterialExpressionConstant3Vector, -480, 650)
    one3.set_editor_property("constant", unreal.LinearColor(1, 1, 1, 1))
    dot = MEL.create_material_expression(m, unreal.MaterialExpressionDotProduct, -360, 520)
    MEL.connect_material_expressions(add2, "", dot, "A")
    MEL.connect_material_expressions(one3, "", dot, "B")
    sat = MEL.create_material_expression(m, unreal.MaterialExpressionSaturate, -260, 520)
    MEL.connect_material_expressions(dot, "", sat, "")
    inv = MEL.create_material_expression(m, unreal.MaterialExpressionOneMinus, -160, 520)
    MEL.connect_material_expressions(sat, "", inv, "")
    rough = MEL.create_material_expression(m, unreal.MaterialExpressionScalarParameter, -450, 150)
    rough.set_editor_property("parameter_name", "Roughness"); rough.set_editor_property("default_value", 0.55)
    MEL.connect_material_property(bc, "RGB", unreal.MaterialProperty.MP_BASE_COLOR)
    MEL.connect_material_property(nm, "RGB", unreal.MaterialProperty.MP_NORMAL)
    MEL.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    MEL.connect_material_property(inv, "", unreal.MaterialProperty.MP_OPACITY_MASK)
    MEL.recompile_material(m)
    EAL.save_loaded_asset(m)
    return m

BLACK = None
def black():
    global BLACK
    if BLACK is None:
        BLACK = unreal.load_asset("/Engine/EngineResources/Black")
    return BLACK

def body_mask_for(garment):
    """The body-mask texture shipped next to a garment (cloth asset)."""
    root = garment.get_path_name().split("/ClothAssets/")[0]
    root = root.rsplit("/", 1)[0]                  # OA_x/<Name> -> OA_x
    f = unreal.ARFilter(package_paths=[root], recursive_paths=True, class_paths=[unreal.TopLevelAssetPath("/Script/Engine", "Texture2D")])
    for ad in AR.get_assets(f):
        if "bodymask" in str(ad.asset_name).lower():
            return unreal.load_asset(str(ad.package_name))
    return None

def body_material(label, body_mesh, garments):
    """MIC for this citizen: the body's own baked textures + the worn garments' body masks."""
    m = master()
    src = body_mesh.get_editor_property("materials")[0].material_interface
    texs = {str(tp.parameter_info.name): tp.parameter_value for tp in src.get_editor_property("texture_parameter_values")}
    name = f"MI_NPCBody_{label}"
    path = f"{D}/{name}"
    mi = unreal.load_asset(path) if EAL.does_asset_exist(path) else AT.create_asset(name, D, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    MEL.set_material_instance_parent(mi, m)
    if texs.get("Basecolor Baked VT"):
        MEL.set_material_instance_texture_parameter_value(mi, "BodyBC", texs["Basecolor Baked VT"])
    if texs.get("Normal Baked VT"):
        MEL.set_material_instance_texture_parameter_value(mi, "BodyN", texs["Normal Baked VT"])
    slots = ["MaskTop", "MaskBottom", "MaskShoes"]
    for slot, g in zip(slots, list(garments) + [None] * 3):
        t = body_mask_for(g) if g else None
        MEL.set_material_instance_texture_parameter_value(mi, slot, t or black())
    MEL.update_material_instance(mi)
    EAL.save_loaded_asset(mi)
    return mi
