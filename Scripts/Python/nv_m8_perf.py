"""NEON VEIL - M8 performance fixes (no visual change).

 - Skyline_CS (City Sample packed-level towers, ~500k instances, all far out of reach):
   no collision, no overlap events, no navigation relevance. They were each creating physics
   bodies at load (4.8 s of physics work on the first packaged frame).
 - Traffic + rain (FX_Atmosphere): no overlap events on purely visual meshes.
Report: Saved/NV_m8_perf.txt
"""
import unreal

REPORT = []
def log(*a):
    msg = " ".join(str(x) for x in a)
    REPORT.append(msg)
    unreal.log("[NV M8 perf] " + msg)

EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
LES = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
VISUAL_FOLDERS = ("Skyline_CS", "FX_Atmosphere")

def strip(comp):
    comp.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    comp.set_collision_profile_name("NoCollision")
    comp.set_editor_property("generate_overlap_events", False)
    comp.set_editor_property("can_ever_affect_navigation", False)

def main():
    actors = comps = insts = 0
    for a in EAS.get_all_level_actors():
        folder = str(a.get_folder_path())
        if not folder.startswith(VISUAL_FOLDERS):
            continue
        actors += 1
        for c in a.get_components_by_class(unreal.PrimitiveComponent):
            if not isinstance(c, (unreal.StaticMeshComponent, unreal.ShapeComponent)):
                continue
            strip(c)
            comps += 1
            if isinstance(c, unreal.InstancedStaticMeshComponent):
                insts += c.get_instance_count()
    log(f"visual-only actors {actors}, components {comps}, instances {insts}: collision off")
    LES.save_current_level()

try:
    main()
finally:
    with open(unreal.Paths.project_saved_dir() + "NV_m8_perf.txt", "w", encoding="utf-8") as fh:
        fh.write("\n".join(REPORT))
