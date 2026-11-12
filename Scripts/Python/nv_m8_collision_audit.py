"""NEON VEIL - M8 collision audit: which actors still create physics bodies (ISM instances count each).
Report: Saved/NV_m8_collision_audit.txt"""
import unreal

EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
rows = []
total = 0
for a in EAS.get_all_level_actors():
    n = 0
    for c in a.get_components_by_class(unreal.PrimitiveComponent):
        try:
            if c.get_collision_enabled() == unreal.CollisionEnabled.NO_COLLISION:
                continue
        except Exception:
            continue
        if isinstance(c, unreal.InstancedStaticMeshComponent):
            n += c.get_instance_count()
        else:
            n += 1
    if n:
        rows.append((n, a.get_actor_label(), str(a.get_folder_path()), a.get_class().get_name()))
        total += n
rows.sort(reverse=True)
out = [f"TOTAL bodies (approx) {total} across {len(rows)} actors"]
by_folder = {}
for n, lab, fol, cls in rows:
    by_folder[fol] = by_folder.get(fol, 0) + n
out += [f"folder {f or '(none)'}: {n}" for f, n in sorted(by_folder.items(), key=lambda x: -x[1])]
out += [f"{n:8d}  {lab}  [{fol}]  {cls}" for n, lab, fol, cls in rows[:40]]
with open(unreal.Paths.project_saved_dir() + "NV_m8_collision_audit.txt", "w", encoding="utf-8") as fh:
    fh.write("\n".join(out))
