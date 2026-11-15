"""Lobby ceiling: the kit ceiling tiles (rolled 180) hang 78 cm below the ceiling line with the ceiling lights
buried inside them, so the ceiling rendered black. Hides them (and the buried light-bar meshes). Adds a solid light-grey ceiling slab just under the tiles
and a grid of glowing white light panels where the ceiling lights are (public-building fluorescent look).
Idempotent; saves. Report: Saved/NV_lobby_ceiling.txt"""
import unreal
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
EAL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary
AT = unreal.AssetToolsHelpers.get_asset_tools()
LES = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
V = unreal.Vector
LES.load_level("/Game/NeonVeil/Maps/M00/L_M00_Prologue")
ZS = -12000.0
X0, X1, Y0, Y1 = 5846, 8246, -4924, -6524
D = "/Game/NeonVeil/Materials/Prologue"
OUT = []
def mi(name, parent, vec, scal):
    path = f"{D}/{name}"
    m = unreal.load_asset(path) if EAL.does_asset_exist(path) else AT.create_asset(name, D, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    MEL.set_material_instance_parent(m, unreal.load_asset(parent))
    for k, v in vec.items():
        MEL.set_material_instance_vector_parameter_value(m, k, unreal.LinearColor(*v, 1))
    for k, v in scal.items():
        MEL.set_material_instance_scalar_parameter_value(m, k, v)
    EAL.save_loaded_asset(m)
    return m
CEIL = mi("MI_NV_LobbyCeiling", "/Game/NeonVeil/Vehicles/M_NV_CarPaint", {"Paint": (0.55, 0.57, 0.6)}, {"Metallic": 0.0, "Roughness": 0.7})
PANEL = mi("MI_NV_Glow_PanelWhite", f"{D}/M_NV_Glow", {"Color": (0.9, 0.95, 1.0)}, {"Glow": 9.0})
CUBE = unreal.load_asset("/Engine/BasicShapes/Cube")
by = {a.get_actor_label(): a for a in EAS.get_all_level_actors()}
def slab(label, c, size, mat):
    a = by.get(label) or EAS.spawn_actor_from_class(unreal.StaticMeshActor, V(*c), unreal.Rotator())
    a.set_actor_label(label); a.set_folder_path("P_Lobby")
    a.set_actor_location(V(*c), False, False)
    a.set_actor_scale3d(V(size[0] / 100.0, size[1] / 100.0, size[2] / 100.0))
    smc = a.static_mesh_component
    smc.set_static_mesh(CUBE)
    smc.set_material(0, mat)
    smc.set_editor_property("cast_shadow", False)
    smc.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    return a
slab("Lobby_CeilingSlab", ((X0 + X1) / 2, (Y0 + Y1) / 2, ZS + 396), (X1 - X0, abs(Y1 - Y0), 6), CEIL)
n = 0
for lab, a in list(by.items()):
    if lab.startswith("Lobby_PL_"):
        l = a.get_actor_location()
        slab(lab.replace("Lobby_PL_", "Lobby_Panel_"), (l.x, l.y, ZS + 391), (320, 70, 3), PANEL); n += 1
    if lab.startswith("Lobby_Fill_"):
        l = a.get_actor_location()
        slab(lab.replace("Lobby_Fill_", "Lobby_PanelF_"), (l.x, l.y, ZS + 391), (60, 260, 3), PANEL); n += 1
    if lab.startswith("Lobby_Ceil_"):
        # kit tiles hang 78 cm below their pivot and swallow the ceiling lights: the slab replaces them
        a.static_mesh_component.set_visibility(False)
        a.set_actor_hidden_in_game(True)
        a.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    if lab.startswith("Lobby_LightBar_"):
        a.set_is_temporarily_hidden_in_editor(False)
        a.static_mesh_component.set_visibility(False)
OUT.append(f"slab + {n} light panels")
LES.save_current_level()
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
open(unreal.Paths.project_saved_dir() + "NV_lobby_ceiling.txt", "w").write("\n".join(OUT))
