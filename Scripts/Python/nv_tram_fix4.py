"""Front end: kit end-wall collision off (its simple collision seals the doorway); invisible blockers frame the
90 cm door opening instead. Then sweep the exit path. Report: Saved/NV_tram_fix4.txt"""
import unreal
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
V = unreal.Vector
XF = -100.0
CUBE = unreal.load_asset("/Engine/BasicShapes/Cube")
out = []
door = None
for a in list(EAS.get_all_level_actors()):
    lab = a.get_actor_label()
    if lab.startswith("T_Block"):
        EAS.destroy_actor(a)
    elif lab in ("T_EndIntFront", "T_EndExtFront"):
        for c in a.get_components_by_class(unreal.PrimitiveComponent):
            c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
        out.append("%s collision off" % lab)
    elif lab == "T_DoorFront":
        door = a

def blocker(label, center, size):
    b = EAS.spawn_actor_from_class(unreal.StaticMeshActor, V(*center), unreal.Rotator())
    c = b.static_mesh_component
    c.set_static_mesh(CUBE)
    b.set_actor_scale3d(V(size[0] / 100.0, size[1] / 100.0, size[2] / 100.0))
    c.set_collision_profile_name("BlockAll")
    c.set_cast_shadow(False)
    b.set_actor_hidden_in_game(True)
    c.set_visibility(False)
    b.set_actor_label(label); b.set_folder_path("Tram")
HALF = 46.0   # door opening half-width
blocker("T_BlockFrontL", (XF + 15, -(150 + HALF) / 2.0, 130), (40, 150 - HALF, 260))
blocker("T_BlockFrontR", (XF + 15, (150 + HALF) / 2.0, 130), (40, 150 - HALF, 260))
blocker("T_BlockFrontTop", (XF + 15, 0, 245), (40, 2 * HALF, 30))
# sweep with the door open
w = unreal.EditorLevelLibrary.get_editor_world()
home = door.get_actor_location()
door.set_actor_location(home + V(0, 92, 0), False, False)
for z in (60, 140):
    hits = unreal.SystemLibrary.sphere_trace_multi(w, V(-400, 0, z), V(300, 0, z), 34.0,
        unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [], unreal.DrawDebugTrace.NONE, True)
    out.append("z%d open: %s" % (z, [(h.to_tuple()[9].get_actor_label(), round(h.to_tuple()[4].x)) for h in hits] or "clear"))
door.set_actor_location(home, False, False)
hits = unreal.SystemLibrary.sphere_trace_multi(w, V(-400, 0, 100), V(300, 0, 100), 34.0,
    unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [], unreal.DrawDebugTrace.NONE, True)
out.append("closed: %s" % [(h.to_tuple()[9].get_actor_label(), round(h.to_tuple()[4].x)) for h in hits])
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
open(unreal.Paths.project_saved_dir() + "NV_tram_fix4.txt", "w").write("\n".join(out))
