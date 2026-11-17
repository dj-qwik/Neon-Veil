import unreal
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
out = []
try:
    sk = unreal.load_asset("/Game/RetroFuturisticSoldier/Meshes/SKM_Soldier_Manny")
    ours = unreal.load_asset("/Game/Characters/Mannequins/Meshes/SK_Mannequin")
    out.append("ours compat: %s" % [str(s) for s in ours.get_editor_property("compatible_skeletons")])
    out.append("theirs %s compat: %s" % (sk.get_editor_property('skeleton').get_path_name(), [str(s) for s in sk.get_editor_property("skeleton").get_editor_property("compatible_skeletons")]))
    for a in EAS.get_all_level_actors():
        if not a.get_actor_label().startswith("C_Target_"):
            continue
        c = {x.get_name(): x for x in a.get_components_by_class(unreal.SceneComponent)}
        f = c.get("Figure")
        if not f:
            continue
        ad = f.get_editor_property("animation_data")
        m = f.get_skeletal_mesh_asset()
        out.append("%s mesh=%s mode=%s anim=%s head=%s" % (a.get_actor_label(), m.get_name() if m else None, f.get_editor_property("animation_mode"),
                   ad.get_editor_property("anim_to_play").get_name() if ad.get_editor_property("anim_to_play") else None,
                   f.get_socket_location("head") - a.get_actor_location()))

except Exception:
    import traceback; out.append(traceback.format_exc())
open(unreal.Paths.project_saved_dir() + "NV_fig_diag.txt", "w").write("\n".join(out))
