"""PIE test: take the (hidden) NVNavArrow, freeze it, place it 4.7 m ahead and make its parts visible once."""
import unreal
w = unreal.EditorLevelLibrary.get_pie_worlds(False)[0]
p = unreal.GameplayStatics.get_player_pawn(w, 0)
loc = p.get_actor_location()
a = unreal.GameplayStatics.get_all_actors_of_class(w, unreal.NVNavArrow)[0]
a.set_actor_tick_enabled(False)
a.set_actor_location(unreal.Vector(loc.x, loc.y + 470, loc.z - 96 + 12), False, False)
for c in a.get_components_by_class(unreal.StaticMeshComponent):
    c.set_visibility(True)
unreal.log_warning("SPAWNTEST %s" % a.get_actor_location())
