"""NEON VEIL - place the Director and his out-of-sync reflection in the antechamber (Bible §4 M00).
 - E_Director: BP_Director (MetaHuman, 'Walter' preset) standing at the dark glass (x = 16400), right of the
   biometric panel, back to the entrance, looking into the glass. Idle body loop.
 - E_DirectorReflection: same BP mirrored across the glass plane (x' = 2*16400 - x, scale X = -1), seen through
   the translucent smoked glass so it reads as his reflection facing the player.
 - E_ReflectionDesync (ANVDirectorReflection): when the player is in the antechamber and looks at the reflection
   for 0.6 s, the reflection holds for 0.35 s, then drifts back into step over 1.4 s. One-shot.
Re-runnable (folder E_Director cleared). Report: Saved/NV_m9_director_place.txt"""
import unreal

REPORT = []
def log(*a):
    msg = " ".join(str(x) for x in a)
    REPORT.append(msg)
    unreal.log("[NV director place] " + msg)

EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
LES = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
V = unreal.Vector
FOLDER = "E_Director"
GLASS_X = 16400.0
REAL = (16190.0, 320.0, 0.0)
IDLE = "/MetaHumanCharacter/Optional/Animation/TemplateAnimations/Technical_Loops/Idle/mhc_mh001_fmn_b_idle"

def main():
    for a in EAS.get_all_level_actors():
        if str(a.get_folder_path()) == FOLDER:
            EAS.destroy_actor(a)
    cls = unreal.load_asset("/Game/NeonVeil/Characters/Director/Director/BP_Director").generated_class()
    real = EAS.spawn_actor_from_class(cls, V(*REAL), unreal.Rotator(0, 0, 0))
    real.set_actor_label("E_Director")
    real.set_folder_path(FOLDER)
    mx = 2 * GLASS_X - REAL[0]
    mirror = EAS.spawn_actor_from_class(cls, V(mx, REAL[1], REAL[2]), unreal.Rotator(0, 0, 0))
    mirror.set_actor_scale3d(V(-1, 1, 1))
    mirror.set_actor_label("E_DirectorReflection")
    mirror.set_folder_path(FOLDER)
    log("real at", REAL, "mirror at", (mx, REAL[1], REAL[2]))

    d = EAS.spawn_actor_from_class(unreal.NVDirectorReflection, V(15600, 0, 300), unreal.Rotator())
    d.get_editor_property("volume").set_box_extent(V(800, 700, 300))
    d.set_editor_property("real", real)
    d.set_editor_property("mirror", mirror)
    anim = unreal.load_asset(IDLE)
    d.set_editor_property("idle_anim", anim)
    d.set_actor_label("E_ReflectionDesync")
    d.set_folder_path(FOLDER)
    log("idle anim", anim.get_path_name() if anim else None,
        "skeleton", anim.get_editor_property("skeleton").get_path_name() if anim else None)
    LES.save_current_level()

try:
    main()
finally:
    with open(unreal.Paths.project_saved_dir() + "NV_m9_director_place.txt", "w", encoding="utf-8") as fh:
        fh.write("\n".join(REPORT))
