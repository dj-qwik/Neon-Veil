"""PIE: report the interaction focus and the third-person state. Saved/NV_pie_focus.txt"""
import unreal
w = unreal.EditorLevelLibrary.get_game_world()
pawn = unreal.GameplayStatics.get_player_pawn(w, 0)
ic = pawn.get_component_by_class(unreal.NVInteractionComponent)
f = ic.get_focused_actor()
out = ["focus %s" % (f.get_actor_label() if f else None), "pawn %s" % pawn.get_actor_location()]
for p in ("b_third_person", "third_person"):
    try:
        out.append("%s %s" % (p, pawn.get_editor_property(p)))
    except Exception:
        pass
pc = unreal.GameplayStatics.get_player_controller(w, 0)
out.append("cam %s" % pc.player_camera_manager.get_camera_location())
open(unreal.Paths.project_saved_dir() + "NV_pie_focus.txt", "w").write("\n".join(out))
