"""Find explosion / fire / smoke / tracer Niagara systems, explosion, siren, gunshot and engine sounds, and hover-car
mesh bounds for the tram chase event. Saved/NV_find_fx.txt"""
import unreal
AR = unreal.AssetRegistryHelpers.get_asset_registry()
out = []
KEYS = ("explo", "fire", "smoke", "spark", "tracer", "debris", "blast", "siren", "police", "gunshot", "shot", "engine",
        "flyby", "fly_by", "whoosh", "impact", "burst", "laser")
for cls in (("/Script/Niagara", "NiagaraSystem"), ("/Script/Engine", "SoundWave"), ("/Script/Engine", "SoundCue"),
            ("/Script/MetasoundEngine", "MetaSoundSource")):
    f = unreal.ARFilter(class_paths=[unreal.TopLevelAssetPath(cls[0], cls[1])], package_paths=["/Game"], recursive_paths=True)
    for d in AR.get_assets(f):
        n = str(d.asset_name).lower()
        if any(k in n for k in KEYS):
            out.append("%s %s" % (cls[1], d.package_name))
for p in ("SM_NV_HoverCar", "SM_NV_HoverCar_Wedge", "SM_NV_HoverCar_Hauler"):
    m = unreal.load_asset("/Game/NeonVeil/Vehicles/" + p)
    b = m.get_bounds()
    out.append("MESH %s origin %s ext %s slots %s" % (p, b.origin, b.box_extent, [s.get_editor_property("material_slot_name") for s in m.get_editor_property("static_materials")]))
open(unreal.Paths.project_saved_dir() + "NV_find_fx.txt", "w").write("\n".join(out))
