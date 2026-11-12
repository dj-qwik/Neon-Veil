"""PIE probe: player + exit door leaf/frame locations; sweep from player through the exit. Report: Saved/NV_pie_where.txt"""
import unreal
w = unreal.EditorLevelLibrary.get_game_world()
out = []
pawn = unreal.GameplayStatics.get_player_pawn(w, 0)
out.append("player %s" % pawn.get_actor_location())
for a in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.StaticMeshActor):
    lab = a.get_actor_label()
    if lab.startswith(("T_Exit", "T_Root", "T_WallFar1", "T_WallFar3", "A_TramFloor")):
        o, e = a.get_actor_bounds(False)
        out.append("%s loc %s bounds c(%.0f,%.0f,%.0f) e(%.0f,%.0f,%.0f)" % (lab, a.get_actor_location(), o.x, o.y, o.z, e.x, e.y, e.z))
for a in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.Actor):
    if a.get_actor_label().startswith("T_WallFar"):
        o, e = a.get_actor_bounds(False)
        out.append("%s bounds y %.0f..%.0f" % (a.get_actor_label(), o.y - e.y, o.y + e.y))
for y in (-60, 0, 60):
    hits = unreal.SystemLibrary.sphere_trace_multi(w, unreal.Vector(-200, y, 100), unreal.Vector(400, y, 100), 34.0,
        unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [pawn], unreal.DrawDebugTrace.NONE, True)
    out.append("sweep y=%d: %s" % (y, [(h.to_tuple()[9].get_actor_label(), round(h.to_tuple()[4].x)) for h in hits] or "clear"))
open(unreal.Paths.project_saved_dir() + "NV_pie_where.txt", "w").write("\n".join(str(x) for x in out))
