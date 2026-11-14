"""Third-person weapon setup for Ghost-7's body animation: hold type per weapon and (optionally) grip / left-hand data.
Grip lines come from the NVBodyInfo probe (first-person KINEMATION rig holding the same gun, same Manny hand bones).
Report: Saved/NV_ghost7_weapons_tp.txt"""
import unreal
OUT = []
EAL = unreal.EditorAssetLibrary
D = "/Game/NeonVeil/Data/Weapons/"
# name: (hold, grip (loc, rot) or None, left-hand point (weapon space) or None)
# Grips measured in PIE with NVBodyInfo from the first-person KINEMATION arms (loc cm, rot P/Y/R deg); the VX-9 is drawn
# at 0.6 scale in first person, so its offset is scaled back up for a full-size third-person gun.
CFG = {
    # VX-9 revolver: full size reads oversized in Ghost's hand, so 0.75 (offset scaled to keep the same grip point).
    "DA_Weapon_VX9": ("PISTOL", ((-13.140 * 0.75 / 0.6, 2.744 * 0.75 / 0.6, 2.497 * 0.75 / 0.6), (15.72, 80.19, -2.85), 0.75), None),
    "DA_Weapon_Kestrel": ("RIFLE", ((-11.484, 3.823, 7.540), (2.41, 79.74, 8.95)), (4.949, 3.417, -2.279)),
    "DA_Weapon_ARX": ("RIFLE", ((-17.867, 5.887, 3.404), (15.51, 73.71, 6.60)), (3.725, 1.549, -7.056)),
    "DA_Weapon_TP12": ("RIFLE", ((-13.008, 1.593, 12.631), (15.20, 74.16, -0.14)), (4.570, 16.540, -13.819)),
    "DA_Weapon_Harrow": ("RIFLE", None, None),
}
for name, (hold, grip, left) in CFG.items():
    w = unreal.load_asset(D + name)
    if not w:
        OUT.append(f"{name}: missing")
        continue
    w.set_editor_property("hold_type", getattr(unreal.NVWeaponHold, hold))
    if grip:
        loc, rot = grip[0], grip[1]
        sc = grip[2] if len(grip) > 2 else 1.0
        w.set_editor_property("third_person_grip", unreal.Transform(unreal.Vector(*loc), unreal.Rotator(roll=rot[2], pitch=rot[0], yaw=rot[1]), unreal.Vector(sc, sc, sc)))
    if left:
        w.set_editor_property("third_person_left_hand", unreal.Vector(*left))
    EAL.save_loaded_asset(w, only_if_is_dirty=False)
    OUT.append(f"{name}: hold={w.get_editor_property('hold_type')} grip={w.get_editor_property('third_person_grip')} left={w.get_editor_property('third_person_left_hand')}")
open(unreal.Paths.project_saved_dir() + "NV_ghost7_weapons_tp.txt", "w").write("\n".join(str(x) for x in OUT))
