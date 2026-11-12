"""Probe: Director BP components/anim setup, retargeters, idle anims, antechamber glass. Report: Saved/NV_mh_probe4.txt"""
import unreal
AR = unreal.AssetRegistryHelpers.get_asset_registry()
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
out = []
bp = unreal.load_asset("/Game/NeonVeil/Characters/Director/Director/BP_Director")
cdo = unreal.get_default_object(bp.generated_class())
SDS = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
BFL = unreal.SubobjectDataBlueprintFunctionLibrary
for h in SDS.k2_gather_subobject_data_for_blueprint(bp):
    o = BFL.get_object(BFL.get_data(h))
    line = f"comp {o.get_name()} {o.get_class().get_name()}"
    if isinstance(o, unreal.SkeletalMeshComponent):
        m = o.get_editor_property("skeletal_mesh_asset")
        line += f" mesh={m.get_path_name() if m else None} skel={m.get_editor_property('skeleton').get_path_name() if m else None}"
        line += f" animmode={o.get_editor_property('animation_mode')} animclass={o.get_editor_property('anim_class')}"
    out.append(line)
for cls, mod in (("IKRetargeter", "/Script/IKRig"), ("AnimSequence", "/Script/Engine"), ("Skeleton", "/Script/Engine")):
    for a in AR.get_assets(unreal.ARFilter(class_paths=[unreal.TopLevelAssetPath(mod, cls)])):
        p = str(a.package_name)
        if cls != "AnimSequence" or any(k in p.lower() for k in ("idle", "metahuman", "mm_", "stand")):
            out.append(f"{cls}: {p}")
for a in EAS.get_all_level_actors():
    o, e = a.get_actor_bounds(False)
    if o.x + e.x > 15800 and o.x - e.x < 17500 and abs(o.y) < 2000:
        smc = a.get_component_by_class(unreal.StaticMeshComponent)
        mats = [m.get_path_name() for m in smc.get_materials() if m] if smc else []
        out.append(f"E: {a.get_actor_label()} o=({o.x:.0f},{o.y:.0f},{o.z:.0f}) e=({e.x:.0f},{e.y:.0f},{e.z:.0f}) {mats}")
g = unreal.load_asset("/Game/NeonVeil/Materials/Art/MI_DIR_DarkGlass")
if g:
    par = g.get_editor_property("parent")
    out.append(f"DarkGlass parent {par.get_path_name()} blend={par.get_editor_property('blend_mode') if hasattr(par,'get_editor_property') else '?'}")
with open(unreal.Paths.project_saved_dir() + "NV_mh_probe4.txt", "w", encoding="utf-8") as fh:
    fh.write("\n".join(out))
