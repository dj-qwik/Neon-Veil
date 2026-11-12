"""End-wall pieces use their render geometry for collision so the open end doorway is walkable.
Also reports what the player capsule would hit walking out of the front door. Report: Saved/NV_tram_fix3.txt"""
import unreal
EAL = unreal.EditorAssetLibrary
out = []
for n in ("SM_ext_endwall_01", "SM_int_wall_end_01", "SM_wall_doorway_01", "SM_ext_endwall_lights_01"):
    m = unreal.load_asset("/Game/SubwayTrain/Meshes/Structure/" + n)
    bs = m.get_editor_property("body_setup")
    if bs:
        bs.set_editor_property("collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
        m.set_editor_property("body_setup", bs)
    EAL.save_loaded_asset(m)
    out.append("%s complex-as-simple" % n)
# sweep test along the exit path (editor world, door actor moved to its open position for the test)
w = unreal.EditorLevelLibrary.get_editor_world()
door = None
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    if a.get_actor_label() == "T_DoorFront":
        door = a
if door:
    home = door.get_actor_location()
    door.set_actor_location(home + unreal.Vector(0, 92, 0), False, False)
for z in (60, 140):
    hits = unreal.SystemLibrary.sphere_trace_multi(w, unreal.Vector(-400, 0, z), unreal.Vector(300, 0, z), 34.0,
        unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [], unreal.DrawDebugTrace.NONE, True)
    for h in hits:
        t = h.to_tuple()
        actor = t[9] if len(t) > 9 else None
        out.append("z%d hit %s at %s" % (z, actor.get_actor_label() if actor else t, t[4] if len(t) > 4 else ""))
if door:
    door.set_actor_location(home, False, False)
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
open(unreal.Paths.project_saved_dir() + "NV_tram_fix3.txt", "w").write("\n".join(str(x) for x in out))
