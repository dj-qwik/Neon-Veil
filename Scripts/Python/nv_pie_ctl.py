"""PIE helper. argv[2]: 'where' | 'tp x y z yaw' | 'ev Tag1 Tag2..' | 'actor <labelprefix>'. Report: Saved/NV_pie_ctl.txt"""
import sys, unreal
w = unreal.EditorLevelLibrary.get_game_world()
out = []
args = (sys.argv[2] if len(sys.argv) > 2 else "where").split()
pawn = unreal.GameplayStatics.get_player_pawn(w, 0)
pc = unreal.GameplayStatics.get_player_controller(w, 0)
if args[0] == "tp" and pawn:
    x, y, z, yaw = (float(v) for v in args[1:5])
    pawn.set_actor_location(unreal.Vector(x, y, z), False, True)
    pc.set_control_rotation(unreal.Rotator(roll=0, pitch=0, yaw=yaw))
if args[0] == "ev":
    obj = unreal.SubsystemBlueprintLibrary.get_game_instance_subsystem(w, unreal.NVObjectiveSubsystem)
    for t in args[1:]:
        tg = unreal.GameplayTag(); tg.import_text('(TagName="%s")' % t)
        out.append("event %s -> %s" % (t, obj.send_event(tg)))
if args[0] == "actor":
    for a in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.Actor):
        if a.get_actor_label().startswith(args[1]):
            out.append("%s %s hidden=%s" % (a.get_actor_label(), a.get_actor_location(), a.is_hidden_ed() if hasattr(a, "is_hidden_ed") else "?"))
out.append("pawn %s" % (pawn.get_actor_location() if pawn else None))
if pawn:
    try:
        bm = pawn.get_editor_property("based_movement")
        b = bm.get_editor_property("movement_base")
        out.append("base %s (%s)" % (b.get_name() if b else None, b.get_owner().get_name() if b else ""))
    except Exception as e:
        out.append("base ? %s" % e)
for a in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.Actor):
    if a.get_class().get_name() == "BP_Tram_C":
        out.append("tram %s %s" % (a.get_actor_label(), a.get_actor_location()))
out.append("pawn class %s" % (pawn.get_class().get_name() if pawn else None))
cam = unreal.GameplayStatics.get_player_camera_manager(w, 0)
if cam:
    out.append("cam %s rot %s" % (cam.get_camera_location(), cam.get_camera_rotation()))
for a in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.PlayerStart):
    out.append("start %s %s" % (a.get_actor_label(), a.get_actor_location()))
gm = unreal.GameplayStatics.get_game_mode(w)
out.append("gm %s" % (gm.get_class().get_name() if gm else None))
open(unreal.Paths.project_saved_dir() + "NV_pie_ctl.txt", "w").write("\n".join(str(x) for x in out))
