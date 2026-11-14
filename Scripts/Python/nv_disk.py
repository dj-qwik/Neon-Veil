"""Free space + big cache folders. Report: Saved/NV_disk.txt"""
import os, shutil
import unreal
def du(p):
    t = 0
    for r, _, fs in os.walk(p):
        for f in fs:
            try:
                t += os.path.getsize(os.path.join(r, f))
            except OSError:
                pass
    return t / 1024 ** 3
out = []
for d in ("C:\\", "D:\\", "E:\\"):
    if os.path.exists(d):
        u = shutil.disk_usage(d)
        out.append("%s free %.1f GB of %.1f GB" % (d, u.free / 1024 ** 3, u.total / 1024 ** 3))
home = os.path.expanduser("~").replace("\\Documents", "")
for p in ("C:/ProgramData/Epic/EpicGamesLauncher/VaultCache", "C:/ProgramData/Epic/EpicGamesLauncher/Data/Manifests",
          home + "/AppData/Local/UnrealEngine/Common/DerivedDataCache", home + "/AppData/Local/UnrealEngine/Common/Zen",
          home + "/AppData/Local/UnrealEngine", "C:/ProgramData/Epic/UnrealEngine", home + "/AppData/Local/Temp",
          "C:/Users/djqwi/Documents/Unreal Projects/GameAnimationSample", "C:/Users/djqwi/Documents/Unreal Projects/InfimaFPS",
          "C:/Users/djqwi/Documents/Unreal Projects/NeonVeil/DerivedDataCache", "C:/Users/djqwi/Documents/Unreal Projects/NeonVeil/Intermediate",
          "C:/Users/djqwi/Documents/Unreal Projects/NeonVeil/Saved"):
    if os.path.isdir(p):
        out.append("%-80s %7.2f GB" % (p, du(p)))
    else:
        out.append("%-80s missing" % p)
vc = "C:/ProgramData/Epic/EpicGamesLauncher/VaultCache"
if os.path.isdir(vc):
    for n in sorted(os.listdir(vc)):
        out.append("   vault %-50s %6.2f GB" % (n, du(os.path.join(vc, n))))
open(unreal.Paths.project_saved_dir() + "NV_disk.txt", "w").write("\n".join(out))
