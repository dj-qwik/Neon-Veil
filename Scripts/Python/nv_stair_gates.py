"""Platform stair gates that actually seal the stairwells.

The two concourse gates (G_Gate_North / G_Gate_South) were 420 cm wide and 350 cm tall over 800 cm wide stairwells, so
you could walk around either side. They now span the full stairwell (plus overlap into the walls) and reach the
ceiling. The stub of floor between the two stairwells only had knee-high railings with a gap at the column, so
invisible pawn blockers (z 400..800) run along both stairwell side edges; they're parallel to the stairs, so they
never get in the way once a gate is open. Two more close the divider itself (its entrance in line with the gates
and its far end), so nobody walks out onto it and hops the railing down to the platform.
Called from nv_station_route.py; safe to run on its own (idempotent, tag NVSTAIR). Report: Saved/NV_stair_gates.txt"""
import unreal
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
V = unreal.Vector
OUT = []
CUBE = unreal.load_asset("/Engine/BasicShapes/Cube")
TAG = "NVSTAIR"
for a in list(EAS.get_all_level_actors()):
    if TAG in [str(t) for t in a.tags]:
        EAS.destroy_actor(a)

STAIRS = {"G_Gate_North": (-1020.0, -220.0), "G_Gate_South": (-2620.0, -1820.0)}   # stairwell y extents
FLOOR_Z, CEIL_Z, EDGE_X = 400.0, 800.0, 6246.0
OVERLAP = 30.0
for a in EAS.get_all_level_actors():
    lab = a.get_actor_label()
    if lab not in STAIRS:
        continue
    y0, y1 = STAIRS[lab]
    width = (y1 - y0) + OVERLAP * 2
    height = CEIL_Z - FLOOR_Z - 4
    l = a.get_actor_location()
    a.set_actor_location(V(l.x, (y0 + y1) / 2, FLOOR_Z), False, False)
    for comp_name, s in (("panel_left", -1), ("panel_right", 1)):
        c = a.get_editor_property(comp_name)
        c.set_editor_property("relative_location", V(0, s * width / 4.0, height / 2))
        c.set_editor_property("relative_scale3d", V(0.12, width / 200.0, height / 100.0))
        c.set_collision_profile_name("BlockAll")
    a.set_editor_property("slide_distance", width / 2.0 + 10)
    OUT.append(f"{lab}: {width:.0f} x {height:.0f} cm at y {(y0 + y1) / 2:.0f}")

def blocker(label, x0, x1, y):
    b = EAS.spawn_actor_from_object(CUBE, V((x0 + x1) / 2, y, (FLOOR_Z + CEIL_Z) / 2), unreal.Rotator())
    b.set_actor_label(label); b.set_folder_path("P_Route"); b.tags = [unreal.Name(TAG)]
    b.set_actor_scale3d(V((x1 - x0) / 100.0, 0.2, (CEIL_Z - FLOOR_Z) / 100.0))
    c = b.static_mesh_component
    c.set_collision_profile_name("InvisibleWall")
    c.set_editor_property("can_ever_affect_navigation", False)
    b.set_actor_hidden_in_game(True)
    OUT.append(f"{label}: x {x0:.0f}..{x1:.0f} at y {y:.0f}")
def cross_blocker(label, x, y0, y1):
    b = EAS.spawn_actor_from_object(CUBE, V(x, (y0 + y1) / 2, (FLOOR_Z + CEIL_Z) / 2), unreal.Rotator())
    b.set_actor_label(label); b.set_folder_path("P_Route"); b.tags = [unreal.Name(TAG)]
    b.set_actor_scale3d(V(0.2, (y1 - y0) / 100.0, (CEIL_Z - FLOOR_Z) / 100.0))
    c = b.static_mesh_component
    c.set_collision_profile_name("InvisibleWall")
    c.set_editor_property("can_ever_affect_navigation", False)
    b.set_actor_hidden_in_game(True)
    OUT.append(f"{label}: y {y0:.0f}..{y1:.0f} at x {x:.0f}")
# the divider between the two stairwells (y -1820..-1020) and both of its long edges
blocker("Stair_Block_S_Edge", 5446, EDGE_X + 10, -1820)
blocker("Stair_Block_N_Edge", 5446, EDGE_X + 10, -1020)
# ...and across it: in line with the gates (you can't walk out onto the divider while the gates are shut) and at its
# far end (the railing you could hop to drop onto the platform)
cross_blocker("Stair_Block_Divider_In", 6300, -1830, -1010)
cross_blocker("Stair_Block_Divider_End", 5446, -1830, -1010)
open(unreal.Paths.project_saved_dir() + "NV_stair_gates.txt", "w").write("\n".join(OUT))
if __name__ == "__main__":
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
