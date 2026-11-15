"""Put the ejected PIE camera under a flying car. args: stream_label [instance] [below_cm] [back_cm] [side_cm]"""
import sys, unreal
lab = sys.argv[2]; idx = int(sys.argv[3]) if len(sys.argv) > 3 else 0
below = float(sys.argv[4]) if len(sys.argv) > 4 else 900; back = float(sys.argv[5]) if len(sys.argv) > 5 else 900
side = float(sys.argv[6]) if len(sys.argv) > 6 else 0
w = unreal.EditorLevelLibrary.get_pie_worlds(False)[0]
UES = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
for a in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.NVTrafficStream):
    if a.get_actor_label() != lab: continue
    isms = a.get_components_by_class(unreal.InstancedStaticMeshComponent)
    c = [i for i in isms if i.get_instance_count() > 0][0]
    t = c.get_instance_transform(idx, True)
    p = t.translation
    f = a.get_actor_forward_vector(); r = a.get_actor_right_vector()
    cam = unreal.Vector(p.x - f.x * back + r.x * side, p.y - f.y * back + r.y * side, p.z - below)
    rot = unreal.MathLibrary.find_look_at_rotation(cam, p)
    UES.set_level_viewport_camera_info(cam, rot)
