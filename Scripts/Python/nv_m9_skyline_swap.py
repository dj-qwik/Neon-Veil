"""Replace skyline towers of one City Sample design (default the NYG 'Ref' blockout, which shows flat untextured
panels) with a finished hero tower at the same transform. Report: Saved/NV_m9_skyline_swap.txt"""
import unreal

FROM = "BPP_NYG_Ref_N1_C"
TO = "/Game/CitySampleBuildings/Building/Library/Kit_Hero_Bldg/LevelInstance/BPP_Bldg_Hero_Tower_CHE_B01_N1"

EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
out = []
bp = unreal.load_asset(TO)
cls = bp.generated_class()
for a in list(EAS.get_all_level_actors()):
    if a.get_class().get_name() != FROM:
        continue
    t = a.get_actor_transform()
    label = a.get_actor_label()
    o, e = a.get_actor_bounds(False)
    n = EAS.spawn_actor_from_class(cls, t.translation, t.rotation.rotator())
    n.set_actor_scale3d(t.scale3d)
    n.set_actor_label(label.replace("NYG_Ref", "Hero_Tower_CHE_B01"))
    n.set_folder_path("Skyline_CS")
    out.append(f"{label} at ({o.x:.0f},{o.y:.0f}) -> {n.get_actor_label()}")
    EAS.destroy_actor(a)
out.append(f"swapped {len(out)}")
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
with open(unreal.Paths.project_saved_dir() + "NV_m9_skyline_swap.txt", "w", encoding="utf-8") as fh:
    fh.write("\n".join(out))
