"""Point the editor viewport down the street at the Veyra Central hub facade. Args: x y z yaw pitch"""
import unreal, sys
a = [float(v) for v in sys.argv[2:]] if len(sys.argv) > 6 else [7046, -10400, -11250, 90, 18]
unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).set_level_viewport_camera_info(unreal.Vector(a[0], a[1], a[2]), unreal.Rotator(0, a[4], a[3]))
