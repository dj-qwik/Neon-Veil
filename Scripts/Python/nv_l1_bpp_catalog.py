"""Spawn every CitySample packed-level building blueprint (BPP_*) once in a scratch level and record its bounds
(size and origin offset). Report: Saved/NV_l1_bpp_catalog.json"""
import json
import unreal
LES = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
LES.new_level("/Game/NeonVeil/Maps/Tests/L_Scratch_BPP")
AR = unreal.AssetRegistryHelpers.get_asset_registry()
f = unreal.ARFilter(package_paths=["/Game/CitySampleBuildings"], recursive_paths=True,
                    class_paths=[unreal.TopLevelAssetPath("/Script/Engine", "Blueprint")])
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
out = {}
for a in AR.get_assets(f):
    name = str(a.asset_name)
    if not name.startswith("BPP_"):
        continue
    p = str(a.package_name)
    bp = unreal.load_asset(p)
    try:
        act = EAS.spawn_actor_from_object(bp, unreal.Vector(0, 0, 0))
    except Exception as e:
        out[p] = {"error": str(e)}
        continue
    if not act:
        continue
    o, e = act.get_actor_bounds(False)
    out[p] = {"origin": [o.x, o.y, o.z], "extent": [e.x, e.y, e.z]}
    EAS.destroy_actor(act)
open(unreal.Paths.project_saved_dir() + "NV_l1_bpp_catalog.json", "w").write(json.dumps(out))
