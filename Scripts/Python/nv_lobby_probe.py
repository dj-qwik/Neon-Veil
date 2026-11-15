import unreal
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
OUT = []
for a in EAS.get_all_level_actors():
    lab = a.get_actor_label()
    if any(k in lab for k in ("Lobby_Ceil", "Lobby_LightBar", "Lobby_PL", "Lobby_Fill", "Cab_")):
        l = a.get_actor_location(); r = a.get_actor_rotation()
        extra = ""
        smc = a.get_component_by_class(unreal.StaticMeshComponent)
        if smc:
            m = smc.get_editor_property("static_mesh")
            extra = f"mesh {m.get_name() if m else None} vis {smc.is_visible()} mats {[x.get_name() if x else None for x in smc.get_materials()]}"
        lc = a.get_component_by_class(unreal.LocalLightComponent)
        if lc:
            extra = f"cd {lc.intensity} r {lc.attenuation_radius} vis {lc.is_visible()} mdd {lc.get_editor_property('max_draw_distance')}"
        OUT.append(f"{lab} @({l.x:.0f},{l.y:.0f},{l.z:.0f}) rot({r.roll:.0f},{r.pitch:.0f},{r.yaw:.0f}) folder {a.get_folder_path()} {extra}")
open(unreal.Paths.project_saved_dir() + "NV_lobby_probe.txt", "w").write("\n".join(sorted(OUT)))
