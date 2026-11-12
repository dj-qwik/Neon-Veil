"""Diagnostic: world bounds of Art_Props actors and any actor using an emissive yellow-ish material near the sim suite."""
import unreal
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
out = []
for a in EAS.get_all_level_actors():
    f = str(a.get_folder_path())
    if f in ("Art_Props",) or a.get_actor_label().startswith(("C_", "B_Opt", "D_Opt", "E_Bio")):
        o, e = a.get_actor_bounds(False)
        mats = []
        for c in a.get_components_by_class(unreal.StaticMeshComponent):
            mats += [m.get_name() for m in c.get_materials() if m]
        out.append(f"{a.get_actor_label():34s} {f:12s} c=({o.x:.0f},{o.y:.0f},{o.z:.0f}) size=({2*e.x:.0f},{2*e.y:.0f},{2*e.z:.0f}) {mats[:3]}")
open(unreal.Paths.project_saved_dir() + "NV_diag_props.txt", "w").write("\n".join(out))
