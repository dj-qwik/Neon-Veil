"""Director polish: charcoal wardrobe, symmetric key light at the glass plane, texture budget.
Report: Saved/NV_m9_director_polish.txt"""
import unreal

REPORT = []
def log(*a):
    msg = " ".join(str(x) for x in a)
    REPORT.append(msg)
    unreal.log("[NV director polish] " + msg)

EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
EAL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary
AR = unreal.AssetRegistryHelpers.get_asset_registry()
DIR = "/Game/NeonVeil/Characters/Director"
CHARCOAL = unreal.LinearColor(0.028, 0.030, 0.034, 1.0)

def textures():
    n = 0
    for a in AR.get_assets(unreal.ARFilter(package_paths=[DIR], recursive_paths=True,
                                           class_paths=[unreal.TopLevelAssetPath("/Script/Engine", "Texture2D")])):
        t = unreal.load_asset(str(a.package_name))
        name = t.get_name().lower()
        cap = 2048 if any(k in name for k in ("face", "head")) else 1024
        if t.get_editor_property("max_texture_size") != cap:
            t.set_editor_property("max_texture_size", cap)
            EAL.save_loaded_asset(t, only_if_is_dirty=False)
            n += 1
    log("textures capped", n)

def wardrobe():
    mesh = unreal.load_asset(f"{DIR}/Director/Clothing/MHC_Director_Outfits")
    done = set()
    for sm in mesh.get_editor_property("materials"):
        mi = sm.get_editor_property("material_interface")
        if not mi or mi.get_path_name() in done:
            continue
        done.add(mi.get_path_name())
        log("outfit material", mi.get_path_name(), type(mi).__name__)
        if isinstance(mi, unreal.MaterialInstanceConstant) and mi.get_path_name().startswith(DIR):
            vparams = MEL.get_vector_parameter_names(mi)
            sparams = MEL.get_scalar_parameter_names(mi)
            log("   vector params", [str(p) for p in vparams])
            log("   scalar params", [str(p) for p in sparams][:40])
            for p in vparams:
                s = str(p).lower()
                if any(k in s for k in ("color", "tint", "albedo", "diffuse")) and not any(k in s for k in ("spec", "sheen", "emiss", "subsurface")):
                    MEL.set_material_instance_vector_parameter_value(mi, p, CHARCOAL)
                    log("   set", str(p), "-> charcoal")
            EAL.save_loaded_asset(mi, only_if_is_dirty=False)

def light():
    for a in EAS.get_all_level_actors():
        if a.get_actor_label() == "E_DirectorKey":
            EAS.destroy_actor(a)
    l = EAS.spawn_actor_from_class(unreal.PointLight, unreal.Vector(16400, 320, 255), unreal.Rotator())
    lc = l.point_light_component
    lc.set_editor_property("intensity_units", unreal.LightUnits.LUMENS)
    lc.set_editor_property("intensity", 1100.0)
    lc.set_editor_property("attenuation_radius", 420.0)
    lc.set_editor_property("source_radius", 25.0)
    lc.set_editor_property("use_temperature", True)
    lc.set_editor_property("temperature", 5600.0)
    lc.set_editor_property("cast_shadows", False)
    l.set_actor_label("E_DirectorKey")
    l.set_folder_path("E_Director")
    log("key light at glass plane")

try:
    textures()
    wardrobe()
    light()
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
finally:
    with open(unreal.Paths.project_saved_dir() + "NV_m9_director_polish.txt", "w", encoding="utf-8") as fh:
        fh.write("\n".join(REPORT))
