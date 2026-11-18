"""PIE: watch the Director beat. Run at the gallery checkpoint (after nv_pie_m01.py's first pass): puts Ghost-7 in the
antechamber facing the Director, makes him invulnerable, completes M00-O04 so M01's lockdown starts."""
import unreal
w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
pc = unreal.GameplayStatics.get_player_controller(w, 0)
def cmd(c): unreal.SystemLibrary.execute_console_command(w, c, pc)
p = pc.get_controlled_pawn()
p.teleport(unreal.Vector(15880, 60, 100), unreal.Rotator(0, 0, 40))
pc.set_control_rotation(unreal.Rotator(roll=0, pitch=-2, yaw=40))
cmd("NVGod 1")
cmd("NVComplete M00-O04")
