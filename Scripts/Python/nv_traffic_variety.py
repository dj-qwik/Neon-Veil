"""Mixes the three hover-car designs and two hover-pad colours (cyan / magenta) into every NVTrafficStream of the
prologue and the Glass Crown maps (needs the NVTrafficStream ExtraMeshes/AccentMaterials build and the assets from
nv_hovercar_variants.py). Idempotent; saves. Report: Saved/NV_traffic_variety.txt"""
import unreal
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
LES = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
D = "/Game/NeonVeil/Vehicles"
OUT = []
extra = [unreal.load_asset(f"{D}/SM_NV_HoverCar_Wedge"), unreal.load_asset(f"{D}/SM_NV_HoverCar_Hauler")]
accents = [unreal.load_asset(f"{D}/MI_NV_CarThruster"), unreal.load_asset(f"{D}/MI_NV_CarThruster_Magenta")]
OUT.append(f"assets: {[a.get_name() if a else None for a in extra + accents]}")
for MAP in ("/Game/NeonVeil/Maps/M00/L_M00_Prologue", "/Game/NeonVeil/Maps/M00/L_M00_GlassCrown"):
    LES.load_level(MAP)
    n = 0
    for a in EAS.get_all_level_actors():
        if isinstance(a, unreal.NVTrafficStream):
            a.set_editor_property("extra_meshes", [m for m in extra if m])
            a.set_editor_property("accent_materials", [m for m in accents if m])
            a.set_editor_property("turn_reverse_cars", True)
            n += 1
    LES.save_current_level()
    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    OUT.append(f"{MAP}: {n} streams")
LES.load_level("/Game/NeonVeil/Maps/M00/L_M00_Prologue")
open(unreal.Paths.project_saved_dir() + "NV_traffic_variety.txt", "w").write("\n".join(OUT))
