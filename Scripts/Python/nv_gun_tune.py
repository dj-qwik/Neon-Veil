"""Live viewmodel tuning: applies Saved/NV_tune.txt to weapon data assets (works during PIE; the viewmodel reads
the data every tick). Line format:  DA_Weapon_VX9 hip 34 10 -11 | ads 24 0 -7.6 | scale 0.6 | yaw -90 | muzzle 0 19 5"""
import unreal
V = unreal.Vector
out = []
for line in open(unreal.Paths.project_saved_dir() + "NV_tune.txt").read().splitlines():
    line = line.strip()
    if not line or line.startswith("#"):
        continue
    name, rest = line.split(" ", 1)
    w = unreal.load_asset("/Game/NeonVeil/Data/Weapons/" + name)
    for part in rest.split("|"):
        f = part.split()
        k, nums = f[0], [float(x) for x in f[1:]]
        if k == "hip":
            w.set_editor_property("viewmodel_hip_offset", V(*nums))
        elif k == "ads":
            w.set_editor_property("viewmodel_ads_offset", V(*nums))
        elif k == "scale":
            w.set_editor_property("viewmodel_scale", V(nums[0], nums[0], nums[0]))
        elif k == "yaw":
            r = w.get_editor_property("viewmodel_rotation")
            w.set_editor_property("viewmodel_rotation", unreal.Rotator(roll=r.roll, pitch=r.pitch, yaw=nums[0]))
        elif k == "pitch":
            r = w.get_editor_property("viewmodel_rotation")
            w.set_editor_property("viewmodel_rotation", unreal.Rotator(roll=r.roll, pitch=nums[0], yaw=r.yaw))
        elif k == "roll":
            r = w.get_editor_property("viewmodel_rotation")
            w.set_editor_property("viewmodel_rotation", unreal.Rotator(roll=nums[0], pitch=r.pitch, yaw=r.yaw))
        elif k == "muzzle":
            w.set_editor_property("muzzle_offset", V(*nums))
    unreal.EditorAssetLibrary.save_loaded_asset(w, only_if_is_dirty=False)
    out.append("tuned " + name)
open(unreal.Paths.project_saved_dir() + "NV_gun_tune.txt", "w").write("\n".join(out))
