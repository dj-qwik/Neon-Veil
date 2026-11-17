"""Clear weapon-mesh animations whose skeleton doesn't match the weapon mesh (a mismatched fire anim collapses the
gun's bones: the Kestrel vanished on every shot, leaving only its magazine floating). Report: Saved/NV_weapon_anim_audit.txt"""
import unreal
EAL = unreal.EditorAssetLibrary
out = []
for path in EAL.list_assets("/Game/NeonVeil/Data/Weapons", recursive=False):
    w = unreal.load_asset(path)
    if not isinstance(w, unreal.NVWeaponData):
        continue
    mesh = w.get_editor_property("weapon_mesh")
    skel = mesh.get_editor_property("skeleton") if mesh else None
    changed = False
    for p in ("weapon_fire_anim", "weapon_reload_anim"):
        a = w.get_editor_property(p)
        if not a:
            continue
        ask = a.get_editor_property("skeleton")
        ok = skel is not None and (ask == skel or ask in list(skel.get_editor_property("compatible_skeletons")))
        out.append("%s %s %s anim-skel=%s mesh-skel=%s %s" % (w.get_name(), p, a.get_name(), ask.get_name() if ask else None,
                   skel.get_name() if skel else None, "OK" if ok else "MISMATCH -> cleared"))
        if not ok:
            w.set_editor_property(p, None)
            changed = True
    if changed:
        EAL.save_loaded_asset(w, only_if_is_dirty=False)
open(unreal.Paths.project_saved_dir() + "NV_weapon_anim_audit.txt", "w").write("\n".join(out))
