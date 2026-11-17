"""Re-initialise the editor preview pose of the hologram figures (single-node rifle idle)."""
import unreal
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
anim = unreal.load_asset("/Game/Characters/Mannequins/Anims/Rifle/MF_Rifle_Idle_ADS")
out = []
for a in EAS.get_all_level_actors():
    if not a.get_actor_label().startswith("C_Target_") or a.get_actor_label() == "C_Target_Drone":
        continue
    f = {x.get_name(): x for x in a.get_components_by_class(unreal.SceneComponent)}.get("Figure")
    f.set_animation_mode(unreal.AnimationMode.ANIMATION_SINGLE_NODE)
    f.set_animation(anim)
    f.play(True)
    f.tick_animation(0.1, False) if hasattr(f, "tick_animation") else None
    f.refresh_bone_transforms() if hasattr(f, "refresh_bone_transforms") else None
    out.append("%s head %s" % (a.get_actor_label(), f.get_socket_location("head") - a.get_actor_location()))
open(unreal.Paths.project_saved_dir() + "NV_fig_reinit.txt", "w").write("\n".join(out))
