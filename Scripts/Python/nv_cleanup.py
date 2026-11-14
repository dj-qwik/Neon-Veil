"""Disk cleanup. argv: 'check' (default) reports, 'delete' removes.
In-project: /Game folders nothing outside them references (checked per package with the asset registry, so
world-partition external actors count too). Plus Saved/StagedBuilds and the two leftover source projects
(CitySubwayTrainModular = the NYC subway train, TramStationSrc = the tram station kit's source, already migrated).
Report: Saved/NV_cleanup.txt"""
import os, shutil, sys
import unreal
AR = unreal.AssetRegistryHelpers.get_asset_registry()
EAL = unreal.EditorAssetLibrary
MODE = sys.argv[-1] if sys.argv[-1] in ("check", "delete") else "check"
OUT = []
def log(*a):
    OUT.append(" ".join(str(x) for x in a))
def du(p):
    t = 0
    for r, _, fs in os.walk(p):
        for f in fs:
            try:
                t += os.path.getsize(os.path.join(r, f))
            except OSError:
                pass
    return t / 1024 ** 3

FOLDERS = ["CitySampleVehicles", "SubwayTrain"]
proj = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
opts = unreal.AssetRegistryDependencyOptions(include_soft_package_references=True, include_hard_package_references=True,
                                             include_searchable_names=False, include_soft_management_references=True,
                                             include_hard_management_references=True)
safe = []
for f in FOLDERS:
    root = "/Game/" + f
    pkgs = {str(d.package_name) for d in AR.get_assets_by_path(root, recursive=True)}
    outside = set()
    for p in pkgs:
        for r in AR.get_referencers(unreal.Name(p), opts) or []:
            r = str(r)
            if not r.startswith(root + "/"):
                outside.add(r)
    log("%s: %d packages, %.2f GB, referenced from outside by %d: %s" % (f, len(pkgs), du(os.path.join(proj, "Content", f)),
        len(outside), ", ".join(sorted(outside)[:8])))
    if not outside:
        safe.append(f)

up = os.path.dirname(os.path.normpath(proj))
EXTRA = [os.path.join(proj, "Saved", "StagedBuilds"), os.path.join(up, "CitySubwayTrainModular"), os.path.join(up, "TramStationSrc")]
for p in EXTRA:
    log("%s exists=%s %.2f GB" % (p, os.path.isdir(p), du(p) if os.path.isdir(p) else 0))

if MODE == "delete":
    for f in safe:
        # Straight off disk: going through the asset tools loads (and Nanite-builds) every mesh first, which
        # needed more memory than the machine has. Nothing references these, so the registry just drops them.
        disk = os.path.join(proj, "Content", f)
        if os.path.isdir(disk):
            shutil.rmtree(disk, ignore_errors=True)
        log("deleted /Game/%s on disk -> %s" % (f, "gone" if not os.path.isdir(disk) else "PARTIAL"))
    for p in EXTRA:
        if os.path.isdir(p):
            shutil.rmtree(p, ignore_errors=True)
            log("deleted", p, "->", "gone" if not os.path.isdir(p) else "PARTIAL (files in use?)")
open(unreal.Paths.project_saved_dir() + "NV_cleanup.txt", "w").write("\n".join(OUT))
