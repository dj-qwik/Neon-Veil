"""Editor: preview AS_NV_SitBench on Manny next to a Platform One bench and shoot it from the side and front.
Saved/NV_shots/sit_side.png, sit_front.png"""
import os
import unreal
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
UES = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
for a in list(EAS.get_all_level_actors()):
    if a.get_actor_label() == "SitPreview":
        EAS.destroy_actor(a)
P = unreal.Vector(7046, -12500, -12000)
a = EAS.spawn_actor_from_class(unreal.SkeletalMeshActor, P, unreal.Rotator(roll=0, pitch=0, yaw=-90))
a.set_actor_label("SitPreview")
c = a.skeletal_mesh_component
c.set_skinned_asset_and_update(unreal.load_asset("/Game/Characters/Mannequins/Meshes/SKM_Manny_Simple"))
c.override_animation_data(unreal.load_asset("/Game/NeonVeil/Animations/Citizens/AS_NV_SitBench"), True, True, 0.0, 1.0)
c.set_update_animation_in_editor(True)
SHOTS = os.path.join(unreal.Paths.project_saved_dir(), "NV_shots")
plan = [("sit_side", unreal.Vector(7046 - 260, -12500, -11920), unreal.Rotator(roll=0, pitch=-5, yaw=0)),
        ("sit_front", unreal.Vector(7046, -12500 + 280, -11910), unreal.Rotator(roll=0, pitch=-8, yaw=-90))]
st = {"i": 0, "t": 0.0, "ph": 0, "h": None}
def tick(dt):
    st["t"] += dt
    if st["i"] >= len(plan):
        unreal.unregister_slate_post_tick_callback(st["h"]); return
    n, loc, rot = plan[st["i"]]
    if st["ph"] == 0:
        UES.set_level_viewport_camera_info(loc, rot); st["ph"], st["t"] = 1, 0.0
    elif st["ph"] == 1 and st["t"] > 1.5:
        unreal.SystemLibrary.execute_console_command(None, 'HighResShot 960x540 filename="%s"' % os.path.join(SHOTS, n + ".png").replace("\\", "/"))
        st["ph"], st["t"] = 2, 0.0
    elif st["ph"] == 2 and st["t"] > 0.6:
        st["ph"] = 0; st["i"] += 1
st["h"] = unreal.register_slate_post_tick_callback(tick)
