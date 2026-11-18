"""Audit: for every interactable in the open level, sweep the player's use-trace (12 cm sphere, Visibility) at it from
eight directions, standing 1.1 m away on the floor with eyes at 160 cm, and list what blocks it first when it is not the interactable. Also lists
every scripted dressing actor (tag NVDRESS2 etc.) that still has collision, with its size. Read-only.
Usage: py nv_audit_use_traces.py  -> Saved/NV_audit_<map>.txt"""
import unreal, math
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
out = []
acts = EAS.get_all_level_actors()
inter = [a for a in acts if isinstance(a, unreal.NVInteractableActor)]
for a in acts:
    try:
        if a not in inter and a.get_class().implements_interface(unreal.NVInteractable):
            inter.append(a)
    except Exception:
        pass
out.append("interactables: %d" % len(inter))
blockers = {}
for a in inter:
    o, ext = a.get_actor_bounds(False)
    bad = []
    ok = 0
    for k in range(8):
        ang = math.radians(k * 45)
        for dz in (0.0, 1.0):
            # stand 1.1 m out on whatever floor is there, eyes 160 cm up (dz=1 aims 20 cm above the centre)
            px, py = o.x + math.cos(ang) * 110, o.y + math.sin(ang) * 110
            fl = unreal.SystemLibrary.line_trace_single(w, unreal.Vector(px, py, o.z + 120), unreal.Vector(px, py, o.z - 400), unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [a], unreal.DrawDebugTrace.NONE, True)
            if not fl:
                continue
            s = unreal.Vector(px, py, fl.to_tuple()[4].z + 160)
            tgt = o + unreal.Vector(0, 0, 20 * dz)
            hit0 = unreal.SystemLibrary.line_trace_single(w, s, s + (tgt - s) * 0.4, unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [], unreal.DrawDebugTrace.NONE, True)
            if hit0 and hit0.to_tuple()[9] and hit0.to_tuple()[9] != a:
                continue
            hit = unreal.SystemLibrary.sphere_trace_single(w, s, tgt, 12.0, unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [], unreal.DrawDebugTrace.NONE, True)
            t = hit.to_tuple() if hit else None
            h = t[9] if t else None
            if h == a or (h and h.get_attach_parent_actor() == a):
                ok += 1
            elif h:
                bad.append(h)
    names = sorted(set(b.get_actor_label() for b in bad))
    for b in bad:
        blockers.setdefault(b.get_actor_label(), (b, set()))[1].add(a.get_actor_label())
    out.append("%-28s ok %2d blocked %2d %s" % (a.get_actor_label(), ok, len(bad), ", ".join(names[:6])))
out.append("")
out.append("blockers:")
for lab, (b, who) in sorted(blockers.items()):
    o, ext = b.get_actor_bounds(False)
    tags = ",".join(str(t) for t in b.tags)
    out.append("  %-30s tags[%s] folder %s size %.0fx%.0fx%.0f -> %s" % (lab, tags, b.get_folder_path(), ext.x*2, ext.y*2, ext.z*2, ", ".join(sorted(who))))
out.append("")
out.append("dressing with collision:")
DT = ("NVDRESS2", "NVM01ART", "NVM01DIR", "NVHB", "NVROUTE", "NVLANTERN", "NVE", "NVG2", "NVSTAIR", "NVM01")
for a in acts:
    tg = [str(t) for t in a.tags]
    if not any(t in DT or t.startswith("NVD_") for t in tg):
        continue
    for c in a.get_components_by_class(unreal.PrimitiveComponent):
        if c.get_collision_enabled() != unreal.CollisionEnabled.NO_COLLISION and c.get_collision_response_to_channel(unreal.CollisionChannel.ECC_VISIBILITY) == unreal.CollisionResponseType.ECR_BLOCK:
            o, ext = a.get_actor_bounds(False)
            out.append("  %s %-30s %.0fx%.0fx%.0f" % (",".join(tg), a.get_actor_label(), ext.x*2, ext.y*2, ext.z*2))
            break
name = w.get_name()
open(unreal.Paths.project_saved_dir() + "NV_audit_%s.txt" % name, "w").write("\n".join(out))
