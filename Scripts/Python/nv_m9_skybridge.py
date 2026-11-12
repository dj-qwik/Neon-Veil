"""NEON VEIL - skybridge (space A) lighting pass. Bible §14 Crown: high-key interior pools against dark windows,
cool rim light, restrained signage; palette: sterile pale white, dark smoked glass, controlled cyan.
 - Roof underside: pale ceramic (was dark titanium) so the ceiling reads high-key; tram roof the same.
 - Seven soft rect-light panels under the seven ceiling strips replace the four point lights (unshadowed: Lumen
   handles occlusion; keeps the heaviest room's GPU cost flat).
 - Thin cyan floor-edge accent lines along both glazing lines (controlled cyan, guides the eye to the atrium).
Re-runnable: removes its own actors (label prefix A_Rect / A_EdgeGlow) first. Report: Saved/NV_m9_skybridge.txt
Tunables via env-free constants below."""
import unreal

RECT_CD = 900.0          # candelas per panel
RECT_TEMP = 6200.0       # K, slightly cool white
EDGE = True

REPORT = []
def log(*a):
    msg = " ".join(str(x) for x in a)
    REPORT.append(msg)
    unreal.log("[NV skybridge] " + msg)

EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
LES = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ART = "/Game/NeonVeil/Materials/Art"
V = unreal.Vector

def find(label):
    for a in EAS.get_all_level_actors():
        if a.get_actor_label() == label:
            return a
    return None

def main():
    for a in EAS.get_all_level_actors():
        if a.get_actor_label().startswith(("A_Rect", "A_EdgeGlow")):
            EAS.destroy_actor(a)

    ceramic = unreal.load_asset(f"{ART}/MI_DIR_CeramicPanel")
    cyan = unreal.load_asset(f"{ART}/MI_DIR_CyanLight")
    for lab in ("A_Roof", "A_TramRoof"):
        a = find(lab)
        if a:
            a.static_mesh_component.set_material(0, ceramic)
            log(lab, "-> ceramic")

    # Old point lights off (kept in the level, hidden, so the change is easy to compare/revert)
    for i in range(4):
        a = find(f"A_Light{i}")
        if a:
            a.light_component.set_visibility(False)
            a.set_actor_hidden_in_game(True)
            a.light_component.set_editor_property("intensity", 0.0)
    log("A_Light0-3 disabled")

    for i in range(7):
        x = 475 + 450 * i
        r = EAS.spawn_actor_from_class(unreal.RectLight, V(x, -25, 418), unreal.Rotator(0, -90, 0))
        lc = r.rect_light_component
        lc.set_editor_property("intensity_units", unreal.LightUnits.CANDELAS)
        lc.set_editor_property("intensity", RECT_CD)
        lc.set_editor_property("use_temperature", True)
        lc.set_editor_property("temperature", RECT_TEMP)
        lc.set_editor_property("source_width", 360.0)
        lc.set_editor_property("source_height", 60.0)
        lc.set_editor_property("barn_door_angle", 70.0)
        lc.set_editor_property("barn_door_length", 20.0)
        lc.set_editor_property("attenuation_radius", 900.0)
        lc.set_editor_property("cast_shadows", False)
        r.set_actor_label(f"A_Rect{i}")
        r.set_folder_path("Lighting")
    log("rect panels 7 x", RECT_CD, "cd")

    if EDGE:
        cube = unreal.load_asset("/Engine/BasicShapes/Cube")
        for side in (-1, 1):
            a = EAS.spawn_actor_from_class(unreal.StaticMeshActor, V(1750, side * 288, 1.2), unreal.Rotator())
            a.static_mesh_component.set_static_mesh(cube)
            a.set_actor_scale3d(V(34.0, 0.04, 0.02))
            a.static_mesh_component.set_material(0, cyan)
            a.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
            a.static_mesh_component.set_editor_property("cast_shadow", False)
            a.set_actor_label(f"A_EdgeGlow_{'L' if side < 0 else 'R'}")
            a.set_folder_path("A_Skybridge")
        log("edge glow lines 2")
    LES.save_current_level()

try:
    main()
finally:
    with open(unreal.Paths.project_saved_dir() + "NV_m9_skybridge.txt", "w", encoding="utf-8") as fh:
        fh.write("\n".join(REPORT))
