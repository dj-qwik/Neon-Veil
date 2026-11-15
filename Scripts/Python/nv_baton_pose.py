"""Baton rest pose: low (just above the waist) and to the right, the tip pointing forward and out, away from the body.
argv[-1] (optional): "hx hy hz gx gy gz pitch yaw roll" = viewmodel hip offset + grip on ik_hand_gun. Saves DA_Weapon_Baton.
Report: Saved/NV_baton_pose.txt"""
import sys, unreal
V = unreal.Vector
v = [12.0, 9.0, 12.0, 0.0, 2.0, -11.0, 15.0, 0.0, 68.0]
if len(sys.argv) > 1 and len(sys.argv[-1].split()) == 9:
    v = [float(x) for x in sys.argv[-1].split()]
d = unreal.load_asset("/Game/NeonVeil/Data/Weapons/DA_Weapon_Baton")
d.set_editor_property("viewmodel_hip_offset", V(*v[0:3]))
d.set_editor_property("arms_weapon_offset", unreal.Transform(V(*v[3:6]), unreal.Rotator(roll=v[8], pitch=v[6], yaw=v[7]), V(1, 1, 1)))
ok = unreal.EditorAssetLibrary.save_loaded_asset(d, only_if_is_dirty=False)
open(unreal.Paths.project_saved_dir() + "NV_baton_pose.txt", "w").write("saved %s %s" % (ok, v))
