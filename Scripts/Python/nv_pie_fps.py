"""PIE helper for the viewmodel/armour pass. argv[-1] is a ';'-separated list of commands:
give | equip N | aim 0/1 | fire | reload | guard [dist] | shot NAME
Report: Saved/NV_pie_fps.txt"""
import math, os, sys, unreal
w = unreal.EditorLevelLibrary.get_game_world()
OUT = []
pawn = unreal.GameplayStatics.get_player_pawn(w, 0)
pc = unreal.GameplayStatics.get_player_controller(w, 0)
wc = pawn.get_component_by_class(unreal.NVWeaponComponent) if pawn else None
SHOTS = os.path.join(unreal.Paths.project_saved_dir(), "NV_shots")
os.makedirs(SHOTS, exist_ok=True)
for cmd in sys.argv[-1].split(";"):
    a = cmd.split()
    if not a:
        continue
    if a[0] == "give" and wc:
        for n in ("DA_Weapon_VX9", "DA_Weapon_Kestrel", "DA_Weapon_ARX", "DA_Weapon_TP12", "DA_Weapon_Harrow"):
            wc.give_weapon(unreal.load_asset("/Game/NeonVeil/Data/Weapons/" + n), n == "DA_Weapon_VX9")
        OUT.append("gave 3")
    elif a[0] == "arms" and pawn:
        pawn.set_editor_property("arms_mesh_asset", unreal.load_asset("/Game/KINEMATION/Sci-fi_FPS_Pack/Gloves/Meshes/SKM_SciFi_Arms"))
        OUT.append("arms set")
    elif a[0] == "vm":   # vm DA_name hx hy hz ax ay az
        d = unreal.load_asset("/Game/NeonVeil/Data/Weapons/" + a[1])
        v = [float(x) for x in a[2:8]]
        d.set_editor_property("viewmodel_hip_offset", unreal.Vector(*v[:3]))
        d.set_editor_property("viewmodel_ads_offset", unreal.Vector(*v[3:6]))
        OUT.append("vm %s %s" % (a[1], v))
    elif a[0] == "aw":   # aw DA x y z pitch yaw roll scale  (weapon on the arms' gun bone)
        d = unreal.load_asset("/Game/NeonVeil/Data/Weapons/" + a[1])
        v = [float(x) for x in a[2:9]]
        d.set_editor_property("arms_weapon_offset", unreal.Transform(location=unreal.Vector(*v[:3]),
            rotation=unreal.Rotator(pitch=v[3], yaw=v[4], roll=v[5]), scale=unreal.Vector(v[6], v[6], v[6])))
        OUT.append("aw %s %s" % (a[1], v))
    elif a[0] == "rot":   # rot DA pitch yaw  (hip convergence)
        d = unreal.load_asset("/Game/NeonVeil/Data/Weapons/" + a[1])
        d.set_editor_property("viewmodel_rotation", unreal.Rotator(pitch=float(a[2]), yaw=float(a[3]), roll=0))
    elif a[0] == "bone":   # bone DA_name bonename
        d = unreal.load_asset("/Game/NeonVeil/Data/Weapons/" + a[1])
        d.set_editor_property("arms_weapon_bone", unreal.Name(a[2]))
    elif a[0] == "equip" and wc:
        OUT.append("equip %s -> %s" % (a[1], wc.equip_slot(int(a[1]))))
    elif a[0] == "aim" and wc:
        wc.set_aiming(a[1] == "1")
    elif a[0] == "reload" and wc:
        wc.reload()
    elif a[0] == "fire":
        unreal.SystemLibrary.execute_console_command(w, "NVFire 1", pc)
    elif a[0] == "guard" and pawn:
        d = float(a[1]) if len(a) > 1 else 260.0
        gs = unreal.GameplayStatics.get_all_actors_of_class(w, unreal.NVGuardCharacter)
        if gs:
            g = gs[0]
            gl, f = g.get_actor_location(), g.get_actor_forward_vector()
            p = unreal.Vector(gl.x + f.x * d, gl.y + f.y * d, gl.z + 10)
            pawn.set_actor_location(p, False, True)
            yaw = math.degrees(math.atan2(gl.y - p.y, gl.x - p.x))
            pc.set_control_rotation(unreal.Rotator(roll=0, pitch=-4, yaw=yaw))
            OUT.append("guard %s at %s" % (g.get_actor_label(), gl))
    elif a[0] == "dbg" and pawn:
        cam = unreal.GameplayStatics.get_player_camera_manager(w, 0)
        OUT.append("cam %s" % cam.get_camera_location())
        OUT.append("pawn class %s / parent %s arms=%s" % (pawn.get_class().get_path_name(), unreal.SystemLibrary.get_class_display_name(pawn.get_class()),
                   pawn.get_editor_property("arms_mesh_asset")))
        for c in pawn.get_components_by_class(unreal.SceneComponent):
            n = c.get_name()
            if n in ("FirstPersonCamera", "ViewmodelRoot", "FirstPersonMesh", "WeaponMesh", "WeaponStaticMesh"):
                extra = ""
                if isinstance(c, unreal.SkeletalMeshComponent):
                    m = c.get_skeletal_mesh_asset() if hasattr(c, "get_skeletal_mesh_asset") else c.skeletal_mesh
                    extra = " mesh=%s vis=%s hidden=%s parent=%s sock=%s" % (m.get_name() if m else None, c.is_visible(),
                        c.get_editor_property("hidden_in_game"), c.get_attach_parent().get_name() if c.get_attach_parent() else None,
                        c.get_attach_socket_name())
                OUT.append("%s world %s rel %s%s" % (n, c.get_world_location(), c.get_relative_transform().translation, extra))
            if n == "FirstPersonMesh":
                for b in ("head", "hand_r", "ik_hand_gun", "weapon_r"):
                    OUT.append("   bone %s %s" % (b, c.get_socket_location(b)))
    elif a[0] == "shot":
        path = os.path.join(SHOTS, a[1] + ".png").replace("\\", "/")
        unreal.SystemLibrary.execute_console_command(w, 'HighResShot 1280x720 filename="%s"' % path, pc)
        OUT.append("shot " + path)
cw = wc.get_current_weapon() if wc else None
OUT.append("weapon %s" % (cw.get_name() if cw else None))
open(unreal.Paths.project_saved_dir() + "NV_pie_fps.txt", "w").write("\n".join(OUT))
