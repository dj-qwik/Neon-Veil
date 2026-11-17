"""Glass Crown: an Etherion (ModularScifiInterior) sliding door closes the sky-bridge entrance to the atrium, with a
palm-scanner panel on the bridge side. Scan palm -> Security VO -> door slides open. Needs build ga43+
(NVObjectiveDoor.OpenWhenUsed / BlockerExtent). The door also opens on its own once M00-O01 is complete, so a
checkpoint past it never locks the player out. Idempotent. Report: Saved/NV_atrium_door.txt"""
import unreal
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
AR = unreal.AssetRegistryHelpers.get_asset_registry()
V, R = unreal.Vector, unreal.Rotator
OUT = []
def log(*a): OUT.append(" ".join(str(x) for x in a))
MSI = "/Game/ModularScifiInterior/Meshes"
FOLDER = "B_Atrium/EntryDoor"
DOOR_X, FLOOR_Z = 3500.0, 0.0

def find_sound(*names):
    f = unreal.ARFilter(package_paths=["/Game"], recursive_paths=True,
                        class_paths=[unreal.TopLevelAssetPath("/Script/Engine", "SoundCue"), unreal.TopLevelAssetPath("/Script/Engine", "SoundWave")])
    hits = {str(d.asset_name): str(d.package_name) for d in AR.get_assets(f)}
    for n in names:
        if n in hits:
            return unreal.load_asset(hits[n])
    return None

def line(speaker, text, dur, comms=True, channel="Crown Security"):
    l = unreal.NVSubtitleLine()
    l.set_editor_property("speaker", unreal.Text(speaker))
    l.set_editor_property("text", unreal.Text(text))
    l.set_editor_property("duration", dur)
    l.set_editor_property("as_comms", comms)
    l.set_editor_property("channel", unreal.Text(channel))
    return l

try:
    for a in EAS.get_all_level_actors():
        if str(a.get_folder_path()) == FOLDER:
            a.destroy_actor()
    door_snd = find_sound("SC_ScifiDoor_Fast", "SC_ScifiDoor_Slow")
    log("door sound:", door_snd.get_path_name() if door_snd else None)

    # --- the door: SM_DoorFrame_A is 625 wide (local Y 0..625) x 462 tall; the two SM_Door_A leaves interlock
    d = EAS.spawn_actor_from_class(unreal.NVObjectiveDoor, V(DOOR_X, 0, FLOOR_Z), R())
    d.set_actor_label("B_EntryDoor")
    d.set_folder_path(FOLDER)
    frame = d.get_editor_property("frame")
    frame.set_static_mesh(unreal.load_asset(f"{MSI}/Doors/SM_DoorFrame_A"))
    frame.set_editor_property("relative_location", V(0, -312.5, 0))
    frame.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)   # the wall around it already blocks
    leaf = unreal.load_asset(f"{MSI}/Doors/SM_Door_A")
    pr = d.get_editor_property("panel_right")          # slides +Y
    pr.set_static_mesh(leaf)
    pr.set_editor_property("relative_location", V(0, -312.5, 0))
    pl = d.get_editor_property("panel_left")           # slides -Y (mirrored leaf, as in BP_Door_A)
    pl.set_static_mesh(leaf)
    pl.set_editor_property("relative_location", V(0, 312.5, 360))
    pl.set_editor_property("relative_rotation", R(roll=180, pitch=0, yaw=0))
    blk = d.get_editor_property("blocker")
    blk.set_editor_property("relative_location", V(0, 0, 230))
    d.set_editor_property("blocker_extent", V(22, 305, 230))
    d.set_editor_property("slide_distance", 380.0)
    d.set_editor_property("open_time", 1.1)
    d.set_editor_property("open_delay", 1.4)
    d.set_editor_property("open_sound", door_snd)
    d.set_editor_property("open_when_complete", "M00-O01")

    # --- palm scanner: the Etherion door-access panel, on the inner face of the bridge's right pilaster
    s = EAS.spawn_actor_from_class(unreal.NVInteractableActor, V(3432, 244, 135), R(yaw=-90))
    s.set_actor_label("B_EntryScanner")
    s.set_folder_path(FOLDER)
    m = s.get_editor_property("mesh")
    m.set_static_mesh(unreal.load_asset(f"{MSI}/Props/SM_DoorPanel_A2"))
    m.set_editor_property("relative_scale3d", V(1.6, 1.6, 1.6))
    s.set_editor_property("prompt", unreal.Text("Scan palm"))
    s.set_editor_property("hold_duration", 0.8)
    s.set_editor_property("single_use", True)
    s.set_editor_property("lines_on_use", [line("Security", "Palm print verified. Welcome back, Ghost-7.", 3.4)])
    beep = find_sound("SC_ScifiPanel_Beep", "SC_Beep", "SW_Beep", "SC_ScifiDoor_Fast_Shut")
    d.set_editor_property("open_when_used", [s])
    log("scanner", s.get_actor_location())

    # soft cyan wash so the panel reads from down the bridge
    gl = EAS.spawn_actor_from_class(unreal.PointLight, V(3415, 225, 175), R())
    gl.set_actor_label("B_EntryScanner_Glow")
    gl.set_folder_path(FOLDER)
    c = gl.get_component_by_class(unreal.PointLightComponent)
    c.set_editor_property("intensity_units", unreal.LightUnits.LUMENS)
    c.set_editor_property("intensity", 260.0)
    c.set_editor_property("attenuation_radius", 220.0)
    c.set_editor_property("light_color", unreal.Color(r=90, g=220, b=255, a=255))
    c.set_editor_property("cast_shadows", False)
    log("door", d.get_actor_location(), "frame", frame.static_mesh.get_name(), "leaves", leaf.get_name())
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    log("saved")
except Exception:
    import traceback
    log(traceback.format_exc())
open(unreal.Paths.project_saved_dir() + "NV_atrium_door.txt", "w").write("\n".join(OUT))
