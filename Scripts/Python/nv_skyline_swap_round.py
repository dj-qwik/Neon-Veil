"""Replace the 8 round CHC_A01 towers (window-light pattern spirals around the cylinder) with the CHJ_B01 / CHE_B01
designs already in the skyline (windows stack per floor). Same transform, alternate designs.
Report: Saved/NV_skyline_swap_round.txt"""
import unreal
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
out = []
acts = list(EAS.get_all_level_actors())
cls = {}
for a in acts:
    n = a.get_class().get_name()
    if n in ("BPP_Bldg_Hero_Tower_CHJ_B01_N1_C", "BPP_Bldg_Hero_Tower_CHE_B01_N1_C"):
        cls[n] = a.get_class()
designs = [cls[k] for k in sorted(cls)]
out.append("designs %s" % [d.get_name() for d in designs])
i = 0
for a in acts:
    if a.get_class().get_name() != "BPP_Bldg_Hero_Tower_CHC_A01_N1_C":
        continue
    t = a.get_actor_transform()
    label = a.get_actor_label()
    c = designs[i % len(designs)]
    n = EAS.spawn_actor_from_class(c, t.translation, t.rotation.rotator())
    n.set_actor_scale3d(t.scale3d)
    n.set_actor_label(label.replace("CHC_A01", c.get_name()[20:27]))
    n.set_folder_path("Skyline_CS")
    out.append("%s -> %s" % (label, n.get_actor_label()))
    EAS.destroy_actor(a)
    i += 1
out.append("swapped %d" % i)
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
open(unreal.Paths.project_saved_dir() + "NV_skyline_swap_round.txt", "w").write("\n".join(out))
