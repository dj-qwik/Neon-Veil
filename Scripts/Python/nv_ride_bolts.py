"""Set the Crown Line chase gunfire bolt size on the ride director in L_M00_GlassCrown and save (same values as
nv_ride_director.py, without re-running the whole director setup)."""
import unreal
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
LES = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
for a in EAS.get_all_level_actors():
    if isinstance(a, unreal.NVTramRideDirector):
        a.set_editor_property("bolt_thickness", 0.32)
        a.set_editor_property("bolt_length", 800.0)
        unreal.log("NV bolts set on %s" % a.get_actor_label())
LES.save_current_level()
