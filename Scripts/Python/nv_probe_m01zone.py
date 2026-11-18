"""List everything in L_M00_GlassCrown around and below the antechamber (the M01 build zone).
Report: Saved/NV_probe_m01zone.txt"""
import unreal
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
LES = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
UES = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
MAP = "/Game/NeonVeil/Maps/M00/L_M00_GlassCrown"
if not UES.get_editor_world().get_path_name().startswith(MAP):
    LES.load_level(MAP)
OUT = []
for a in EAS.get_all_level_actors():
    o, e = a.get_actor_bounds(False)
    if o.x + e.x < 14600 or o.x - e.x > 32000 or o.y + e.y < -3000 or o.y - e.y > 11000 or o.z - e.z > 3000 or o.z + e.z < -7000:
        continue
    m = ""
    if isinstance(a, unreal.StaticMeshActor) and a.static_mesh_component.static_mesh:
        m = a.static_mesh_component.static_mesh.get_name()
    OUT.append("%s [%s] %s bo=(%d,%d,%d) be=(%d,%d,%d) %s" % (a.get_actor_label(), a.get_class().get_name(), m, o.x, o.y, o.z, e.x, e.y, e.z, a.get_folder_path()))
open(unreal.Paths.project_saved_dir() + "NV_probe_m01zone.txt", "w", encoding="utf-8").write("\n".join(sorted(OUT)))
