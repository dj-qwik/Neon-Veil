"""Survey for the NPC / guard / cleanup pass. Report: Saved/NV_survey_cleanup.txt
- rain fields in the open map
- top-level /Game folders: size on disk, and whether anything the game uses (dependency closure of /Game/NeonVeil
  plus every map under it) reaches into them
- skeletal meshes per pack (NPC candidates)
- disk sizes of the project's own build folders and sibling projects"""
import os, collections
import unreal
AR = unreal.AssetRegistryHelpers.get_asset_registry()
OUT = []
def log(*a):
    OUT.append(" ".join(str(x) for x in a))

def du(path):
    tot = 0
    for root, _, files in os.walk(path):
        for f in files:
            try:
                tot += os.path.getsize(os.path.join(root, f))
            except OSError:
                pass
    return tot
GB = 1024 ** 3

EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for a in EAS.get_all_level_actors():
    if a.get_class().get_name() == "NVRainField":
        log("rain", a.get_actor_label(), a.get_editor_property("count"))

proj = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
content = os.path.join(proj, "Content")
log("== project folders")
for d in ("Content", "Saved", "Intermediate", "DerivedDataCache", "Binaries", "Build", "Plugins"):
    p = os.path.join(proj, d)
    if os.path.isdir(p):
        log("  %-18s %6.2f GB" % (d, du(p) / GB))
for d in ("Saved/Logs", "Saved/Autosaves", "Saved/Crashes", "Saved/NV_shots", "Saved/Trailer", "Saved/MusicReview", "Saved/VO_raw",
          "Saved/Backup", "Saved/Collections", "Saved/Config", "Saved/StagedBuilds", "Saved/ShaderDebugInfo"):
    p = os.path.join(proj, d)
    if os.path.isdir(p):
        log("  %-18s %6.2f GB" % (d, du(p) / GB))

# dependency closure of what the game uses
opts = unreal.AssetRegistryDependencyOptions(include_soft_package_references=True, include_hard_package_references=True,
                                             include_searchable_names=False, include_soft_management_references=False,
                                             include_hard_management_references=False)
seeds = set()
for d in AR.get_assets_by_path("/Game/NeonVeil", recursive=True):
    seeds.add(str(d.package_name))
# config-referenced (game mode, default maps) live under NeonVeil already; add engine-template content we know is used
for extra in ("/Game/Characters/Mannequins/Meshes/SKM_Manny_Simple", "/Game/Input/IMC_Default"):
    seeds.add(extra)
seen, stack = set(), list(seeds)
while stack:
    p = stack.pop()
    if p in seen:
        continue
    seen.add(p)
    deps = AR.get_dependencies(unreal.Name(p), opts) or []
    for dp in deps:
        s = str(dp)
        if s.startswith("/Game/") and s not in seen:
            stack.append(s)
used = collections.Counter(p.split("/")[2] for p in seen if p.count("/") >= 2)
log("== top-level /Game folders: size, packages used by the game")
rows = []
for name in sorted(os.listdir(content)):
    p = os.path.join(content, name)
    if os.path.isdir(p):
        rows.append((du(p), name))
for size, name in sorted(rows, reverse=True):
    total = len(AR.get_assets_by_path("/Game/" + name, recursive=True))
    log("  %-34s %6.2f GB  assets %5d  used %5d" % (name, size / GB, total, used.get(name, 0)))

log("== skeletal meshes (NPC candidates)")
f = unreal.ARFilter(class_paths=[unreal.TopLevelAssetPath("/Script/Engine", "SkeletalMesh")], recursive_classes=True)
by = collections.defaultdict(list)
for d in AR.get_assets(f):
    pk = str(d.package_name)
    if pk.startswith("/Game/"):
        by["/".join(pk.split("/")[:3])].append(pk.split("/")[-1])
for k in sorted(by):
    v = by[k]
    log("  %s (%d): %s" % (k, len(v), ", ".join(sorted(v)[:25])))
f = unreal.ARFilter(class_paths=[unreal.TopLevelAssetPath("/Script/Engine", "Blueprint")], package_paths=["/Game"], recursive_paths=True)
mh = [str(d.package_name) for d in AR.get_assets(f) if "/MetaHumans/" in str(d.package_name) or str(d.asset_name).startswith("BP_") and "MH" in str(d.package_name)]
log("  metahuman-ish BPs:", ", ".join(mh[:30]))

log("== sibling projects")
up = os.path.dirname(os.path.normpath(proj))
for name in sorted(os.listdir(up)):
    p = os.path.join(up, name)
    if os.path.isdir(p) and name != os.path.basename(os.path.normpath(proj)):
        log("  %-28s %6.2f GB" % (name, du(p) / GB))
open(unreal.Paths.project_saved_dir() + "NV_survey_cleanup.txt", "w").write("\n".join(OUT))
