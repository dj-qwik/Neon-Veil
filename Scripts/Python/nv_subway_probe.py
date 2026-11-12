"""Inspect Dekogon subway kit pieces (bounds, BP components, BP vars/functions) + current tram actors.
Report: Saved/NV_subway_probe.txt"""
import unreal
out = []
EAL = unreal.EditorAssetLibrary
for p in EAL.list_assets("/Game/SubwayTrain/Meshes/Structure", recursive=False):
    m = unreal.load_asset(p)
    if isinstance(m, unreal.StaticMesh):
        b = m.get_bounding_box()
        out.append("SM %-42s min(%6.0f,%6.0f,%6.0f) max(%6.0f,%6.0f,%6.0f) mats=%d" % (m.get_name(), b.min.x, b.min.y, b.min.z, b.max.x, b.max.y, b.max.z, len(m.static_materials)))
SDS = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
BFL = unreal.SubobjectDataBlueprintFunctionLibrary
for p in EAL.list_assets("/Game/SubwayTrain/Blueprints", recursive=False):
    bp = unreal.load_asset(p.split(".")[0])
    if not isinstance(bp, unreal.Blueprint):
        continue
    out.append("BP %s" % bp.get_name())
    for h in SDS.k2_gather_subobject_data_for_blueprint(bp):
        d = BFL.get_data(h); o = BFL.get_object(d)
        if isinstance(o, unreal.SceneComponent):
            extra = ""
            if isinstance(o, unreal.StaticMeshComponent) and o.get_editor_property("static_mesh"):
                extra = o.get_editor_property("static_mesh").get_name()
            t = o.get_editor_property("relative_location"); r = o.get_editor_property("relative_rotation")
            try:
                par = str(BFL.get_variable_name(d))
            except Exception:
                par = o.get_name()
            out.append("    %-28s %-24s loc(%.0f,%.0f,%.0f) rot(%.0f,%.0f,%.0f) %s" % (par, o.get_class().get_name(), t.x, t.y, t.z, r.pitch, r.yaw, r.roll, extra))
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    lab = a.get_actor_label()
    if lab.startswith(("A_Tram", "C00_", "PlayerStart")):
        o, e = a.get_actor_bounds(False)
        out.append("ACT %-22s %s c(%.0f,%.0f,%.0f) e(%.0f,%.0f,%.0f) mob=%s" % (lab, a.get_class().get_name(), o.x, o.y, o.z, e.x, e.y, e.z,
            a.root_component.get_editor_property("mobility") if a.root_component else None))
        if a.get_class().get_name() == "NVTramArrival":
            out.append("    parts %s" % [x.get_actor_label() for x in a.get_editor_property("parts") if x])
open(unreal.Paths.project_saved_dir() + "NV_subway_probe.txt", "w").write("\n".join(out))
