"""BP_Tram: list mesh components (name, mesh, relative location, materials + their texture parameters) to find the
destination display and the hand scanner. Saved/NV_tram_probe2.txt"""
import unreal
SDS = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
BFL = unreal.SubobjectDataBlueprintFunctionLibrary
out = []
bp = unreal.load_asset("/Game/SciFiTramStation/Blueprints/BP_Tram")
seen_m = set()
for h in SDS.k2_gather_subobject_data_for_blueprint(bp):
    o = BFL.get_object(BFL.get_data(h))
    if not isinstance(o, unreal.StaticMeshComponent):
        if o:
            out.append("# %s %s" % (o.get_name(), o.get_class().get_name()))
        continue
    sm = o.get_editor_property("static_mesh")
    mats = []
    for i in range(o.get_num_materials()):
        m = o.get_material(i)
        mats.append(m.get_name() if m else None)
        if m and m.get_name() not in seen_m:
            seen_m.add(m.get_name())
            tex = []
            if isinstance(m, unreal.MaterialInstance):
                for tp in m.get_editor_property("texture_parameter_values"):
                    t = tp.get_editor_property("parameter_value")
                    tex.append("%s=%s" % (tp.get_editor_property("parameter_info").get_editor_property("name"), t.get_path_name() if t else None))
            out.append("   MAT %s (%s) %s" % (m.get_path_name(), m.get_class().get_name(), tex))
    out.append("%s mesh=%s rel=%s mats=%s" % (o.get_name(), sm.get_path_name() if sm else None, o.get_editor_property("relative_location"), mats))
open(unreal.Paths.project_saved_dir() + "NV_tram_probe2.txt", "w").write("\n".join(out))
