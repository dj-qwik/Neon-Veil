import unreal
w = unreal.EditorLevelLibrary.get_pie_worlds(False)[0]
O = []
pc = unreal.GameplayStatics.get_player_controller(w, 0)
cm = pc.player_camera_manager
O.append(f"cam {cm.get_camera_location()} rot {cm.get_camera_rotation()} fov {cm.get_fov_angle()}")
p = unreal.GameplayStatics.get_player_pawn(w, 0)
O.append(f"pawn {p.get_actor_location()}")
for a in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.NVNavArrow):
    O.append(f"arrow {a.get_actor_location()} rot {a.get_actor_rotation()}")
    for c in a.get_components_by_class(unreal.SceneComponent):
        vis = c.is_visible() if hasattr(c, "is_visible") else "?"
        O.append(f"  {c.get_name()} world {c.get_world_location()} scale {c.get_world_scale()} vis {vis}")
    for c in a.get_components_by_class(unreal.StaticMeshComponent):
        m = c.get_material(0)
        op = m.k2_get_scalar_parameter_value("Opacity") if hasattr(m, "k2_get_scalar_parameter_value") else "?"
        O.append(f"  {c.get_name()} mat {m.get_name() if m else None} opacity {op} visible {c.is_visible()} hiddenInGame {c.get_editor_property('hidden_in_game')} rendered {c.was_recently_rendered(0.2)}")
open(unreal.Paths.project_saved_dir() + "NV_arrow_probe.txt", "w").write("\n".join(O))
