"""Survey current map: tram(s), tram drivers, rain, X-ray. argv[2]=map path (optional). Report: Saved/NV_tram_survey.txt"""
import sys, unreal
LES = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if len(sys.argv) > 2 and not unreal.EditorLevelLibrary.get_editor_world().get_path_name().startswith(sys.argv[2]):
    LES.load_level(sys.argv[2])
out = []
def v(x): return f"({x.x:.0f},{x.y:.0f},{x.z:.0f})"
for a in EAS.get_all_level_actors():
    cn = a.get_class().get_name(); lab = a.get_actor_label()
    if cn in ("NVTramService", "NVTramRide"):
        out.append(f"{cn} {lab} at {v(a.get_actor_location())} rot {a.get_actor_rotation().yaw:.0f}")
        for p in ("tram", "dock_door_side", "flip_door_direction", "door_slide", "tram_yaw_offset", "depart_distance", "depart_time"):
            try:
                val = a.get_editor_property(p)
                out.append(f"   {p} = {val.get_actor_label() if hasattr(val, 'get_actor_label') else val}")
            except Exception:
                pass
        if cn == "NVTramRide":
            sp = a.get_editor_property("path")
            n = sp.get_number_of_spline_points()
            out.append("   path " + " ".join(v(sp.get_location_at_spline_point(i, unreal.SplineCoordinateSpace.WORLD)) for i in range(n)))
    if cn == "BP_Tram_C":
        out.append(f"TRAM {lab} at {v(a.get_actor_location())} yaw {a.get_actor_rotation().yaw:.0f}")
        for c in a.get_components_by_class(unreal.PrimitiveComponent):
            m = c.get_editor_property("static_mesh").get_name() if isinstance(c, unreal.StaticMeshComponent) and c.get_editor_property("static_mesh") else ""
            out.append(f"   {c.get_name()} {c.get_class().get_name()} rel {v(c.get_editor_property('relative_location'))} yaw {c.get_editor_property('relative_rotation').yaw:.0f} scale {v(c.get_editor_property('relative_scale3d'))} mesh {m} col {c.get_collision_enabled()}")
    if cn == "NVRainField" or "rain" in lab.lower():
        ext = ""
        try: ext = v(a.get_editor_property("extent"))
        except Exception: pass
        out.append(f"RAIN {cn} {lab} at {v(a.get_actor_location())} yaw {a.get_actor_rotation().yaw:.0f} scale {v(a.get_actor_scale3d())} extent {ext}")
    if "xray" in lab.lower() or "scanner" in lab.lower() or "x_ray" in lab.lower():
        out.append(f"XRAY {cn} {lab} at {v(a.get_actor_location())} yaw {a.get_actor_rotation().yaw:.0f} scale {v(a.get_actor_scale3d())}")
open(unreal.Paths.project_saved_dir() + "NV_tram_survey.txt", "w").write("\n".join(out))
