"""Fine plan slice around the X-ray checkpoint: for each 20 cm cell, the highest surface between z 400 and 650.
Report: Saved/NV_xray_slice.txt"""
import unreal
UES = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
w = UES.get_game_world() or UES.get_editor_world()
OBJ = [unreal.ObjectTypeQuery.OBJECT_TYPE_QUERY1, unreal.ObjectTypeQuery.OBJECT_TYPE_QUERY2]
out = []
for a in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.StaticMeshActor):
    if a.get_actor_label().startswith("XRay_"):
        o, e = a.get_actor_bounds(False)
        out.append(f"{a.get_actor_label()} o=({o.x:.0f},{o.y:.0f},{o.z:.0f}) e=({e.x:.0f},{e.y:.0f},{e.z:.0f})")
out.append("rows y desc from -3300 to -4000; cols x 6400..7700 step 20; digit = (top-400)/25, '.'=floor, '#'>=250")
for yi in range(-3300, -4001, -20):
    row = ""
    for xi in range(6400, 7701, 20):
        h = unreal.SystemLibrary.line_trace_single_for_objects(w, unreal.Vector(xi, yi, 650), unreal.Vector(xi, yi, 380), OBJ, False, [], unreal.DrawDebugTrace.NONE, True)
        if not h:
            row += " "; continue
        z = h.to_tuple()[4].z - 400
        row += "." if z < 12 else ("#" if z >= 250 else str(min(9, int(z // 25))))
    out.append(f"{yi:6d} {row}")
open(unreal.Paths.project_saved_dir() + "NV_xray_slice.txt", "w").write("\n".join(out))
