import unreal
w = unreal.EditorLevelLibrary.get_game_world()
out = []
for a in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.Actor):
    if a.get_actor_label() in ("B_Opt_NewsFeed", "A_ArrivalVO"):
        for p in ("lines_on_use", "lines_on_complete"):
            try: arr = a.get_editor_property(p)
            except Exception: continue
            for l in arr:
                v = l.get_editor_property("voice")
                out.append("%s %s dur %.2f voice %s" % (a.get_actor_label(), p, l.get_editor_property("duration"), v.get_name() if v else None))
open(unreal.Paths.project_saved_dir() + "NV_vo_probe.txt", "w").write("\n".join(out) or "none")
