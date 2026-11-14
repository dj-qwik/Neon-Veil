"""Walkable floors between z 0..750 (object trace on WorldStatic, upward-facing). Report: Saved/NV_floor_grid.txt"""
import unreal
UES = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
w = UES.get_game_world() or UES.get_editor_world()
OBJ = [unreal.ObjectTypeQuery.OBJECT_TYPE_QUERY1, unreal.ObjectTypeQuery.OBJECT_TYPE_QUERY2]
def floors(x, y):
    z, res = 760.0, []
    for _ in range(8):
        hit = unreal.SystemLibrary.line_trace_single_for_objects(w, unreal.Vector(x, y, z), unreal.Vector(x, y, -100), OBJ, False, [], unreal.DrawDebugTrace.NONE, True)
        if not hit: break
        t = hit.to_tuple(); hz = t[4].z
        if t[7].z > 0.7: res.append(int(hz))
        z = hz - 40
    return res
out = []
for x in range(5000, 9501, 250):
    cells = []
    for y in range(-3500, 5501, 500):
        f = floors(x, y)
        cells.append(("/".join(str(v) for v in f) or "-").rjust(8))
    out.append(f"x={x:5d} " + "".join(cells))
out.insert(0, "y:      " + "".join(str(y).rjust(8) for y in range(-3500, 5501, 500)))
for x in range(0, 5001, 500):
    out.append(f"P x={x:5d} " + "".join(("/".join(str(v) for v in floors(x, y)) or "-").rjust(8) for y in range(-3000, 501, 250)))
open(unreal.Paths.project_saved_dir() + "NV_floor_grid.txt", "w").write("\n".join(out))
