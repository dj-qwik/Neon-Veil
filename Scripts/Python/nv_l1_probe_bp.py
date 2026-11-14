"""List components (SCS + inherited) and editable variables of a few blueprints. Report: Saved/NV_l1_probe_bp.txt"""
import unreal
out = []
BPS = ["/Game/SciFiTramStation/Blueprints/BP_Tram", "/Game/SciFiTramStation/Blueprints/BP_Door_A",
       "/Game/ModularScifiInterior/Blueprints/BP_Door_A", "/Game/ModularScifiInterior/Blueprints/BP_Corridoor",
       "/Game/KINEMATION/Sci-fi_FPS_Pack/Blueprints/BP_SciFi_Character"]
SDS = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
for p in BPS:
    bp = unreal.load_asset(p)
    if not bp:
        out.append(f"{p}: missing"); continue
    out.append(f"== {p}")
    try:
        handles = SDS.k2_gather_subobject_data_for_blueprint(bp)
        for h in handles:
            d = SDS.k2_find_subobject_data_from_handle(h)
            o = unreal.SubobjectDataBlueprintFunctionLibrary.get_object(d)
            if o:
                extra = ""
                if isinstance(o, unreal.StaticMeshComponent) and o.static_mesh:
                    extra = o.static_mesh.get_name() + f" rel={o.get_editor_property('relative_location')}"
                out.append(f"   {o.get_class().get_name()} {o.get_name()} {extra}")
    except Exception as e:
        out.append(f"   gather failed: {e}")
    cdo = unreal.get_default_object(bp.generated_class())
    for n in dir(cdo):
        pass
open(unreal.Paths.project_saved_dir() + "NV_l1_probe_bp.txt", "w").write("\n".join(out))
