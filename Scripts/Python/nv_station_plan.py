"""Plan-view survey of the station (prologue map) for route planning. Writes Saved/NV_plan_<z>.txt grids
(F floor, O obstacle, . void; lowercase = no ceiling above) and Saved/NV_plan_actors.txt (markers)."""
import unreal
UES = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
w = UES.get_game_world() or UES.get_editor_world()
OBJ = [unreal.ObjectTypeQuery.OBJECT_TYPE_QUERY1, unreal.ObjectTypeQuery.OBJECT_TYPE_QUERY2]
X0, X1, Y0, Y1, S = -1500, 10000, -5200, 6200, 75
def tr(a, b):
    h = unreal.SystemLibrary.line_trace_single_for_objects(w, a, b, OBJ, False, [], unreal.DrawDebugTrace.NONE, True)
    return h.to_tuple()[4].z if h else None
SAV = unreal.Paths.project_saved_dir()
for FZ in (400, 0):
    rows = []
    y = Y1
    while y >= Y0:
        row = []
        x = X0
        while x <= X1:
            hz = tr(unreal.Vector(x, y, FZ + 190), unreal.Vector(x, y, FZ - 60))
            if hz is None or hz < FZ - 30:
                c = "."
            elif hz <= FZ + 30:
                c = "F"
            else:
                c = "O"
            if c != "O":
                up = tr(unreal.Vector(x, y, FZ + 200), unreal.Vector(x, y, FZ + 900))
                if up is None:
                    c = c.lower() if c == "F" else ","
            row.append(c)
            x += S
        rows.append("".join(row))
        y -= S
    open(SAV + f"NV_plan_{FZ}.txt", "w").write(f"X0={X0} Y1={Y1} S={S} rows=y desc, cols=x asc\n" + "\n".join(rows))
out = []
for a in EAS.get_all_level_actors():
    cn = a.get_class().get_name(); lab = a.get_actor_label()
    if any(k in cn for k in ("NVObjective", "NVInteract", "NVTutorial", "NVElevator", "NVTram", "PlayerStart", "NVCheckpoint", "Door")) \
            or "Door" in lab or lab.startswith(("NPC_", "XRay", "S_", "Shutter", "Vault", "G_Gate")):
        l = a.get_actor_location()
        out.append(f"{cn}|{lab}|{l.x:.0f}|{l.y:.0f}|{l.z:.0f}|{a.get_actor_rotation().yaw:.0f}|{a.get_folder_path()}")
open(SAV + "NV_plan_actors.txt", "w").write("\n".join(out))
