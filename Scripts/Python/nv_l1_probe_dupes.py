"""Report duplicate actor labels and per-folder counts -> Saved/NV_l1_probe_dupes.txt"""
import collections, unreal
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
acts = EAS.get_all_level_actors()
labels = collections.Counter(a.get_actor_label() for a in acts)
folders = collections.Counter(str(a.get_folder_path()) for a in acts)
out = ["actors %d" % len(acts), "-- folders"] + ["%s %d" % kv for kv in sorted(folders.items()) if kv[1] > 0]
out += ["-- dup labels"] + ["%s x%d" % kv for kv in labels.most_common(60) if kv[1] > 1]
lights = [a for a in acts if isinstance(a, (unreal.PointLight, unreal.SpotLight))]
out += ["-- light labels sample"] + sorted(set("%s | %s" % (a.get_actor_label(), a.get_folder_path()) for a in lights))[:400]
open(unreal.Paths.project_saved_dir() + "NV_l1_probe_dupes.txt", "w").write("\n".join(out))
