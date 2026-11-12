"""NEON VEIL - M8: strip collision from the City Sample packed-level tower Blueprints used by the skyline.
The towers are far out of reach; their ISMs were creating ~508k physics bodies (load stall + multi-second
Chaos acceleration-structure rebuilds). Per-instance overrides don't stick because packed-level actors rebuild
their components, so this edits the Blueprint component templates. Local Fab content (gitignored).
Report: Saved/NV_m8_skyline_bp.txt"""
import unreal

REPORT = []
def log(*a):
    msg = " ".join(str(x) for x in a)
    REPORT.append(msg)
    unreal.log("[NV M8 skyline bp] " + msg)

EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
SDS = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
BFL = unreal.SubobjectDataBlueprintFunctionLibrary

def strip(comp):
    comp.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    comp.set_collision_profile_name("NoCollision")
    comp.set_editor_property("generate_overlap_events", False)
    comp.set_editor_property("can_ever_affect_navigation", False)

def main():
    classes = {}
    for a in EAS.get_all_level_actors():
        if str(a.get_folder_path()) == "Skyline_CS":
            classes[a.get_class().get_path_name()] = a.get_class()
    log("tower classes", len(classes))
    for path, cls in classes.items():
        bp_path = path.rsplit(".", 1)[0]
        bp = unreal.load_asset(bp_path)
        if not bp:
            log("could not load", bp_path)
            continue
        n = 0
        for h in SDS.k2_gather_subobject_data_for_blueprint(bp):
            data = BFL.get_data(h)
            obj = BFL.get_object(data)
            if isinstance(obj, unreal.StaticMeshComponent):
                strip(obj)
                n += 1
        unreal.BlueprintEditorLibrary.compile_blueprint(bp)
        unreal.EditorAssetLibrary.save_loaded_asset(bp, only_if_is_dirty=False)
        log(bp_path, "components stripped", n)
    # refresh placed instances so the level picks up the new templates, then verify
    bodies = 0
    for a in EAS.get_all_level_actors():
        if str(a.get_folder_path()) != "Skyline_CS":
            continue
        a.rerun_construction_scripts() if hasattr(a, "rerun_construction_scripts") else None
        for c in a.get_components_by_class(unreal.StaticMeshComponent):
            if c.get_collision_enabled() != unreal.CollisionEnabled.NO_COLLISION:
                bodies += c.get_instance_count() if isinstance(c, unreal.InstancedStaticMeshComponent) else 1
    log("skyline bodies still with collision:", bodies)
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()

try:
    main()
finally:
    with open(unreal.Paths.project_saved_dir() + "NV_m8_skyline_bp.txt", "w", encoding="utf-8") as fh:
        fh.write("\n".join(REPORT))
