"""PIE: where is the first-person weapon, and what is floating in front of the camera? Saved/NV_pie_gun_diag.txt"""
import unreal
out = []
try:
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    pc = unreal.GameplayStatics.get_player_controller(w, 0)
    p = pc.get_controlled_pawn()
    cam = pc.player_camera_manager
    cl, cr = cam.get_camera_location(), cam.get_camera_rotation()
    out.append("cam %s %s" % (cl, cr))
    for c in p.get_components_by_class(unreal.PrimitiveComponent):
        if not isinstance(c, (unreal.SkeletalMeshComponent, unreal.StaticMeshComponent)):
            continue
        m = c.get_skeletal_mesh_asset() if isinstance(c, unreal.SkeletalMeshComponent) else c.static_mesh
        extra = ""
        if isinstance(c, unreal.SkeletalMeshComponent):
            inst = c.get_anim_instance()
            extra = " mode=%s anim=%s pos=%.2f playing=%s" % (c.get_animation_mode(), inst.get_class().get_name() if inst else None,
                    c.get_position() if hasattr(c, "get_position") else -1, c.is_playing() if hasattr(c, "is_playing") else "?")
            try:
                extra += " root=%s" % (c.get_socket_location("root") - cl)
            except Exception:
                pass
        out.append("%s mesh=%s vis=%s hidden=%s rel=%s world-cam=%s%s" % (c.get_name(), m.get_name() if m else None, c.is_visible(),
                   c.get_editor_property("hidden_in_game"), c.get_editor_property("relative_location"), c.get_world_location() - cl, extra))
    for n in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.Actor):
        for nc in n.get_components_by_class(unreal.NiagaraComponent):
            d = (nc.get_world_location() - cl).length()
            if d < 600:
                out.append("niagara %s on %s dist=%.0f active=%s asset=%s" % (nc.get_name(), n.get_name(), d, nc.is_active(),
                           nc.get_asset().get_name() if nc.get_asset() else None))

except Exception:
    import traceback; out.append(traceback.format_exc())
open(unreal.Paths.project_saved_dir() + "NV_pie_gun_diag.txt", "w").write("\n".join(out))
