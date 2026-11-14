"""Open a map (argv[2], default Soul City slum) and dump actors (class, mesh, transform, bounds) to
Saved/NV_l1_survey_<mapname>.json for offline layout planning. Usage: nv_run.py nv_l1_survey_map /Game/Path/Map"""
import json, sys
import unreal
MAP = sys.argv[2] if len(sys.argv) > 2 else "/Game/SoulCity/Maps/LV_Soul_Slum"
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level(MAP)
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
rows = []
for a in EAS.get_all_level_actors():
    o, e = a.get_actor_bounds(False)
    mesh = ""
    if isinstance(a, unreal.StaticMeshActor):
        sm = a.static_mesh_component.static_mesh
        mesh = sm.get_name() if sm else ""
    l, r, s = a.get_actor_location(), a.get_actor_rotation(), a.get_actor_scale3d()
    rows.append(dict(label=a.get_actor_label(), cls=a.get_class().get_name(), mesh=mesh,
                     loc=[l.x, l.y, l.z], rot=[r.pitch, r.yaw, r.roll], scale=[s.x, s.y, s.z],
                     bo=[o.x, o.y, o.z], be=[e.x, e.y, e.z], folder=str(a.get_folder_path())))
name = MAP.rsplit("/", 1)[-1]
open(unreal.Paths.project_saved_dir() + f"NV_l1_survey_{name}.json", "w").write(json.dumps(rows))
