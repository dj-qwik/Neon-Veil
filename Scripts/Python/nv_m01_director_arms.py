"""M01 story beats on top of nv_setup_m01.py (run after it, then nv_vo_hook.py M01):
 - The Director signs the order (Bible §15): revocation -> he turns to Ghost-7 -> "Director. Override this." -> he turns
   to the biometric panel and signs (console goes red, comms card) -> AION: "The Director has already approved your
   removal." -> a holo containment tube rises around him and his lift pad takes him down through the floor.
 - Name tag over the Director (M00 and the start of M01): THE DIRECTOR / DIRECTORATE CITADEL // COMMAND AUTHORITY.
 - Medical reclamation: the four graybox surgical rigs become ceiling-hung robotic arms (Black Honey robotic arm by
   Gerardo Justel, CC-BY, Fab; merged to /Game/BlackHoneyArm/SM_SM_NV_RestraintArm by Saved/nv_arm_assemble.py)
   that drop and close in on him.
 - Prologue opening title on BP_NVGameMode_Prologue.
Idempotent. Report: Saved/NV_m01_director_arms.txt"""
import json
import math
import os
import unreal

OUT = []
def log(*a): OUT.append(" ".join(str(x) for x in a))
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
LES = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
UES = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
EAL = unreal.EditorAssetLibrary
V = unreal.Vector
T = unreal.Text
MAP = "/Game/NeonVeil/Maps/M00/L_M00_GlassCrown"
FOLDER, TAG = "M01_Director", "NVM01DIR"

try:
    # ------------------------------------------------------------------ prologue title (asset only; any map loaded)
    GM = "/Game/NeonVeil/Core/BP_NVGameMode_Prologue"
    gbp = unreal.load_asset(GM)
    unreal.BlueprintEditorLibrary.compile_blueprint(gbp)
    gcdo = unreal.get_default_object(EAL.load_blueprint_class(GM))
    gcdo.set_editor_property("opening_title", T("Neon Veil"))
    gcdo.set_editor_property("opening_subtitle", T("Act I  //  The Fall"))
    gcdo.set_editor_property("opening_tagline", T("Veyra-9  ·  Veyra Central"))
    gcdo.set_editor_property("opening_delay", 1.2)
    gcdo.set_editor_property("opening_duration", 8.5)
    gbp.modify()
    EAL.save_loaded_asset(gbp, only_if_is_dirty=False)
    log("prologue title set:", gcdo.get_editor_property("opening_title"))

    if not UES.get_editor_world().get_path_name().startswith(MAP):
        LES.load_level(MAP)
    for a in list(EAS.get_all_level_actors()):
        lab = a.get_actor_label()
        if TAG in [str(t) for t in a.tags] or lab.startswith("TMP_Arm"):
            EAS.destroy_actor(a)
    ACT = {a.get_actor_label(): a for a in EAS.get_all_level_actors()}
    dr = ACT["M01_BlackProtocolDirector"]
    proj = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
    LINES = {l["id"]: l for l in json.load(open(os.path.join(proj, "Scripts", "VO", "M01_lines.json")))}

    def lines(*ids):
        out = []
        for i in ids:
            d = LINES[i]
            s = unreal.NVSubtitleLine()
            s.set_editor_property("speaker", T(d["speaker"]))
            s.set_editor_property("text", T(d["text"]))
            s.set_editor_property("duration", float(d.get("dur", 3.5)))
            out.append(s)
        return out

    def tagged(a, label):
        a.set_actor_label(label)
        a.set_folder_path(FOLDER)
        a.tags = [unreal.Name(TAG)]
        return a

    def mover(actor, offset, rot=None):
        m = unreal.NVMover()
        m.set_editor_property("actor", actor)
        m.set_editor_property("offset", offset)
        if rot:
            m.set_editor_property("rotation", rot)
        return m

    def find_sound(*keys):
        reg = unreal.AssetRegistryHelpers.get_asset_registry()
        for k in keys:
            for root in ("/Game/SciFiUISFX", "/Game/SciFi_UI_SFX_Pack_Vol_1_Holographic_Glitch_And_Bubble_Sounds", "/Game/NeonVeil/Audio"):
                for d in reg.get_assets_by_path(root, recursive=True):
                    if str(d.asset_class_path.asset_name) in ("SoundWave", "SoundCue") and k.lower() in str(d.asset_name).lower():
                        return unreal.load_asset(str(d.package_name))
        return None

    # ------------------------------------------------------------------ the Director
    director = ACT.get("E_Director")
    mirror = ACT.get("E_DirectorReflection")
    panel = ACT.get("E_BiometricPanel")
    log("director", director, "mirror", mirror, "panel", panel)
    dpos = director.get_actor_location()

    cl = EAS.spawn_actor_from_class(unreal.PointLight, V(panel.get_actor_location().x - 20, panel.get_actor_location().y, 175))
    lc = cl.point_light_component
    lc.set_intensity(900)
    lc.set_attenuation_radius(260)
    lc.set_light_color(unreal.LinearColor(0.2, 0.85, 1.0, 1))
    lc.set_cast_shadows(False)
    tagged(cl, "A_ConsoleLight")

    holo = unreal.load_asset("/Game/UndergroundSciFi/Meshes/SM_HoloTube01")      # 100 x 100 x 150, base at z 0
    tube = EAS.spawn_actor_from_class(unreal.StaticMeshActor, V(dpos.x, dpos.y, dpos.z - 360), unreal.Rotator(0, 0, 0))
    tube.static_mesh_component.set_static_mesh(holo)
    tube.static_mesh_component.set_mobility(unreal.ComponentMobility.MOVABLE)
    tube.set_actor_scale3d(V(1.6, 1.6, 2.3))
    tube.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    tube.static_mesh_component.set_cast_shadow(False)
    tagged(tube, "A_EvacTube")

    cyl = unreal.load_asset("/Engine/BasicShapes/Cylinder")
    pad = EAS.spawn_actor_from_class(unreal.StaticMeshActor, V(dpos.x, dpos.y, dpos.z + 1.5), unreal.Rotator(0, 0, 0))
    pad.static_mesh_component.set_static_mesh(cyl)
    pad.static_mesh_component.set_mobility(unreal.ComponentMobility.MOVABLE)
    pad.set_actor_scale3d(V(1.5, 1.5, 0.03))
    pad.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    pad.static_mesh_component.set_cast_shadow(False)
    padmat = unreal.load_asset("/Game/UndergroundSciFi/Materials/MI_HoloTube02")
    if padmat:
        pad.static_mesh_component.set_material(0, padmat)
    tagged(pad, "A_EvacPad")

    dr.set_editor_property("the_director", director)
    dr.set_editor_property("director_reflection", mirror)
    dr.set_editor_property("reflection_plane_x", 16400.0)
    dr.set_editor_property("director_console", panel)
    dr.set_editor_property("console_light", cl)
    dr.set_editor_property("evac_tube", mover(tube, V(0, 0, 360)))
    dr.set_editor_property("evac_platform", mover(pad, V(0, 0, -420)))
    dr.set_editor_property("revocation_lines", lines("M01_AION_01"))
    dr.set_editor_property("director_appeal_lines", lines("M01_Ghost_13"))
    dr.set_editor_property("director_approval_lines", lines("M01_AION_12"))
    dr.set_editor_property("after_director_lines", lines("M01_Ghost_01", "M01_AION_02"))
    dr.set_editor_property("signed_sender", T("The Director"))
    dr.set_editor_property("signed_channel", T("Directorate Citadel"))
    dr.set_editor_property("signed_body", T("Decommission order for asset GHOST-7: authorized."))
    dr.set_editor_property("designation_delay", 22.0)
    snd = find_sound("Confirm", "Access", "Accept", "Beep")
    if snd:
        dr.set_editor_property("sign_sound", snd)
    evs = find_sound("PowerUp", "Power_Up", "Whoosh", "Hologram")
    if evs:
        dr.set_editor_property("evac_sound", evs)
    log("sign sound", snd.get_path_name() if snd else None, "evac sound", evs.get_path_name() if evs else None)

    tag = EAS.spawn_actor_from_class(unreal.NVNameTag, V(dpos.x, dpos.y, dpos.z + 205), unreal.Rotator(0, 0, 0))
    tag.set_editor_property("display_name", T("The Director"))
    tag.set_editor_property("role_text", T("Directorate Citadel // Command authority"))
    tag.attach_to_actor(director, "", unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD, False)
    tagged(tag, "E_DirectorNameTag")

    # ------------------------------------------------------------------ restraint arms (D)
    arm = unreal.load_asset("/Game/BlackHoneyArm/SM_SM_NV_RestraintArm")
    grey = unreal.load_asset("/Game/Clinic/Materials/MaterialInstances/MI_LightGrey")
    BAY = V(16650, 7000, 0)
    CEIL = -3905.0
    S = 1.8
    ARM_YAW = 0.0   # correction if the gripper does not point along the mesh's +X
    movers = []
    for i in range(4):
        a = ACT.get(f"D_SurgicalArm_{i}")
        tip = ACT.get(f"D_SurgicalArm_{i}_Tip")
        if not a:
            continue
        if tip:
            tip.set_actor_hidden_in_game(True)
            tip.static_mesh_component.set_visibility(False)
        loc = a.get_actor_location()
        dx, dy = BAY.x - loc.x, BAY.y - loc.y
        yaw = math.degrees(math.atan2(dy, dx))
        c = a.static_mesh_component
        c.set_static_mesh(arm)
        c.set_cast_shadow(False)
        if grey:
            c.set_material(0, grey)
        # hung upside down from the ceiling (roll 180 is applied first, so the arm's reach along local +X follows yaw)
        a.set_actor_location_and_rotation(V(loc.x, loc.y, CEIL), unreal.Rotator(roll=180.0, pitch=0.0, yaw=yaw + ARM_YAW), False, True)
        a.set_actor_scale3d(V(S, S, S))
        n = math.hypot(dx, dy) or 1.0
        movers.append(mover(a, V(dx / n * 45.0, dy / n * 45.0, -150.0), unreal.Rotator(roll=0.0, pitch=0.0, yaw=0.0)))
        log("arm", i, "yaw", round(yaw), "at", loc.x, loc.y)
    dr.set_editor_property("surgical_arms", movers)

    LES.save_current_level()
    log("saved")
except Exception:
    import traceback
    log("ERROR", traceback.format_exc())
open(unreal.Paths.project_saved_dir() + "NV_m01_director_arms.txt", "w", encoding="utf-8").write("\n".join(OUT))
