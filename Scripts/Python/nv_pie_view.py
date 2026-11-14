"""PIE: inspect/drive the view + holster. argv[2] = 'info' | 'tp' | 'fp' | 'holster'. Report: Saved/NV_pie_view.txt"""
import sys, unreal
UES = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
w = UES.get_game_world()
p = unreal.GameplayStatics.get_player_pawn(w, 0)
arg = sys.argv[2] if len(sys.argv) > 2 else "info"
out = [f"pawn {p.get_class().get_name()}"]
if arg == "tp": p.set_third_person(True)
if arg == "fp": p.set_third_person(False)
if arg == "holster": p.get_weapons().toggle_holster()
out.append(f"holster_action={p.get_editor_property('holster_action')} view_action={p.get_editor_property('toggle_view_action')}")
out.append(f"third={p.is_third_person()} holstered={p.get_weapons().is_holstered()} weapon={p.get_weapons().get_current_weapon()}")
open(unreal.Paths.project_saved_dir() + "NV_pie_view.txt", "w").write("\n".join(out))
