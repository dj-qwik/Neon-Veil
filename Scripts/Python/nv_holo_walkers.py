"""NEON VEIL - hologram combatants walk their patrols (needs the ANVTrainingTarget figure code, build ga33+).
Sets idle/walk loops on BP_NVTrainingTarget_Test; the rifle rides hand_r with the Kestrel's
measured grip, so it stays in the hands through the walk cycle.
Report: Saved/NV_holo_walkers.txt"""
import unreal

OUT = []
EAL = unreal.EditorAssetLibrary
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
BP_PATH = "/Game/NeonVeil/Tests/BP_NVTrainingTarget_Test"
IDLE = "/Game/Characters/Mannequins/Anims/Rifle/MF_Rifle_Idle_ADS"
WALK = "/Game/Characters/Mannequins/Anims/Rifle/Walk/MF_Rifle_Walk_Fwd"

def main():
    # The Kestrel's measured third-person grip on Manny's hand_r (same Gepard mesh, same template rifle anims;
    # see nv_ghost7_weapons_tp.py) - holds in both the aim idle and the walk loop.
    grip = unreal.Transform(unreal.Vector(-11.484, 3.823, 7.540), unreal.Rotator(roll=8.95, pitch=2.41, yaw=79.74), unreal.Vector(1, 1, 1))
    walk = unreal.load_asset(WALK)
    OUT.append("walk anim %s" % (walk.get_path_name() if walk else "MISSING"))
    bp = unreal.load_asset(BP_PATH)
    cdo = unreal.get_default_object(bp.generated_class())
    cdo.set_editor_property("figure_idle_anim", unreal.load_asset(IDLE))
    cdo.set_editor_property("figure_walk_anim", walk)
    cdo.set_editor_property("figure_gun_grip", grip)
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    EAL.save_loaded_asset(bp, only_if_is_dirty=False)
    OUT.append("saved BP")

try:
    main()
except Exception:
    import traceback
    OUT.append(traceback.format_exc())
finally:
    open(unreal.Paths.project_saved_dir() + "NV_holo_walkers.txt", "w").write("\n".join(OUT))
