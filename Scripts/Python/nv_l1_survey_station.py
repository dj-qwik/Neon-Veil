"""Open the Sci-Fi Tram Station map and dump every actor (class, mesh, transform, world bounds) to JSON so the
walk route can be planned offline. Report: Saved/NV_l1_station_actors.json"""
import json
import unreal
LES = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
LES.load_level("/Game/SciFiTramStation/Maps/SciFiStation")
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
rows = []
for a in EAS.get_all_level_actors():
    o, e = a.get_actor_bounds(False)
    mesh = ""
    if isinstance(a, unreal.StaticMeshActor):
        sm = a.static_mesh_component.static_mesh
        mesh = sm.get_name() if sm else ""
    elif a.get_class().get_name().startswith("BP_"):
        mesh = a.get_class().get_name()
    l, r, s = a.get_actor_location(), a.get_actor_rotation(), a.get_actor_scale3d()
    rows.append(dict(label=a.get_actor_label(), cls=a.get_class().get_name(), mesh=mesh,
                     loc=[l.x, l.y, l.z], rot=[r.pitch, r.yaw, r.roll], scale=[s.x, s.y, s.z],
                     bo=[o.x, o.y, o.z], be=[e.x, e.y, e.z],
                     folder=str(a.get_folder_path())))
open(unreal.Paths.project_saved_dir() + "NV_l1_station_actors.json", "w").write(json.dumps(rows))
