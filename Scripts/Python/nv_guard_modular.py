"""Assemble the M00 agency guard from the Waveforce modular pieces (no mohawk, shades or chain) + battery pack.

Leader: SK_NV_Guard_Body (carbon undersuit, bare head until a helmet is claimed).
Followers (leader pose): jacket/vest, trousers, boots, gloves, common (eyes/teeth).
Battery pack: SM_Sci_Fi_Battery_Unit from our Sci-Fi Light kit on the upper back (Bible §8 tell).
Run after nv_guard_merc (which makes the MI_NV_Guard_* materials) and nv_guard_suit.
"""
import unreal

SRC = "/Game/Mercenary_Male_WaveforceStudio/"
DST = "/Game/NeonVeil/Characters/Guard/"
eat = unreal.EditorAssetLibrary
out = []


def nv_mi(mi):
    if not mi:
        return mi
    n = mi.get_name().replace("MI_MER_ME_", "MI_NV_Guard_")
    p = DST + n
    return unreal.load_asset(p) if eat.does_asset_exist(p) else mi


def nv_mesh(src_rel, dst_name):
    dst = DST + dst_name
    mesh = unreal.load_asset(dst) if eat.does_asset_exist(dst) else eat.duplicate_asset(SRC + src_rel, dst)
    mats = []
    for sm in mesh.get_editor_property("materials"):
        ns = unreal.SkeletalMaterial()
        ns.set_editor_property("material_interface", nv_mi(sm.get_editor_property("material_interface")))
        for prop in ("material_slot_name", "uv_channel_data"):
            try:
                ns.set_editor_property(prop, sm.get_editor_property(prop))
            except Exception:
                pass
        mats.append(ns)
    mesh.set_editor_property("materials", mats)
    eat.save_loaded_asset(mesh)
    out.append("%s: %s" % (dst_name, ", ".join(m.get_editor_property("material_interface").get_name()
                                              for m in mesh.get_editor_property("materials"))))
    return mesh


body = nv_mesh("Mesh/Modular/SK_MER_ME_Body", "SK_NV_Guard_Body")
parts = [nv_mesh("Mesh/Modular/SK_MER_ME_Outer01", "SK_NV_Guard_Outer"),
         nv_mesh("Mesh/Modular/SK_MER_ME_Pant01", "SK_NV_Guard_Pant"),
         nv_mesh("Mesh/Modular/SK_MER_ME_Shoes01", "SK_NV_Guard_Shoes"),
         nv_mesh("Mesh/Modular/SK_MER_ME_Gloves01", "SK_NV_Guard_Gloves"),
         nv_mesh("Mesh/Modular/SK_MER_ME_Common", "SK_NV_Guard_Common")]
anim = unreal.load_object(None, SRC + "Animation/MER_ABP_Manny.MER_ABP_Manny_C")
battery = unreal.load_asset("/Game/Sci_Fi_Light/Static_Meshes/SM_Sci_Fi_Battery_Unit/Mesh/SM_Sci_Fi_Battery_Unit")
bb = battery.get_bounding_box()
out.append("battery bounds min %s max %s" % (bb.min, bb.max))
helmet_path = None
for cand in ["/Game/NeonVeil/Characters/Guard/SM_NV_Guard_Helmet"]:
    if eat.does_asset_exist(cand):
        helmet_path = cand

# Battery: mesh space faces +Y; back = -Y. Long axis (X, 61 cm) vertical, scaled to a ~30 cm pack.
bat_xf = unreal.Transform(location=unreal.Vector(0, -20, 128), rotation=unreal.Rotator(roll=0, pitch=90, yaw=0),
                          scale=unreal.Vector(0.48, 0.48, 0.48))
n = 0
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    if not isinstance(a, unreal.NVGuardCharacter):
        continue
    a.set_editor_property("body_mesh_asset", body)
    a.set_editor_property("body_anim_class", anim)
    a.set_editor_property("outfit_parts", parts)
    a.set_editor_property("battery_mesh_asset", battery)
    a.set_editor_property("battery_offset", bat_xf)
    if helmet_path:
        a.set_editor_property("helmet_mesh_asset", unreal.load_asset(helmet_path))
    # Touch the transform so OnConstruction reruns with the new properties.
    a.set_actor_location(a.get_actor_location(), False, False)
    n += 1
    out.append("guard " + a.get_actor_label())
out.append("guards %d helmet %s" % (n, helmet_path))
unreal.EditorLevelLibrary.save_current_level()
open(unreal.Paths.project_saved_dir() + "NV_nv_guard_modular.txt", "w").write("\n".join(out))
