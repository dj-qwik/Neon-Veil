"""PIE: sweep Ghost's capsule from the crew-room doorway up to the Station Ops crew-pass terminal to prove the path is
open (no crouch/jump needed). Saved/NV_pie_crewwalk.txt"""
import os
import unreal
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
pawn = unreal.GameplayStatics.get_player_controller(w, 0).get_controlled_pawn()
out = []
Z = 525.0
pawn.set_actor_location(unreal.Vector(6790, 3900, Z), False, True)
out.append("start %s" % pawn.get_actor_location())
for tgt in ((6790, 4300), (6790, 4640), (6730, 4680)):
    pawn.set_actor_location(unreal.Vector(tgt[0], tgt[1], Z), True, True)
    l = pawn.get_actor_location()
    out.append("to %s -> (%d, %d)%s" % (tgt, l.x, l.y, "" if abs(l.x - tgt[0]) < 2 and abs(l.y - tgt[1]) < 2 else "  BLOCKED"))
cp = None
for a in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.NVInteractableActor):
    if a.get_actor_label() == "I_CrewPass":
        cp = a
if cp:
    out.append("distance to crew pass terminal: %.0f cm" % (pawn.get_actor_location() - cp.get_actor_location()).length())
open(os.path.join(unreal.Paths.project_saved_dir(), "NV_pie_crewwalk.txt"), "w").write("\n".join(out))
