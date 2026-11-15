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
MASTER = D + "/M_NV_BodyMasked4"
# M_NV_BodyMasked2 never compiled: its mask samplers were Linear Color but the pack's body masks are sRGB, and the
# parameters had no default textures. A material that fails to compile renders as the engine's grey default material
# with no opacity mask, so every citizen's body showed through their clothes as flat grey patches and grey hands.
# v4: Color samplers for the masks, real default textures on every parameter, linear masks copied to sRGB, and the
# masks multiplied (white = visible) instead of inverted (v3 clipped the hands).
VT_COLOR = unreal.MaterialSamplerType.SAMPLERTYPE_VIRTUAL_COLOR
VT_NORMAL = unreal.MaterialSamplerType.SAMPLERTYPE_VIRTUAL_NORMAL

WHITE = None
def white():
    global WHITE
    if WHITE is None:
        WHITE = unreal.load_asset("/Engine/EngineResources/WhiteSquareTexture")
    return WHITE

def srgb_copy(t):
    """Masks are sampled as Color (sRGB). The odd linear one (jeans) gets an sRGB copy in our folder."""
    if t is None or t.get_editor_property("srgb"):
        return t
    path = f"{D}/Masks/{t.get_name()}_sRGB"
    if not EAL.does_asset_exist(path):
        EAL.duplicate_asset(t.get_path_name(), path)
        c = unreal.load_asset(path)
        c.set_editor_property("srgb", True)
        EAL.save_loaded_asset(c)
    return unreal.load_asset(path)

def master():
    if EAL.does_asset_exist(MASTER):
        return unreal.load_asset(MASTER)
    m = AT.create_asset("M_NV_BodyMasked4", D, unreal.Material, unreal.MaterialFactoryNew())
    m.set_editor_property("blend_mode", unreal.BlendMode.BLEND_MASKED)
    m.set_editor_property("two_sided", False)
    m.set_editor_property("used_with_skeletal_mesh", True)
    def tp(name, x, y, sampler, default):
        e = MEL.create_material_expression(m, unreal.MaterialExpressionTextureSampleParameter2D, x, y)
        e.set_editor_property("parameter_name", name)
        e.set_editor_property("texture", default)
        e.set_editor_property("sampler_type", sampler)
        return e
    ref = "/MetaHumanCrowdContent/Characters/Assembled/AverageFemale_Head01/Body/Baked/"
    bc = tp("BodyBC", -900, -300, VT_COLOR, unreal.load_asset(ref + "T_Body_BC_VT"))
    nm = tp("BodyN", -900, 0, VT_NORMAL, unreal.load_asset(ref + "T_Body_N_VT"))
    masks = [tp(n, -900, 300 + k * 260, unreal.MaterialSamplerType.SAMPLERTYPE_COLOR, white()) for k, n in enumerate(("MaskTop", "MaskBottom", "MaskShoes"))]
    # The pack's body masks are WHITE where the body stays visible and black under the garment, so the body's opacity
    # is the product of the worn garments' masks (an unused slot gets white).
    mul1 = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -600, 400)
    MEL.connect_material_expressions(masks[0], "R", mul1, "A")
    MEL.connect_material_expressions(masks[1], "R", mul1, "B")
    mul2 = MEL.create_material_expression(m, unreal.MaterialExpressionMultiply, -480, 500)
    MEL.connect_material_expressions(mul1, "", mul2, "A")
    MEL.connect_material_expressions(masks[2], "R", mul2, "B")
    inv = mul2
    rough = MEL.create_material_expression(m, unreal.MaterialExpressionScalarParameter, -450, 150)
    rough.set_editor_property("parameter_name", "Roughness"); rough.set_editor_property("default_value", 0.55)
    MEL.connect_material_property(bc, "RGB", unreal.MaterialProperty.MP_BASE_COLOR)
    MEL.connect_material_property(nm, "RGB", unreal.MaterialProperty.MP_NORMAL)
    MEL.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    MEL.connect_material_property(inv, "", unreal.MaterialProperty.MP_OPACITY_MASK)
    MEL.recompile_material(m)
    EAL.save_loaded_asset(m)
    return m

def body_mask_for(garment, sex="f"):
    """The body-mask texture shipped next to a garment (cloth asset); the wearer's sex first where the pack has both."""
    root = garment.get_path_name().split("/ClothAssets/")[0]
    root = root.rsplit("/", 1)[0]                  # OA_x/<Name> -> OA_x
    f = unreal.ARFilter(package_paths=[root], recursive_paths=True, class_paths=[unreal.TopLevelAssetPath("/Script/Engine", "Texture2D")])
    found = [str(ad.package_name) for ad in AR.get_assets(f) if "bodymask" in str(ad.asset_name).lower()]
    found.sort(key=lambda n: 0 if n.rsplit("/", 1)[-1].lower().startswith(sex + "_") else 1)
    return srgb_copy(unreal.load_asset(found[0])) if found else None

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
    sex = "f" if "female" in body_mesh.get_name().lower() else "m"
    for slot, g in zip(slots, list(garments) + [None] * 3):
        t = body_mask_for(g, sex) if g else None
        MEL.set_material_instance_texture_parameter_value(mi, slot, t or white())
    MEL.update_material_instance(mi)
    EAL.save_loaded_asset(mi)
    return mi
