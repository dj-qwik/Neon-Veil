"""Directorate recolour for the guard MetaHuman's clothing (Bible palette: pale white, carbon, cyan accents).
Soldier materials: BaseColor -> Desaturate -> x NV_Tint (carbon). Helmet P05: BaseColor desaturated (white/grey,
red trims gone); Emissive desaturated x NV_Glow (cyan optics). Also removes the guards' extra battery mesh
(the outfit's own backpack carries the 'exposed battery pack' tell). Idempotent. Report: Saved/NV_guard_recolor.txt"""
import unreal
out = []
MEL = unreal.MaterialEditingLibrary
EAL = unreal.EditorAssetLibrary
MP = unreal.MaterialProperty

def tint(mat, prop, pname, default):
    if pname in [str(n) for n in MEL.get_vector_parameter_names(mat)]:
        out.append("  %s already has %s" % (mat.get_name(), pname)); return
    src = MEL.get_material_property_input_node(mat, prop)
    if src is None:
        out.append("  %s: nothing on %s" % (mat.get_name(), prop)); return
    src_out = MEL.get_material_property_input_node_output_name(mat, prop)
    x = src.get_editor_property("material_expression_editor_x") + 260
    y = src.get_editor_property("material_expression_editor_y")
    desat = MEL.create_material_expression(mat, unreal.MaterialExpressionDesaturation, x, y)
    par = MEL.create_material_expression(mat, unreal.MaterialExpressionVectorParameter, x, y + 160)
    par.set_editor_property("parameter_name", pname)
    par.set_editor_property("default_value", default)
    mul = MEL.create_material_expression(mat, unreal.MaterialExpressionMultiply, x + 220, y)
    MEL.connect_material_expressions(src, src_out, desat, "")
    MEL.connect_material_expressions(desat, "", mul, "A")
    MEL.connect_material_expressions(par, "", mul, "B")
    MEL.connect_material_property(mul, "", prop)
    out.append("  %s: %s tinted via %s (src out '%s')" % (mat.get_name(), prop, pname, src_out))

CARBON = unreal.LinearColor(0.42, 0.44, 0.47, 1)   # x desaturated albedo -> carbon/charcoal kit
soldier = sorted({m.split(".")[0] for m in EAL.list_assets("/Game/Outfits/TacticalSoldier/Soldier_Outfit_v1/Material")
                  if m.split(".")[0].split("/")[-1].startswith("M_")})
for p in soldier:
    mat = unreal.load_asset(p)
    if isinstance(mat, unreal.Material):
        tint(mat, MP.MP_BASE_COLOR, "NV_Tint", CARBON)
        MEL.recompile_material(mat)
        EAL.save_loaded_asset(mat, only_if_is_dirty=False)

hel = unreal.load_asset("/Game/Outfits/SciFi_Helmet_P05/SciFi_Helmet_P05/Materials/SciFi_Base/M_Helmet_Armor_P05_c1")
tint(hel, MP.MP_BASE_COLOR, "NV_Tint", unreal.LinearColor(1.0, 1.0, 1.0, 1))
tint(hel, MP.MP_EMISSIVE_COLOR, "NV_Glow", unreal.LinearColor(0.25, 2.2, 3.0, 1))
MEL.recompile_material(hel)
EAL.save_loaded_asset(hel, only_if_is_dirty=False)

n = 0
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    if isinstance(a, unreal.NVGuardCharacter):
        a.set_editor_property("battery_mesh_asset", None)
        a.set_actor_location(a.get_actor_location(), False, False)
        n += 1
out.append("battery removed on %d guards" % n)
unreal.EditorLevelLibrary.save_current_level()
open(unreal.Paths.project_saved_dir() + "NV_guard_recolor.txt", "w").write("\n".join(out))
