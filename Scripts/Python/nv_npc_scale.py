"""PIE: scale garments of NPCs (label prefix or 'all'). argv[2] = 'prefix sx sz'."""
import sys, unreal
UES = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
w = UES.get_game_world()
pre, sx, sz = sys.argv[2].split()
sx, sz = float(sx), float(sz)
for a in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.Character):
    if pre != "all" and not a.get_actor_label().startswith(pre):
        continue
    for c in a.get_components_by_class(unreal.SceneComponent):
        if c.get_name().startswith("Garment"):
            c.set_relative_scale3d(unreal.Vector(sx, sx, sz))
