"""PIE: scale all NPC garments. argv[2] = 'sx sz'."""
import sys, unreal
UES = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
w = UES.get_game_world()
sx, sz = (float(v) for v in sys.argv[2].split())
for a in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.Character):
    for c in a.get_components_by_class(unreal.SceneComponent):
        if c.get_name().startswith("Garment"):
            c.set_relative_scale3d(unreal.Vector(sx, sx, sz))
