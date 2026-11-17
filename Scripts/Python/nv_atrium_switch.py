"""Glass Crown atrium: a console on each side of the orrery holo-table toggles the room between "show" (dim,
orrery on) and "work lights" (ceiling lights x BRIGHT back to standard, full-brightness materials, holograms off).
Needs build ga44+ (NVRoomLightSwitch). Args: [console yaw offset; run with 180 - the SM_Console screen faces its local -X]. Idempotent. Report: Saved/NV_atrium_switch.txt"""
import sys
import unreal
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
AR = unreal.AssetRegistryHelpers.get_asset_registry()
V, R = unreal.Vector, unreal.Rotator
OUT = []
def log(*a): OUT.append(" ".join(str(x) for x in a))
args = [a for a in sys.argv[1:] if not a.endswith(".py")]
YAW = float(args[0]) if args else 0.0
FOLDER = "B_Atrium/LightSwitch"
ATRIUM = (3500, 6300, -1100, 1100)

def by_label(l):
    return next((a for a in EAS.get_all_level_actors() if a.get_actor_label() == l), None)

def ground(x, y, top=500.0):
    w = unreal.EditorLevelLibrary.get_editor_world()
    hit = unreal.SystemLibrary.line_trace_single(w, V(x, y, top), V(x, y, -200), unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,
                                                 True, [], unreal.DrawDebugTrace.NONE, True)
    if hit:
        vs = [v for v in hit.to_tuple() if isinstance(v, unreal.Vector)]
        if vs:
            return vs[0].z
    return 0.0

def sound(*prefer):
    f = unreal.ARFilter(package_paths=["/Game"], recursive_paths=True,
                        class_paths=[unreal.TopLevelAssetPath("/Script/Engine", "SoundCue"), unreal.TopLevelAssetPath("/Script/Engine", "SoundWave")])
    hits = {str(d.asset_name): str(d.package_name) for d in AR.get_assets(f)}
    for p in prefer:
        for n, path in sorted(hits.items()):
            if p.lower() in n.lower():
                return unreal.load_asset(path)
    return None

try:
    for a in EAS.get_all_level_actors():
        if str(a.get_folder_path()) == FOLDER:
            a.destroy_actor()
    base = by_label("B_Orrery_Base")
    bc = base.get_actor_location()
    console = unreal.load_asset("/Game/ModularScifiInterior/Meshes/Props/SM_Console")
    panels = []
    for side, sy in (("S", -1), ("N", 1)):
        y = bc.y + sy * 330.0
        z = ground(bc.x, y)
        # console stands outside the table, screen facing outward toward whoever walks up
        p = EAS.spawn_actor_from_class(unreal.NVInteractableActor, V(bc.x, y, z), R(yaw=(90.0 if sy > 0 else -90.0) + YAW))
        p.set_actor_label("B_LightConsole_" + side)
        p.set_folder_path(FOLDER)
        m = p.get_editor_property("mesh")
        m.set_static_mesh(console)
        p.set_editor_property("single_use", False)
        p.set_editor_property("prompt", unreal.Text("Raise room lights"))
        panels.append(p)
        log("console", side, p.get_actor_location(), "ground z", z)

    lights = [by_label("B_Light%d" % i) for i in range(4)]
    lights = [l for l in lights if l]
    mats = []
    for a in EAS.get_all_level_actors():
        l = a.get_actor_location()
        if not (ATRIUM[0] - 100 <= l.x <= ATRIUM[1] + 100 and ATRIUM[2] - 100 <= l.y <= ATRIUM[3] + 100):
            continue
        for c in a.get_components_by_class(unreal.StaticMeshComponent):
            if any(c.get_material(i) and c.get_material(i).get_name().endswith("_Atrium") for i in range(c.get_num_materials())):
                mats.append(a)
                break
    holos = [h for h in (by_label("B_Orrery"), by_label("B_Orrery_Beam")) if h]

    s = EAS.spawn_actor_from_class(unreal.NVRoomLightSwitch, V(bc.x, bc.y, bc.z + 300), R())
    s.set_actor_label("B_AtriumLightSwitch")
    s.set_folder_path(FOLDER)
    s.set_editor_property("panels", panels)
    s.set_editor_property("lights", lights)
    s.set_editor_property("bright_scale", 6.3)
    s.set_editor_property("material_actors", mats)
    s.set_editor_property("holograms", holos)
    up = sound("PowerUp", "Power_Up", "SwitchOn", "Switch", "ScifiDoor_Slow")
    dn = sound("PowerDown", "Power_Down", "SwitchOff", "Switch", "ScifiDoor_SlowShut")
    s.set_editor_property("lights_up_sound", up)
    s.set_editor_property("show_sound", dn)
    # ElevenLabs hologram flicker one-shots (Art/Audio/Holo), imported non-looping
    import os
    src = os.path.join(unreal.Paths.project_dir(), "Art", "Audio", "Holo")
    def imp(name):
        f = os.path.join(src, name + ".wav")
        if not os.path.exists(f):
            return None
        t = unreal.AssetImportTask()
        t.filename = f; t.destination_path = "/Game/NeonVeil/Audio/Holo"; t.destination_name = name
        t.replace_existing = True; t.automated = True; t.save = True
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])
        return unreal.load_asset("/Game/NeonVeil/Audio/Holo/" + name)
    s.set_editor_property("hologram_off_sound", imp("SW_NV_HoloFlickerOff"))
    s.set_editor_property("hologram_on_sound", imp("SW_NV_HoloFlickerOn"))
    log("holo sounds", s.get_editor_property("hologram_off_sound"), s.get_editor_property("hologram_on_sound"))
    log("switch: lights", len(lights), "material actors", len(mats), "holograms", [h.get_actor_label() for h in holos])
    log("sounds", up.get_path_name() if up else None, dn.get_path_name() if dn else None)
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    log("saved")
except Exception:
    import traceback
    log(traceback.format_exc())
open(unreal.Paths.project_saved_dir() + "NV_atrium_switch.txt", "w").write("\n".join(OUT))
