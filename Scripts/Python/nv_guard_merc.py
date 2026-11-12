"""Restyle the free Waveforce mercenary (merged mesh SK_MER_ME_Outfit01) as a Directorate agency guard.

Bible §3 palette: Crown/Directorate = sterile pale white, dark smoked glass, polished ceramic, carbon composite.
Bible §8 guard tells: helmet optics + exposed battery pack. Optics: the goggle lenses glow cyan.
Creates /Game/NeonVeil/Characters/Guard/{SK_NV_Guard, MI_NV_Guard_*} and leaves the pack's own assets untouched.
"""
import unreal

SRC = "/Game/Mercenary_Male_WaveforceStudio/"
DST = "/Game/NeonVeil/Characters/Guard/"
eat = unreal.EditorAssetLibrary
mel = unreal.MaterialEditingLibrary
out = []

C = unreal.LinearColor
WHITE = C(0.62, 0.635, 0.65, 1)      # pale ceramic (linear; reads off-white under the cool key lights)
CARBON = C(0.018, 0.019, 0.022, 1)
CHAR = C(0.045, 0.047, 0.052, 1)
GUNM = C(0.09, 0.095, 0.105, 1)
SMOKE = C(0.02, 0.022, 0.026, 1)
HAIR = C(0.03, 0.022, 0.016, 1)

# MI name -> (TintColor_01, TintColor_02)
TINTS = {
    "MI_MER_ME_Outer01": (WHITE, CHAR),       # jacket shell = ceramic white, trims charcoal
    "MI_MER_ME_Pant01": (CARBON, CHAR),
    "MI_MER_ME_Body": (CHAR, GUNM),
    "MI_MER_ME_Body_Toptank": (CHAR, GUNM),
    "MI_MER_ME_Common": (CHAR, WHITE),
    "MI_MER_ME_ACC01": (GUNM, WHITE),
    "MI_MER_ME_Gloves01": (CARBON, CHAR),
    "MI_MER_ME_Shoes01": (CARBON, CHAR),
    "MI_MER_ME_Glass01": (SMOKE, CHAR),
    "MI_MER_ME_Hair01": (HAIR, HAIR),
    "MI_MER_ME_Head01": (None, None),         # skin untouched
    "MI_MER_ME_Trans_Glass01": (None, None),
}

if not eat.does_directory_exist(DST):
    eat.make_directory(DST)

new = {}
for name, (t1, t2) in TINTS.items():
    src = SRC + "Materials/Materials_Instance/" + name
    dst = DST + name.replace("MI_MER_ME_", "MI_NV_Guard_")
    if eat.does_asset_exist(dst):
        mi = unreal.load_asset(dst)
    else:
        mi = eat.duplicate_asset(src, dst)
    if mi is None:
        out.append("FAILED dup " + name)
        continue
    if t1 is not None:
        mel.set_material_instance_vector_parameter_value(mi, "TintColor_01", t1)
        mel.set_material_instance_vector_parameter_value(mi, "TintColor_02", t2)
    new[SRC + "Materials/Materials_Instance/" + name + "." + name] = mi
    eat.save_loaded_asset(mi)
    out.append("MI " + mi.get_name())

# Optic lenses: emissive cyan on the translucent goggle glass (Bible tell "helmet optics").
lens_src = SRC + "Materials/Materials_Instance/MI_MER_ME_Trans_Glass01"
lens = new.get(lens_src + ".MI_MER_ME_Trans_Glass01")
if lens:
    vs = [str(n) for n in mel.get_vector_parameter_names(lens)]
    ss = [str(n) for n in mel.get_scalar_parameter_names(lens)]
    out.append("lens params V=%s S=%s" % (vs, ss))
    for v in vs:
        if any(k in v.lower() for k in ["color", "tint", "emiss"]):
            mel.set_material_instance_vector_parameter_value(lens, v, C(0.05, 0.75, 1.0, 1))
    for s in ss:
        if "emiss" in s.lower():
            mel.set_material_instance_scalar_parameter_value(lens, s, 8.0)
    eat.save_loaded_asset(lens)

# Guard mesh = duplicate of the merged outfit with Directorate materials.
mesh_dst = DST + "SK_NV_Guard"
mesh = unreal.load_asset(mesh_dst) if eat.does_asset_exist(mesh_dst) else eat.duplicate_asset(SRC + "Mesh/SK_MER_ME_Outfit01", mesh_dst)
mats = []
for sm in mesh.get_editor_property("materials"):
    mi = sm.get_editor_property("material_interface")
    rep = new.get(mi.get_path_name()) if mi else None
    ns = unreal.SkeletalMaterial()
    ns.set_editor_property("material_interface", rep or mi)
    for prop in ("material_slot_name", "imported_material_slot_name", "uv_channel_data"):
        try:
            ns.set_editor_property(prop, sm.get_editor_property(prop))
        except Exception:
            pass
    mats.append(ns)
mesh.set_editor_property("materials", mats)
mesh.post_edit_change() if hasattr(mesh, "post_edit_change") else None
eat.save_loaded_asset(mesh)
out.append("mesh slots: " + ", ".join(m.get_editor_property("material_interface").get_name() for m in mesh.get_editor_property("materials")))

# Assign to the M00 guards.
anim = unreal.load_object(None, SRC + "Animation/MER_ABP_Manny.MER_ABP_Manny_C")
n = 0
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    if isinstance(a, unreal.NVGuardCharacter):
        a.set_editor_property("body_mesh_asset", mesh)
        a.set_editor_property("body_anim_class", anim)
        smc = a.get_component_by_class(unreal.SkeletalMeshComponent)
        if hasattr(smc, "set_skinned_asset_and_update"):
            smc.set_skinned_asset_and_update(mesh)
        else:
            smc.set_skeletal_mesh(mesh)
        smc.set_anim_instance_class(anim)
        n += 1
        out.append("guard " + a.get_actor_label())
out.append("guards updated %d" % n)
unreal.EditorLevelLibrary.save_current_level()
open(unreal.Paths.project_saved_dir() + "NV_nv_guard_merc.txt", "w").write("\n".join(out))
