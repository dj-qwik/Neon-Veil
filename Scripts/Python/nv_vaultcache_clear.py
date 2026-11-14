"""Clear the Epic launcher's VaultCache (downloaded pack archives; re-downloadable from Fab). Report: Saved/NV_vault.txt"""
import os, shutil
import unreal
vc = "C:/ProgramData/Epic/EpicGamesLauncher/VaultCache"
out = []
before = shutil.disk_usage("C:\\").free
if os.path.isdir(vc):
    for n in os.listdir(vc):
        p = os.path.join(vc, n)
        shutil.rmtree(p, ignore_errors=True) if os.path.isdir(p) else os.remove(p)
        out.append("%s -> %s" % (n, "gone" if not os.path.exists(p) else "LEFT (in use?)"))
after = shutil.disk_usage("C:\\").free
out.append("freed %.1f GB, C: free now %.1f GB" % ((after - before) / 1024 ** 3, after / 1024 ** 3))
open(unreal.Paths.project_saved_dir() + "NV_vault.txt", "w").write("\n".join(out))
