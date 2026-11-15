"""PIE helper for the melee/baton pass. argv[-1]: ';'-separated commands
equip N | holster | strike baton|bash|fist | aim 0/1 | aw x y z pitch yaw roll (baton grip, re-equips) |
fistoff x y z | shot NAME | state
Report: Saved/NV_pie_melee.txt"""
import os, sys, unreal
w = unreal.EditorLevelLibrary.get_game_world()
OUT = []
pawn = unreal.GameplayStatics.get_player_pawn(w, 0)
pc = unreal.GameplayStatics.get_player_controller(w, 0)
wc = pawn.get_component_by_class(unreal.NVWeaponComponent)
mc = pawn.get_component_by_class(unreal.NVMeleeComponent)
SHOTS = os.path.join(unreal.Paths.project_saved_dir(), "NV_shots")
os.makedirs(SHOTS, exist_ok=True)
STY = {"baton": unreal.NVMeleeStyle.BATON, "bash": unreal.NVMeleeStyle.GUN_BASH, "fist": unreal.NVMeleeStyle.FIST}
for cmd in sys.argv[-1].split(";"):
    a = cmd.split()
    if not a:
        continue
    if a[0] == "equip":
        OUT.append("equip %s -> %s" % (a[1], wc.equip_slot(int(a[1]))))
    elif a[0] == "holster":
        wc.holster()
    elif a[0] == "strike":
        OUT.append("strike %s -> %s" % (a[1], mc.strike(STY[a[1]])))
    elif a[0] == "aim":
        wc.set_aiming(a[1] == "1")
    elif a[0] == "aw":
        d = unreal.load_asset("/Game/NeonVeil/Data/Weapons/DA_Weapon_Baton")
        v = [float(x) for x in a[1:7]]
        d.set_editor_property("arms_weapon_offset", unreal.Transform(unreal.Vector(*v[:3]), unreal.Rotator(roll=v[5], pitch=v[3], yaw=v[4]), unreal.Vector(1, 1, 1)))
        cur = wc.get_current_slot_index()
        wc.holster()
        wc.equip_slot(cur)
        OUT.append("aw %s" % v)
    elif a[0] == "slow":   # slow F: stretch every swing by F (for screenshots); slow 1 restores
        f = float(a[1])
        base = {"baton": 0.6, "bash": 0.55, "fist": 0.42}
        mc.set_editor_property("swing_time", base["baton"] * f)
        for k, prop in (("bash", "gun_bash"), ("fist", "fist")):
            pr = mc.get_editor_property(prop)
            pr.set_editor_property("swing_time", base[k] * f)
            pr.set_editor_property("wind_up", 0.1 * f)
            mc.set_editor_property(prop, pr)
        mc.set_editor_property("wind_up", 0.12 * f)
        pawn.set_editor_property("fist_punch_rate", 1.25 / f)
        OUT.append("slow %s" % f)
    elif a[0] == "fistoff":
        pawn.set_editor_property("fist_viewmodel_offset", unreal.Vector(*[float(x) for x in a[1:4]]))
    elif a[0] == "shot":
        path = os.path.join(SHOTS, a[1] + ".png").replace("\\", "/")
        unreal.SystemLibrary.execute_console_command(w, 'HighResShot 1280x720 filename="%s"' % path, pc)
        OUT.append("shot " + path)
    elif a[0] == "state":
        cw = wc.get_current_weapon()
        OUT.append("weapon %s slot %d slots %d" % (cw.get_name() if cw else None, wc.get_current_slot_index(), len(wc.get_slots())))
        for c in pawn.get_components_by_class(unreal.PrimitiveComponent):
            if c.get_name() in ("FirstPersonMesh", "WeaponMesh", "WeaponStaticMesh", "BatonMesh"):
                OUT.append("  %s visible=%s hidden=%s parent=%s" % (c.get_name(), c.is_visible(), c.get_editor_property("hidden_in_game"),
                           c.get_attach_parent().get_name() if c.get_attach_parent() else None))
open(unreal.Paths.project_saved_dir() + "NV_pie_melee.txt", "w").write("\n".join(OUT))
