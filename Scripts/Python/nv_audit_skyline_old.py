"""Lists actors in a world-space X range (default the skybridge, -1400..3500) with mesh, materials, bounds.
Report: Saved/NV_audit_skyline_old.txt"""
import unreal

X0, X1 = -200000, 200000
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
out = []
for a in EAS.get_all_level_actors():
    o, e = a.get_actor_bounds(False)
    if o.x + e.x < X0 or o.x - e.x > X1 or str(a.get_folder_path()) != "Skyline":
        continue
    line = f"{a.get_actor_label():34s} {a.get_class().get_name():22s} [{a.get_folder_path()}] o=({o.x:.0f},{o.y:.0f},{o.z:.0f}) e=({e.x:.0f},{e.y:.0f},{e.z:.0f})"
    smc = a.get_component_by_class(unreal.StaticMeshComponent)
    if smc and smc.static_mesh:
        mats = [m.get_name() if m else "-" for m in smc.get_materials()]
        line += f" mesh={smc.static_mesh.get_name()} mats={mats}"
    lc = a.get_component_by_class(unreal.LightComponent)
    if lc:
        line += f" light I={lc.intensity:.0f} col={lc.light_color.r},{lc.light_color.g},{lc.light_color.b}"
        if isinstance(lc, unreal.PointLightComponent):
            line += f" r={lc.attenuation_radius:.0f}"
    out.append(line)
out.sort()
with open(unreal.Paths.project_saved_dir() + "NV_audit_skyline_old.txt", "w", encoding="utf-8") as fh:
    fh.write("\n".join(out))
