"""PIE: Kestrel weapon mesh pose check. Saved/NV_pie_gun_diag2.txt"""
import unreal
out = []
try:
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    pawn = unreal.GameplayStatics.get_player_controller(w, 0).get_controlled_pawn()
    gun = next(c for c in pawn.get_components_by_class(unreal.SkeletalMeshComponent) if c.get_name() == "WeaponMesh")
    inst = gun.get_anim_instance()
    cur = inst.get_current_asset() if hasattr(inst, "get_current_asset") else None
    m = gun.get_skeletal_mesh_asset()
    out.append("mesh %s skel %s" % (m.get_path_name(), m.get_editor_property("skeleton").get_path_name()))
    out.append("anim %s skel %s" % (cur.get_path_name() if cur else None, cur.get_editor_property("skeleton").get_path_name() if cur else None))
    names = gun.get_all_socket_names()
    base = gun.get_world_location()
    for n in list(names)[:40]:
        out.append("  %s %s" % (n, gun.get_socket_location(n) - base))
    k = unreal.load_asset("/Game/NeonVeil/Data/Weapons/DA_Weapon_Kestrel")
    for p in ("weapon_fire_anim", "weapon_reload_anim", "weapon_mesh"):
        try:
            out.append("%s = %s" % (p, k.get_editor_property(p)))
        except Exception as e:
            out.append("%s: %s" % (p, e))
except Exception:
    import traceback; out.append(traceback.format_exc())
open(unreal.Paths.project_saved_dir() + "NV_pie_gun_diag2.txt", "w").write("\n".join(out))
