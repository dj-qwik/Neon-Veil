"""Survey the open map for the streamed-ride design: extents, environment actors, old subway tram, dock approach.
Report: Saved/NV_l1_survey_crown.txt (+ .json of every actor's bounds)"""
import json, unreal
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
out, rows = [], []
ENV = ("DirectionalLight", "SkyLight", "SkyAtmosphere", "ExponentialHeightFog", "PostProcessVolume", "VolumetricCloud",
       "SkySphere", "BP_Sky", "PlayerStart", "NVCheckpoint", "NVTramArrival", "WorldSettings", "LevelSequence", "NVMusic")
mins, maxs = [1e9] * 3, [-1e9] * 3
for a in EAS.get_all_level_actors():
    c = a.get_class().get_name()
    lab = a.get_actor_label()
    o, e = a.get_actor_bounds(False)
    mesh = ""
    if isinstance(a, unreal.StaticMeshActor) and a.static_mesh_component.static_mesh:
        mesh = a.static_mesh_component.static_mesh.get_path_name()
    rows.append({"label": lab, "cls": c, "mesh": mesh, "folder": str(a.get_folder_path()),
                 "loc": [round(v) for v in (a.get_actor_location().x, a.get_actor_location().y, a.get_actor_location().z)],
                 "bo": [round(o.x), round(o.y), round(o.z)], "be": [round(e.x), round(e.y), round(e.z)]})
    if e.x < 200000 and e.y < 200000 and e.z < 200000 and (e.x + e.y) > 0:
        for i, (cv, ev) in enumerate(((o.x, e.x), (o.y, e.y), (o.z, e.z))):
            mins[i] = min(mins[i], cv - ev); maxs[i] = max(maxs[i], cv + ev)
    if any(k in c for k in ENV):
        out.append("ENV %s | %s | loc %s | folder %s" % (c, lab, rows[-1]["loc"], rows[-1]["folder"]))
    if "/Game/SubwayTrain" in mesh or "SubwayTrain" in c or lab.startswith(("T_", "C00_", "A_Tram")):
        out.append("SUBWAY %s | %s | %s" % (lab, c, mesh))
out.insert(0, "actors %d  extents min %s max %s" % (len(rows), [round(v) for v in mins], [round(v) for v in maxs]))
# what is near the old dock approach (x -2500..1500, y -2000..25000, z -600..900)
for r in rows:
    (ox, oy, oz), (ex, ey, ez) = r["bo"], r["be"]
    if ex > 50000 or ey > 50000:
        continue
    if ox + ex > -2500 and ox - ex < 1500 and oy + ey > -2000 and oy - ey < 25000 and oz + ez > -600 and oz - ez < 900:
        out.append("NEAR %s | %s | c%s e%s" % (r["label"], r["cls"], r["bo"], r["be"]))
ws = unreal.EditorLevelLibrary.get_editor_world().get_world_settings()
out.append("gamemode %s killz %s" % (ws.get_editor_property("default_game_mode"), ws.get_editor_property("kill_z")))
sd = unreal.Paths.project_saved_dir()
open(sd + "NV_l1_survey_crown.txt", "w").write("\n".join(out))
json.dump(rows, open(sd + "NV_l1_survey_crown.json", "w"))
