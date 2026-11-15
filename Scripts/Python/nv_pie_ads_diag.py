"""PIE diagnostic for first-person ADS clutter. argv[-1]: ';'-separated commands
arx | aim 0/1 | hide COMP 0/1 | bones | comps | shot NAME
Report: Saved/NV_ads_diag.txt"""
import os, sys, unreal
w = unreal.EditorLevelLibrary.get_game_world()
OUT = []
pawn = unreal.GameplayStatics.get_player_pawn(w, 0)
pc = unreal.GameplayStatics.get_player_controller(w, 0)
wc = pawn.get_component_by_class(unreal.NVWeaponComponent) if pawn else None
SHOTS = os.path.join(unreal.Paths.project_saved_dir(), "NV_shots")
os.makedirs(SHOTS, exist_ok=True)


def comp(name):
    for c in pawn.get_components_by_class(unreal.SceneComponent):
        if c.get_name() == name:
            return c
    return None


for cmd in sys.argv[-1].split(";"):
    a = cmd.split()
    if not a:
        continue
    if a[0] == "arx" and wc:
        d = unreal.load_asset("/Game/NeonVeil/Data/Weapons/DA_Weapon_ARX")
        wc.give_weapon(d, True)
        OUT.append("weapon %s" % wc.get_current_weapon().get_name())
    elif a[0] == "aim" and wc:
        wc.set_aiming(a[1] == "1")
    elif a[0] == "hide":
        c = comp(a[1])
        if c:
            c.set_hidden_in_game(a[2] == "1")
        OUT.append("hide %s %s -> %s" % (a[1], a[2], c is not None))
    elif a[0] == "comps":
        cam = comp("FirstPersonCamera")
        ct = cam.get_world_transform()
        for c in pawn.get_components_by_class(unreal.PrimitiveComponent):
            m = ""
            if isinstance(c, unreal.SkeletalMeshComponent):
                sk = c.get_skeletal_mesh_asset()
                m = sk.get_name() if sk else "-"
            elif isinstance(c, unreal.StaticMeshComponent):
                sm = c.get_editor_property("static_mesh")
                m = sm.get_name() if sm else "-"
            OUT.append("%s [%s] mesh=%s visible=%s hiddenInGame=%s ownerNoSee=%s onlyOwner=%s" % (
                c.get_name(), c.get_class().get_name(), m, c.is_visible(), c.get_editor_property("hidden_in_game"),
                c.get_editor_property("owner_no_see"), c.get_editor_property("only_owner_see")))
    elif a[0] == "bones":
        cam = comp("FirstPersonCamera")
        ct = cam.get_world_transform()
        fp = comp("FirstPersonMesh")
        for b in ("clavicle_r", "upperarm_r", "lowerarm_r", "hand_r", "clavicle_l", "upperarm_l", "lowerarm_l", "hand_l", "spine_05", "neck_01", "head"):
            try:
                p = fp.get_socket_location(b)
                l = ct.inverse_transform_location(p)
                OUT.append("bone %-11s cam-space x=%.1f y=%.1f z=%.1f" % (b, l.x, l.y, l.z))
            except Exception as e:
                OUT.append("bone %s err %s" % (b, e))
        OUT.append("ads alpha %.2f" % wc.get_ads_alpha())
        OUT.append("vmroot rel %s" % comp("ViewmodelRoot").get_relative_transform())
        OUT.append("fp rel %s" % fp.get_relative_transform())
        bn = fp.get_num_bones()
        OUT.append("fp bones %d: %s" % (bn, ", ".join(str(fp.get_bone_name(i)) for i in range(min(bn, 80)))))
    elif a[0] == "shot":
        path = os.path.join(SHOTS, a[1] + ".png").replace("\\", "/")
        unreal.SystemLibrary.execute_console_command(w, 'HighResShot 1280x720 filename="%s"' % path, pc)
        OUT.append("shot " + path)
open(unreal.Paths.project_saved_dir() + "NV_ads_diag.txt", "w").write("\n".join(OUT))
