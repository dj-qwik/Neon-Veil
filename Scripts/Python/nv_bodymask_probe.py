"""Body-mask hookup: body mesh materials + parameters, and every outfit body-mask texture. Report: Saved/NV_bodymask.txt"""
import unreal
AR = unreal.AssetRegistryHelpers.get_asset_registry()
MEL = unreal.MaterialEditingLibrary
out = []
b = unreal.load_asset("/MetaHumanCrowdContent/Characters/Assembled/AverageFemale_Head01/Body/SKM_MHC_AverageFemale_Head01_BodyMesh")
for s in b.get_editor_property("materials"):
    mi = s.material_interface
    out.append(f"slot {s.material_slot_name}: {mi.get_path_name() if mi else None}")
    if mi:
        for kind, fn in (("tex", MEL.get_texture_parameter_names), ("scal", MEL.get_scalar_parameter_names), ("vec", MEL.get_vector_parameter_names), ("sw", MEL.get_static_switch_parameter_names)):
            try:
                names = fn(mi.get_base_material() if hasattr(mi, "get_base_material") else mi)
                out.append(f"   {kind}: {[str(n) for n in names]}")
            except Exception as e:
                out.append(f"   {kind} err {e}")
        if isinstance(mi, unreal.MaterialInstanceConstant):
            for tp in mi.get_editor_property("texture_parameter_values"):
                out.append(f"   set tex {tp.parameter_info.name} = {tp.parameter_value.get_name() if tp.parameter_value else None}")
f = unreal.ARFilter(package_paths=["/MetaHumanCrowdContent/Outfits"], recursive_paths=True, class_paths=[unreal.TopLevelAssetPath("/Script/Engine", "Texture2D")])
for ad in AR.get_assets(f):
    if "bodymask" in str(ad.asset_name).lower():
        out.append(f"mask {ad.package_name}")
open(unreal.Paths.project_saved_dir() + "NV_bodymask.txt", "w").write("\n".join(out))
