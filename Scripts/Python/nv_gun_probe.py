"""Probe the Sci Fi gunpack: bounds/orientation, bones, animations, materials. Report: Saved/NV_gun_probe.txt"""
import unreal
out = []
P = "/Game/Pack/"
GUNS = {"pistol": P + "B_W_Sci_fi_pistol/skeletal_mesh/SK_A_Sci_fi_Pistol",
        "smg": P + "b_w_smg_mini/skeletal_mesh/SK_b_w_smg_mini",
        "sniper": P + "Sci_fi_sniper_rifle/mesh/SK_SCI_fi_sniper_rifle_ANIMATION"}
for k, p in GUNS.items():
    m = unreal.load_asset(p)
    b = m.get_bounds()
    o, e = b.origin, b.box_extent
    out.append("%s %s origin (%.1f %.1f %.1f) extent (%.1f %.1f %.1f)" % (k, m.get_name(), o.x, o.y, o.z, e.x, e.y, e.z))
    a = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.SkeletalMeshActor, unreal.Vector(0, 0, -50000))
    c = a.skeletal_mesh_component
    c.set_skinned_asset_and_update(m) if hasattr(c, "set_skinned_asset_and_update") else c.set_skeletal_mesh(m)
    bones = []
    for i in range(c.get_num_bones()):
        n = c.get_bone_name(i)
        t = c.get_socket_transform(n, unreal.RelativeTransformSpace.RTS_COMPONENT)
        bones.append("%s(%.0f,%.0f,%.0f)" % (n, t.translation.x, t.translation.y, t.translation.z))
    a.destroy_actor()
    out.append("   bones: " + " ".join(bones))
    out.append("   mats: " + ", ".join("%s" % (sm.get_editor_property("material_interface").get_name() if sm.get_editor_property("material_interface") else None) for sm in m.get_editor_property("materials")))
    skel = m.get_editor_property("skeleton")
    AR = unreal.AssetRegistryHelpers.get_asset_registry()
    folder = p.rsplit("/", 2)[0]
    for d in AR.get_assets(unreal.ARFilter(package_paths=[folder], recursive_paths=True)):
        if str(d.asset_class_path.asset_name) == "AnimSequence":
            an = d.get_asset()
            out.append("   anim %s len %.2f skel %s" % (an.get_name(), an.get_play_length(), an.get_editor_property("skeleton").get_name()))
out.append("muzzle flash candidates:")
AR = unreal.AssetRegistryHelpers.get_asset_registry()
for d in AR.get_assets(unreal.ARFilter(class_paths=[unreal.TopLevelAssetPath("/Script/Niagara", "NiagaraSystem")], package_paths=["/Game"], recursive_paths=True)):
    n = str(d.asset_name).lower()
    if any(k in n for k in ("muzzle", "flash", "tracer", "impact", "spark", "shell", "casing", "hit")):
        out.append("  " + str(d.package_name))
w = unreal.load_asset("/Game/NeonVeil/Data/Weapons/DA_Weapon_VX9")
out.append("VX9 flash=%s tracer=%s impact=%s fire=%s" % (w.get_editor_property("muzzle_flash"), w.get_editor_property("tracer"), w.get_editor_property("impact_effect"), w.get_editor_property("fire_sound")))
open(unreal.Paths.project_saved_dir() + "NV_gun_probe.txt", "w").write("\n".join(out))
