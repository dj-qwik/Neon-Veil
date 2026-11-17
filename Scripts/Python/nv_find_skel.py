"""List skeletal meshes in the project (name, skeleton, bounds, material slots) to pick hologram target bodies."""
import unreal
AR = unreal.AssetRegistryHelpers.get_asset_registry()
out = []
f = unreal.ARFilter(class_paths=[unreal.TopLevelAssetPath("/Script/Engine", "SkeletalMesh")], package_paths=["/Game"], recursive_paths=True)
for d in AR.get_assets(f):
    p = str(d.package_name)
    if p.startswith("/Game/MetaHumans") or "/Outfits/" in p:
        continue
    out.append(p)
out.sort()
lines = []
for p in out:
    sm = unreal.load_asset(p)
    sk = sm.get_editor_property("skeleton")
    b = sm.get_bounds()
    lines.append("%s | skel=%s | ext=%s | slots=%d" % (p, sk.get_path_name() if sk else None,
                 (round(b.box_extent.x), round(b.box_extent.y), round(b.box_extent.z)), len(sm.get_editor_property("materials"))))
# idle-ish anims on the template Manny skeleton
fa = unreal.ARFilter(class_paths=[unreal.TopLevelAssetPath("/Script/Engine", "AnimSequence")], package_paths=["/Game/Characters/Mannequins/Anims"], recursive_paths=True)
for d in AR.get_assets(fa):
    n = str(d.asset_name)
    if "Idle" in n or "Aim" in n:
        lines.append("ANIM " + str(d.package_name))
open(unreal.Paths.project_saved_dir() + "NV_find_skel.txt", "w").write("\n".join(lines))
