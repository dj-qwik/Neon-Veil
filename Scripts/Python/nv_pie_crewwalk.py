"""PIE: sweep Ghost's capsule along the real route from the concourse, up the north service corridor and into the
crew room, to the Station Ops crew-pass terminal. Logs the blocking actor at each leg. Saved/NV_pie_crewwalk.txt"""
import os
import unreal
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
pawn = unreal.GameplayStatics.get_player_controller(w, 0).get_controlled_pawn()
out = []
Z = 510.0
ROUTE = [(6740, 2350), (6740, 2700), (6725, 3300), (6725, 3700), (6760, 3950), (6790, 4300), (6790, 4560), (6740, 4640)]
pawn.set_actor_location(unreal.Vector(ROUTE[0][0], ROUTE[0][1], Z), False, True)
for tgt in ROUTE[1:]:
    r = pawn.set_actor_location(unreal.Vector(tgt[0], tgt[1], Z), True, False)
    l = pawn.get_actor_location()
    ok = abs(l.x - tgt[0]) < 2 and abs(l.y - tgt[1]) < 2
    who = ""
    if not ok:
        hit = unreal.SystemLibrary.capsule_trace_single(w, l, unreal.Vector(tgt[0], tgt[1], Z), 34.0, 88.0,
                                                        unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, True, [pawn], unreal.DrawDebugTrace.NONE, True)
        if hit:
            t = hit.to_tuple()
            who = " hit %s/%s at %s" % (t[9].get_actor_label() if t[9] else None, t[10].get_name() if t[10] else None, t[5])
        pawn.set_actor_location(unreal.Vector(tgt[0], tgt[1], Z), False, True)   # carry on from the target
    out.append("to %s -> (%d, %d) %s%s" % (tgt, l.x, l.y, "ok" if ok else "BLOCKED", who))
open(os.path.join(unreal.Paths.project_saved_dir(), "NV_pie_crewwalk.txt"), "w").write("\n".join(out))
