"""List the skybridge (space A) actors in the Glass Crown map. Report: Saved/NV_skybridge_survey.txt"""
import unreal
LES = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
MAP = "/Game/NeonVeil/Maps/M00/L_M00_GlassCrown"
if not unreal.EditorLevelLibrary.get_editor_world().get_path_name().startswith(MAP):
    LES.load_level(MAP)
out = []
for a in EAS.get_all_level_actors():
    lab = a.get_actor_label()
    o, e = a.get_actor_bounds(False)
    if lab.startswith("A_") or (-1500 < o.x < 3600 and -1600 < o.y < 1600 and -200 < o.z < 1500 and isinstance(a, unreal.StaticMeshActor)):
        m = ""; mats = ""
        if isinstance(a, unreal.StaticMeshActor) and a.static_mesh_component.static_mesh:
            c = a.static_mesh_component
            m = c.static_mesh.get_name()
            mats = ",".join((x.get_name() if x else "-") for x in c.get_materials())
        out.append(f"{lab}|{a.get_class().get_name()}|{a.get_folder_path()}|{m}|{mats}|o=({o.x:.0f},{o.y:.0f},{o.z:.0f}) e=({e.x:.0f},{e.y:.0f},{e.z:.0f})")
for lab in ("B_Floor", "B_Ceiling"):
    pass
open(unreal.Paths.project_saved_dir() + "NV_skybridge_survey.txt", "w").write("\n".join(sorted(out)))
