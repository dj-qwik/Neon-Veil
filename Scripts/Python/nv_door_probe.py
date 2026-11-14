"""Inspect station BP doors (vars + components). Report: Saved/NV_door_probe.txt"""
import unreal
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
out = []
for a in EAS.get_all_level_actors():
    if a.get_class().get_name().startswith("BP_Door"):
        l = a.get_actor_location()
        out.append(f"== {a.get_actor_label()} {a.get_class().get_name()} at ({l.x:.0f},{l.y:.0f},{l.z:.0f}) yaw {a.get_actor_rotation().yaw:.0f} hidden={a.is_hidden_ed()}")
        cls = a.get_class()
        for p in ("locked", "is_locked", "b_locked", "open", "auto_open", "door_locked", "Locked", "IsLocked"):
            try:
                out.append(f"   {p} = {a.get_editor_property(p)}")
            except Exception:
                pass
        for c in a.get_components_by_class(unreal.PrimitiveComponent):
            rl = c.get_editor_property("relative_location")
            out.append(f"   {c.get_name()} {c.get_class().get_name()} rel ({rl.x:.0f},{rl.y:.0f},{rl.z:.0f}) col {c.get_collision_enabled()} prof {c.get_collision_profile_name()}")
open(unreal.Paths.project_saved_dir() + "NV_door_probe.txt", "w").write("\n".join(out))
