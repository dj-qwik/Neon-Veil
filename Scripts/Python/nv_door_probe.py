import unreal
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
O = []
for m in ["SM_Door_Left", "SM_Door_Right", "SM_Wall_Door_A", "SM_Door_Frame_A"]:
    a = unreal.load_asset("/Game/SciFiTramStation/Meshes/" + m)
    if a:
        b = a.get_bounding_box(); O.append(f"{m} min {b.min} max {b.max}")
for a in EAS.get_all_level_actors():
    l = a.get_actor_label()
    if l.startswith(("Lo_Door", "Up_Door", "Lo_DoorWall", "Up_DoorWall")):
        o, e = a.get_actor_bounds(False)
        O.append(f"{l} loc {a.get_actor_location()} rot {a.get_actor_rotation()} bmin {o - e} bmax {o + e}")
bp = unreal.EditorAssetLibrary.load_blueprint_class("/Game/SciFiTramStation/Blueprints/BP_Door_A")
if bp:
    cdo = unreal.get_default_object(bp)
    O.append("BP_Door_A cdo " + str(cdo))
    for c in cdo.get_components_by_class(unreal.StaticMeshComponent):
        O.append(f"  comp {c.get_name()} mesh {c.static_mesh.get_name() if c.static_mesh else None} rel {c.get_editor_property('relative_location')}")
open(unreal.Paths.project_saved_dir() + "NV_door_probe.txt", "w").write("\n".join(O))
