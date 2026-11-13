"""Second round-tower pass: CHE_B01 is also a cylinder (window pattern spirals), so swap every CHE_B01
for the square-plan CHJ_A01 / CHJ_B01 designs. Same transform, alternating designs.
Report: Saved/NV_skyline_swap_round2.txt"""
import unreal
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
out = []
acts = list(EAS.get_all_level_actors())
cls = {}
for a in acts:
    n = a.get_class().get_name()
    if n in ("BPP_Bldg_Hero_Tower_CHJ_A01_N1_C", "BPP_Bldg_Hero_Tower_CHJ_B01_N1_C"):
        cls[n] = a.get_class()
designs = [cls[k] for k in sorted(cls)]
out.append("designs %s" % [d.get_name() for d in designs])
i = 0
for a in acts:
    if a.get_class().get_name() not in ("BPP_Bldg_Hero_Tower_CHE_B01_N1_C", "BPP_Bldg_Hero_Tower_CHC_A01_N1_C"):
        continue
    t = a.get_actor_transform()
    label = a.get_actor_label()
    folder = a.get_folder_path()
    c = designs[i % len(designs)]
    n = EAS.spawn_actor_from_class(c, t.translation, t.rotation.rotator())
    n.set_actor_scale3d(t.scale3d)
    n.set_actor_label("CS_Tower_%s_%02d" % (c.get_name()[20:27], i))
    n.set_folder_path(folder)
    out.append("%s -> %s" % (label, n.get_actor_label()))
    EAS.destroy_actor(a)
    i += 1
out.append("swapped %d" % i)
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
open(unreal.Paths.project_saved_dir() + "NV_skyline_swap_round2.txt", "w").write("\n".join(out))
