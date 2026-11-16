"""Platform Two control room: the "restore power" console becomes a wall breaker box (NVBreakerPanel: steel housing,
fuse row, hazard strip, red/green lamps, a throw lever that slams down when used). Takes over I_PowerPanel's prompt,
objective, event and lines, then replaces it on the room's east wall. Called from nv_station_route.py; safe to run on
its own (idempotent). Report: Saved/NV_breaker_panel.txt"""
import unreal
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
EAL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary
AT = unreal.AssetToolsHelpers.get_asset_tools()
V = unreal.Vector
OUT = []
D = "/Game/NeonVeil/Materials/Prologue"
WALL = (1323.0, -3050.0, 0.0)     # east wall of the control room: inner wall panel face x 1324 (SM_Wall7), faces -X
YAW = 180.0

def mi(name, parent, vec, scal):
    path = f"{D}/{name}"
    m = unreal.load_asset(path) if EAL.does_asset_exist(path) else AT.create_asset(name, D, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    MEL.set_material_instance_parent(m, unreal.load_asset(parent))
    for k, v in vec.items():
        MEL.set_material_instance_vector_parameter_value(m, k, unreal.LinearColor(*v, 1))
    for k, v in scal.items():
        MEL.set_material_instance_scalar_parameter_value(m, k, v)
    EAL.save_loaded_asset(m)
    return m
PAINT = "/Game/NeonVeil/Vehicles/M_NV_CarPaint"
GLOW = f"{D}/M_NV_Glow"
looks = {
    "housing_material": mi("MI_NV_Breaker_Steel", PAINT, {"Paint": (0.09, 0.095, 0.1)}, {"Metallic": 0.85, "Roughness": 0.42}),
    "plate_material": mi("MI_NV_Breaker_Plate", PAINT, {"Paint": (0.2, 0.21, 0.22)}, {"Metallic": 0.7, "Roughness": 0.5}),
    "lever_material": mi("MI_NV_Breaker_Lever", PAINT, {"Paint": (0.03, 0.03, 0.035)}, {"Metallic": 0.6, "Roughness": 0.35}),
    "hazard_material": mi("MI_NV_Breaker_Hazard", PAINT, {"Paint": (0.75, 0.48, 0.02)}, {"Metallic": 0.1, "Roughness": 0.55}),
    "fuse_material": mi("MI_NV_Breaker_Fuse", GLOW, {"Color": (0.25, 0.75, 1.0)}, {"Glow": 2.5}),
    "red_lit_material": mi("MI_NV_Breaker_RedLit", GLOW, {"Color": (1.0, 0.06, 0.03)}, {"Glow": 18.0}),
    "green_lit_material": mi("MI_NV_Breaker_GreenLit", GLOW, {"Color": (0.1, 1.0, 0.25)}, {"Glow": 18.0}),
    "lamp_off_material": mi("MI_NV_Breaker_LampOff", PAINT, {"Paint": (0.02, 0.02, 0.02)}, {"Metallic": 0.0, "Roughness": 0.3}),
}
old = None
for a in EAS.get_all_level_actors():
    if a.get_actor_label() == "I_PowerPanel":
        old = a
props = {}
tags, folder = [unreal.Name("NVROUTE")], "P_Route"
if old:
    for k in ("prompt", "completion_event_tag", "required_active_objective", "lines_on_use", "use_sound", "single_use"):
        try:
            props[k] = old.get_editor_property(k)
        except Exception as e:
            OUT.append(f"skip {k}: {e}")
    tags, folder = list(old.tags), old.get_folder_path()
    OUT.append(f"replacing {old.get_class().get_name()} at {old.get_actor_location()}")
    EAS.destroy_actor(old)
b = EAS.spawn_actor_from_class(unreal.NVBreakerPanel, V(*WALL), unreal.Rotator(roll=0.0, pitch=0.0, yaw=YAW))
b.set_actor_label("I_PowerPanel"); b.set_folder_path(folder); b.tags = tags
for k, v in props.items():
    b.set_editor_property(k, v)
if not props:
    b.set_editor_property("prompt", unreal.Text("Restore Platform One power"))
    b.set_editor_property("required_active_objective", "M00P-O06")
for k, v in looks.items():
    b.set_editor_property(k, v)
b.set_editor_property("prompt", unreal.Text("Throw the breaker"))
OUT.append(f"breaker at {b.get_actor_location()} yaw {b.get_actor_rotation().yaw:.0f}, props {sorted(props)}")
open(unreal.Paths.project_saved_dir() + "NV_breaker_panel.txt", "w").write("\n".join(OUT))
if __name__ == "__main__":
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
