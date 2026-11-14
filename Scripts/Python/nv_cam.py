import sys, unreal
a = [float(x) for x in sys.argv[2:8]]
unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).set_level_viewport_camera_info(unreal.Vector(a[0], a[1], a[2]), unreal.Rotator(pitch=a[3], yaw=a[4], roll=0))
