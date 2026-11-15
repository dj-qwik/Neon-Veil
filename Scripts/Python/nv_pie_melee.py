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
    elif a[0] == "motion":   # motion baton|rifle|pistol wp wy wr wx wy wz sp sy sr sx sy sz [windEnd strikeEnd holdEnd]
        prop = {"baton": "baton_motion", "rifle": "rifle_bash_motion", "pistol": "pistol_bash_motion"}[a[1]]
        f = [float(x) for x in a[2:]]
        m = pawn.get_editor_property(prop)
        m.set_editor_property("wind_rot", unreal.Rotator(pitch=f[0], yaw=f[1], roll=f[2]))
        m.set_editor_property("wind_offset", unreal.Vector(f[3], f[4], f[5]))
        m.set_editor_property("strike_rot", unreal.Rotator(pitch=f[6], yaw=f[7], roll=f[8]))
        m.set_editor_property("strike_offset", unreal.Vector(f[9], f[10], f[11]))
        if len(f) >= 15:
            m.set_editor_property("wind_end", f[12]); m.set_editor_property("strike_end", f[13]); m.set_editor_property("hold_end", f[14])
        pawn.set_editor_property(prop, m)
        OUT.append("motion %s %s" % (a[1], f))
    elif a[0] == "prop":   # prop name float
        pawn.set_editor_property(a[1], float(a[2]))
    elif a[0] == "fistoff":
        pawn.set_editor_property("fist_viewmodel_offset", unreal.Vector(*[float(x) for x in a[1:4]]))
    elif a[0] == "shot":
        path = os.path.join(SHOTS, a[1] + ".png").replace("\\", "/")
        unreal.SystemLibrary.execute_console_command(w, 'HighResShot 1280x720 filename="%s"' % path, pc)
        OUT.append("shot " + path)
    elif a[0] == "state":
        cw = wc.get_current_weapon()
        OUT.append("swing alpha %.3f style %s swinging %s" % (mc.get_swing_alpha(), mc.get_swing_style(), mc.is_swinging()))
        for c in pawn.get_components_by_class(unreal.SceneComponent):
            if c.get_name() == "ViewmodelRoot":
                OUT.append("  vmroot %s" % c.get_relative_transform())
            if c.get_name() == "FirstPersonCamera":
                camt = c.get_world_transform()
        for c in pawn.get_components_by_class(unreal.SceneComponent):
            if c.get_name() in ("WeaponStaticMesh", "WeaponMesh"):
                t = c.get_world_transform()
                g = camt.inverse_transform_location(t.translation)
                tip = camt.inverse_transform_location(t.transform_location(unreal.Vector(0, 0, 40)))
                fwd = camt.inverse_transform_location(t.transform_location(unreal.Vector(0, 40, 0)))
                OUT.append("  %s cam-space grip %s | +Z40 %s | +Y40 %s" % (c.get_name(), g, tip, fwd))
        OUT.append("weapon %s slot %d slots %d" % (cw.get_name() if cw else None, wc.get_current_slot_index(), len(wc.get_slots())))
        for c in pawn.get_components_by_class(unreal.PrimitiveComponent):
            if c.get_name() in ("FirstPersonMesh", "WeaponMesh", "WeaponStaticMesh", "BatonMesh"):
                OUT.append("  %s visible=%s hidden=%s parent=%s" % (c.get_name(), c.is_visible(), c.get_editor_property("hidden_in_game"),
                           c.get_attach_parent().get_name() if c.get_attach_parent() else None))
open(unreal.Paths.project_saved_dir() + "NV_pie_melee.txt", "w").write("\n".join(OUT))
