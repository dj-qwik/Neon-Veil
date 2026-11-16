"""PIE: stand Ghost in front of the breaker box, optionally third person. argv[-1]: 'tp' or 'fp'."""
import sys, unreal
w = unreal.EditorLevelLibrary.get_game_world()
pawn = unreal.GameplayStatics.get_player_pawn(w, 0)
pc = unreal.GameplayStatics.get_player_controller(w, 0)
panel = [a for a in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.NVBreakerPanel)][0]
loc = panel.get_actor_location()
fwd = panel.get_actor_forward_vector()
dest = unreal.Vector(loc.x + fwd.x * 160, loc.y + fwd.y * 160, loc.z + 100)
yaw = unreal.MathLibrary.find_look_at_rotation(dest, loc).yaw
pawn.teleport(dest, unreal.Rotator(0, 0, 0))
pc.set_control_rotation(unreal.Rotator(roll=0, pitch=0, yaw=yaw))
pawn.set_third_person(sys.argv[-1] == "tp")
open(unreal.Paths.project_saved_dir() + "NV_pie_focus.txt", "w").write("moved to %s yaw %.0f panel %s" % (dest, yaw, panel.get_name()))
