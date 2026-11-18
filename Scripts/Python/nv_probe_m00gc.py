"""Probe L_M00_GlassCrown gallery + antechamber for the LANTERN core pass. Report: Saved/NV_probe_m00gc.txt"""
import unreal
OUT = []
def log(*a): OUT.append(" ".join(str(x) for x in a))
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
LES = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
UES = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
MAP = "/Game/NeonVeil/Maps/M00/L_M00_GlassCrown"
if not UES.get_editor_world().get_path_name().startswith(MAP):
    LES.load_level(MAP)
def fmt(v): return "(%d,%d,%d)" % (v.x, v.y, v.z)
for a in EAS.get_all_level_actors():
    o, e = a.get_actor_bounds(False)
    if e.x > 20000 or e.y > 20000: continue
    if o.x + e.x < 10000 or o.x - e.x > 16600: continue
    extra = ""
    if isinstance(a, unreal.StaticMeshActor):
        sm = a.static_mesh_component.static_mesh
        extra = sm.get_name() if sm else ""
    try:
        lu = a.get_editor_property("lines_on_use")
        extra += " USE=" + " | ".join("%s:%s" % (l.speaker, l.text) for l in lu)
    except Exception: pass
    log("%s [%s] loc=%s rot=%s bo=%s be=%s %s" % (a.get_actor_label(), a.get_class().get_name(), fmt(a.get_actor_location()),
        a.get_actor_rotation(), fmt(o), fmt(e), extra))
p = unreal.Paths.project_saved_dir() + "NV_probe_m00gc.txt"
open(p, "w", encoding="utf-8").write("\n".join(sorted(OUT)))
unreal.log("NV_PROBE done %d" % len(OUT))
