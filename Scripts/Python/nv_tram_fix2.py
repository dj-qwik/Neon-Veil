"""Tram polish: drop the safety chains across the front (exit) end door, Nanite on opaque kit meshes (VSM cost),
cap kit textures at 1024 (VRAM). Report: Saved/NV_tram_fix2.txt"""
import unreal
EAL = unreal.EditorAssetLibrary
out = []
for a in unreal.EditorLevelLibrary.get_all_level_actors():
    if a.get_actor_label() == "T_EndExtFront":
        for c in a.get_components_by_class(unreal.StaticMeshComponent):
            m = c.get_editor_property("static_mesh")
            if m and m.get_name() == "SM_ext_doorchains_01":
                c.set_visibility(False)
                c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
                out.append("front chains hidden")
nan = 0
for p in EAL.list_assets("/Game/SubwayTrain/Meshes", recursive=True):
    m = unreal.load_asset(p.split(".")[0])
    if not isinstance(m, unreal.StaticMesh):
        continue
    mats = [s.material_interface for s in m.static_materials]
    def translucent(mi):
        if not mi:
            return False
        base = mi.get_base_material()
        return base.get_editor_property("blend_mode") not in (unreal.BlendMode.BLEND_OPAQUE, unreal.BlendMode.BLEND_MASKED)
    if any(translucent(x) for x in mats) or "Fog" in m.get_name() or "polyplane" in m.get_name():
        continue
    ns = m.get_editor_property("nanite_settings")
    if not ns.enabled:
        ns.enabled = True
        m.set_editor_property("nanite_settings", ns)
        EAL.save_loaded_asset(m)
        nan += 1
out.append("nanite enabled on %d meshes" % nan)
cap = 0
for p in EAL.list_assets("/Game/SubwayTrain", recursive=True):
    t = unreal.load_asset(p.split(".")[0])
    if isinstance(t, unreal.Texture2D) and t.get_editor_property("max_texture_size") != 1024:
        t.set_editor_property("max_texture_size", 1024)
        EAL.save_loaded_asset(t)
        cap += 1
out.append("textures capped %d" % cap)
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
open(unreal.Paths.project_saved_dir() + "NV_tram_fix2.txt", "w").write("\n".join(out))
