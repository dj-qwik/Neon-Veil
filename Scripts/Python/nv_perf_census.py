"""Level census for optimisation: lights (by type/shadow/radius), primitive counts by folder, emissive boxes."""
import unreal, collections
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
O = []
lights = collections.Counter(); shadow = collections.Counter(); byfolder = collections.Counter(); lf = collections.Counter()
smc = collections.Counter(); shadowmesh = 0; meshes = 0
for a in EAS.get_all_level_actors():
    folder = str(a.get_folder_path()) or "(none)"
    byfolder[folder] += 1
    for c in a.get_components_by_class(unreal.LightComponent):
        k = type(c).__name__
        lights[k] += 1
        if c.get_editor_property("cast_shadows"): shadow[k] += 1
        lf[folder] += 1
    for c in a.get_components_by_class(unreal.StaticMeshComponent):
        meshes += 1
        if c.get_editor_property("cast_shadow"): shadowmesh += 1
        smc[folder] += 1
O.append(f"lights {dict(lights)} shadow-casting {dict(shadow)}")
O.append("lights by folder: " + ", ".join(f"{k}:{v}" for k, v in lf.most_common(25)))
O.append(f"static mesh comps {meshes}, shadow casting {shadowmesh}")
O.append("meshes by folder: " + ", ".join(f"{k}:{v}" for k, v in smc.most_common(30)))
O.append("actors by folder: " + ", ".join(f"{k}:{v}" for k, v in byfolder.most_common(30)))
open(unreal.Paths.project_saved_dir() + "NV_perf_census.txt", "w").write("\n".join(O))
