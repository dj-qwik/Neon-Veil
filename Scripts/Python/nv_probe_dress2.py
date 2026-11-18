"""Probe for dressing pass 2: holoscreens, lift cab screen parent, benches, sit animations, crowd body shapes,
prop sizes for the breaker rebuild. Report: Saved/NV_probe_dress2.txt"""
import unreal
OUT = []
def log(*a):
    OUT.append(" ".join(str(x) for x in a))
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
UES = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
AR = unreal.AssetRegistryHelpers.get_asset_registry()
def f(v):
    return "(%d,%d,%d)" % (v.x, v.y, v.z)
ACTORS = list(EAS.get_all_level_actors())

log("== holoscreens / signs")
for a in ACTORS:
    for c in a.get_components_by_class(unreal.StaticMeshComponent):
        sm = c.static_mesh
        if sm and ("Holoscreen" in sm.get_name() or "Sign_A" in sm.get_name()):
            o, e = a.get_actor_bounds(False)
            par = a.get_attach_parent_actor()
            log(a.get_actor_label(), a.get_class().get_name(), sm.get_name(), "loc", f(c.get_world_location()), "yaw", round(c.get_world_rotation().yaw),
                "scale", c.get_world_scale(), "bounds", f(o), f(e), "mats", [m.get_name() if m else None for m in c.get_materials()],
                "parent", par.get_actor_label() if par else None, "folder", a.get_folder_path())

log("== cab screen + lift")
for a in ACTORS:
    l = a.get_actor_label()
    if l.startswith("Cab_") or "Lift" in a.get_class().get_name() or l.startswith("Lift"):
        par = a.get_attach_parent_actor()
        log(l, a.get_class().get_name(), f(a.get_actor_location()), "parent", par.get_actor_label() if par else None,
            "root", a.root_component.get_name() if a.root_component else None, "mob", a.root_component.mobility if a.root_component else None)

log("== benches")
for a in ACTORS:
    names = [c.static_mesh.get_name() for c in a.get_components_by_class(unreal.StaticMeshComponent) if c.static_mesh]
    if any("Bench" in n or "Seat" in n for n in names) or "Bench" in a.get_class().get_name():
        o, e = a.get_actor_bounds(False)
        log(a.get_actor_label(), a.get_class().get_name(), names[:3], "loc", f(a.get_actor_location()), "yaw", round(a.get_actor_rotation().yaw), "bounds", f(o), f(e))

log("== sit-like animations")
flt = unreal.ARFilter(class_paths=[unreal.TopLevelAssetPath("/Script/Engine", "AnimSequence")], recursive_classes=True)
for ad in AR.get_assets(flt):
    n = str(ad.asset_name).lower()
    if any(k in n for k in ("sit", "seat", "bench", "chair", "idle_talk", "phone", "lean", "wait")):
        log("  ", ad.package_name)

log("== crowd assembled looks")
for p in sorted(str(x) for x in AR.get_sub_paths("/MetaHumanCrowdContent/Characters/Assembled", False)):
    log("  ", p)

log("== prop sizes")
for p in ("/Game/ModularScifiInterior/Meshes/Props/SM_Pipes_A", "/Game/ModularScifiInterior/Meshes/Props/SM_Monitor_A",
          "/Game/ModularScifiInterior/Meshes/Props/SM_Monitor_B", "/Game/ModularScifiInterior/Meshes/Props/SM_Monitor_Wide",
          "/Game/ModularScifiInterior/Meshes/Props/SM_DoorPanel_A2", "/Game/ModularScifiInterior/Meshes/Props/SM_Wall_C_Light",
          "/Game/ModularScifiInterior/Meshes/Walls/SM_Wall_Fan", "/Game/ModularScifiInterior/Meshes/Walls/SM_Wall_FanTrim",
          "/Game/SciFiTramStation/Meshes/SM_WiresWall_A", "/Game/SciFiTramStation/Meshes/SM_WiresWall_B",
          "/Game/SciFiTramStation/Meshes/SM_Wire_A", "/Game/SciFiTramStation/Meshes/SM_Vent", "/Game/SciFiTramStation/Meshes/SM_VentSmall",
          "/Game/SciFiTramStation/Meshes/SM_Box_B", "/Game/SciFiTramStation/Meshes/SM_Sign_A", "/Game/SciFiTramStation/Meshes/SM_Light_C",
          "/Game/SciFiTramStation/Meshes/SM_Light_A", "/Game/SciFiTramStation/Meshes/SM_Light_B"):
    m = unreal.load_asset(p)
    if m:
        b = m.get_bounding_box()
        log("  ", m.get_name(), f(b.min), f(b.max), [s.material_slot_name for s in m.static_materials],
            [s.material_interface.get_name() if s.material_interface else None for s in m.static_materials])

for lab in ("S_OpsCorridor", "I_CrewPass", "I_PowerPanel", "SM_Crate_A9"):
    for a in ACTORS:
        if a.get_actor_label() == lab:
            o, e = a.get_actor_bounds(False)
            log(lab, f(a.get_actor_location()), "yaw", round(a.get_actor_rotation().yaw), "bounds", f(o), f(e))
            for c in a.get_components_by_class(unreal.PrimitiveComponent):
                log("    comp", c.get_name(), c.get_collision_enabled(), c.get_collision_profile_name(),
                    c.get_collision_response_to_channel(unreal.CollisionChannel.ECC_VISIBILITY) if hasattr(c, "get_collision_response_to_channel") else "")
# what does a visibility trace from the approach hit?
W = UES.get_editor_world()
for start in ((6730, 4600, 560), (6790, 4500, 560), (6850, 4620, 560)):
    hit = unreal.SystemLibrary.line_trace_single(W, unreal.Vector(*start), unreal.Vector(6720, 4780, 480), unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,
                                                 True, [], unreal.DrawDebugTrace.NONE, True)
    if hit:
        t = hit.to_tuple()
        log("trace", start, "->", t[9].get_actor_label() if t[9] else None, t[10].get_name() if t[10] else None, f(t[5]))
open(unreal.Paths.project_saved_dir() + "NV_probe_dress2.txt", "w").write("\n".join(OUT))
