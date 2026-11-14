"""Glass Crown: keep the rain fields out of the docked tram. RainNear_BridgeN/S reached west to x -1300 and covered the
dock (tram docked at x -550..-50); they now start at the skybridge end (x 0). Any other NVRainField overlapping the
dock box is trimmed the same way. Report: Saved/NV_crown_rain_dock.txt"""
import unreal
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
LES = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
MAP = "/Game/NeonVeil/Maps/M00/L_M00_GlassCrown"
if not unreal.EditorLevelLibrary.get_editor_world().get_path_name().startswith(MAP):
    LES.load_level(MAP)
OUT = []
DOCK_MAX_X = 0.0           # east edge of the docked car plus a margin
DOCK_Y = (-700.0, 1650.0)  # docked car spans y -575..1525
for a in EAS.get_all_level_actors():
    if a.get_class().get_name() != "NVRainField":
        continue
    l = a.get_actor_location(); e = a.get_editor_property("extent")
    xa, xb, ya, yb = l.x - e.x, l.x + e.x, l.y - e.y, l.y + e.y
    if xa < DOCK_MAX_X + 1 and xb > DOCK_MAX_X and ya < DOCK_Y[1] and yb > DOCK_Y[0] and xb > DOCK_MAX_X + 200:
        nxa = DOCK_MAX_X
        a.set_actor_location(unreal.Vector((nxa + xb) / 2, l.y, l.z), False, False)
        a.set_editor_property("extent", unreal.Vector((xb - nxa) / 2, e.y, e.z))
        cnt = a.get_editor_property("count")
        a.set_editor_property("count", int(cnt * (xb - nxa) / (xb - xa)))
        OUT.append(f"trimmed {a.get_actor_label()}: x {xa:.0f}..{xb:.0f} -> {nxa:.0f}..{xb:.0f}")
LES.save_current_level()
open(unreal.Paths.project_saved_dir() + "NV_crown_rain_dock.txt", "w").write("\n".join(OUT) or "nothing to trim")
