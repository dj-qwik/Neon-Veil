import unreal
OUT = unreal.Paths.project_saved_dir() + "NV_drone_pie.txt"
w = unreal.EditorLevelLibrary.get_game_world()
log = []
if not w:
    log.append("no PIE world")
else:
    for a in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.NVTrainingTarget):
        if "Drone" in a.get_actor_label() or "Drone" in a.get_name():
            h = a.get_editor_property("health")
            log.append("%s loc %s hidden %s cleared %s health %.1f/%.1f" % (a.get_name(), a.get_actor_location(), a.is_hidden_ed() if hasattr(a,'is_hidden_ed') else a.get_editor_property("hidden"), a.is_cleared(), h.get_health(), h.get_editor_property("max_health")))
    for p in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.Character):
        log.append("pawn %s %s" % (p.get_name(), p.get_actor_location()))
open(OUT, "a").write("\n".join(log) + "\n----\n")
