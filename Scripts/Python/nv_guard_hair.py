"""Guards: remove the scalp groom that pokes through the P05 helmet (brows/lashes stay).
Report: Saved/NV_guard_hair.txt"""
import unreal
OUT = unreal.Paths.project_saved_dir() + "NV_guard_hair.txt"
log = []
BP = "/Game/NeonVeil/Characters/GuardMH/Guard/BP_Guard"
bp = unreal.load_asset(BP)
sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
handles = sds.k2_gather_subobject_data_for_blueprint(bp)
changed = 0
for h in handles:
    data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h)
    obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_object(data)
    if obj is None:
        continue
    name = obj.get_name()
    line = "%s  %s" % (name, obj.get_class().get_name())
    if obj.get_class().get_name() == "GroomComponent":
        g = obj.get_editor_property("groom_asset")
        line += "  groom=%s" % (g.get_path_name() if g else None)
        low = name.lower()
        if low.startswith("hair") and g is not None:
            obj.set_editor_property("groom_asset", None)
            obj.set_editor_property("visible", False)
            line += "  -> CLEARED"
            changed += 1
    elif isinstance(obj, unreal.SkeletalMeshComponent):
        m = obj.get_editor_property("skeletal_mesh_asset") if hasattr(obj, "skeletal_mesh_asset") else None
        line += "  mesh=%s" % (m.get_name() if m else None)
    log.append(line)
if changed:
    unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    unreal.EditorAssetLibrary.save_loaded_asset(bp)
log.append("changed %d" % changed)
open(OUT, "w").write("\n".join(log))
