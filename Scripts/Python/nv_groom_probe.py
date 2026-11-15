import unreal
AR = unreal.AssetRegistryHelpers.get_asset_registry()
O = []
root = "/MetaHumanCharacter/Optional/Grooms"
for ad in AR.get_assets(unreal.ARFilter(package_paths=[root], recursive_paths=True)):
    c = str(ad.asset_class_path.asset_name)
    if c in ("Texture2D", "MaterialInstanceConstant"): continue
    O.append(f"{c} {ad.package_name}")
O.sort()
b = unreal.load_asset(root + "/Bindings/Hair/Hair_M_BobStraight_Binding")
if b:
    for prop in ("groom", "target_skeletal_mesh", "source_skeletal_mesh", "binding_type", "num_interpolation_points"):
        try: O.append(f"binding {prop} = {b.get_editor_property(prop)}")
        except Exception as e: O.append(f"binding {prop} err {e}")
    try:
        g = b.get_editor_property("groom")
        O.append(f"groom lods: {[ (l.get_editor_property('geometry_type')) for l in g.get_editor_property('lod') ] if g else None}")
    except Exception as e: O.append(f"lod err {e}")
open(unreal.Paths.project_saved_dir() + "NV_groom_probe.txt", "w").write("\n".join(O))
