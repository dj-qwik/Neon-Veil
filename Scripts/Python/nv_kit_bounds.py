"""Exact local bounds (min/max) and material slots for the meshes the M01 art pass uses. Report: Saved/NV_kit_bounds.txt"""
import unreal
MESHES = """
/Game/ModularScifiInterior/Meshes/SM_Wall_D_A /Game/ModularScifiInterior/Meshes/SM_Wall_D_B /Game/ModularScifiInterior/Meshes/SM_Floor_A
/Game/ModularScifiInterior/Meshes/SM_Floor_B /Game/ModularScifiInterior/Meshes/SM_Ceiling_A /Game/ModularScifiInterior/Meshes/SM_Ceiling_B
/Game/ModularScifiInterior/Meshes/SM_DoorFrame_A /Game/ModularScifiInterior/Meshes/SM_Console /Game/ModularScifiInterior/Meshes/SM_Crate_A
/Game/ModularScifiInterior/Meshes/SM_Crate_B /Game/ModularScifiInterior/Meshes/SM_Pipes_A /Game/ModularScifiInterior/Meshes/SM_Wall_Flat_A
/Game/ModularScifiInterior/Meshes/SM_Light_A /Game/ModularScifiInterior/Meshes/SM_Monitor_Wide
/Game/Clinic/Meshes/SM_Stacks /Game/Clinic/Meshes/SM_Room_TileGround /Game/Clinic/Meshes/SM_Room_SteelWall01 /Game/Clinic/Meshes/SM_Room_SteelWall02
/Game/Clinic/Meshes/SM_RoomMedicalMachine_Machine /Game/Clinic/Meshes/SM_RoomMedicalMachine_Control /Game/Clinic/Meshes/SM_Room_CelingLight01
/Game/Clinic/Meshes/SM_Room_Ceiling /Game/Clinic/Meshes/SM_RoomWall_Decor_5 /Game/Clinic/Meshes/SM_RoomWorkTable_Table
/Game/SciFI_Lite_Assets/Meshes/SM_Wall_Straight_01 /Game/SciFI_Lite_Assets/Meshes/SM_Pipe_Straight_3m_01 /Game/SciFI_Lite_Assets/Meshes/SM_Pipe_Straight_3m_02
/Game/SciFI_Lite_Assets/Meshes/SM_Containers_01 /Game/SciFI_Lite_Assets/Meshes/SM_Fence_01 /Game/SciFI_Lite_Assets/Meshes/SM_GasTankHolder_01
/Game/SciFI_Lite_Assets/Meshes/SM_Door_Frame_01 /Game/SciFI_Lite_Assets/Meshes/SM_Column_Single_01
/Game/Sci_Fi_Light/Meshes/SM_Sci_Fi_Heavy_Duty_Linear_Beacon /Game/Sci_Fi_Light/Meshes/SM_Sci_Fi_Corridor_Ceiling_Strip /Game/Sci_Fi_Light/Meshes/SM_Sci_Fi_Chevron_Luminaire
""".split()
AR = unreal.AssetRegistryHelpers.get_asset_registry()
OUT = []
def find(path):
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        return path
    name = path.rsplit("/", 1)[1]
    root = "/" + "/".join(path.split("/")[1:3])
    for a in AR.get_assets_by_path(root, recursive=True):
        if str(a.asset_name) == name and str(a.asset_class_path.asset_name) == "StaticMesh":
            return str(a.package_name)
    return None
for p in MESHES:
    q = find(p)
    if not q:
        OUT.append("MISSING " + p); continue
    m = unreal.load_asset(q)
    b = m.get_bounding_box()
    mats = [str(s.material_interface.get_path_name()) if s.material_interface else "-" for s in m.static_materials]
    OUT.append("%s\tmin(%d,%d,%d) max(%d,%d,%d)\tnanite=%s\t%s" % (q, b.min.x, b.min.y, b.min.z, b.max.x, b.max.y, b.max.z,
               m.get_editor_property("nanite_settings").get_editor_property("enabled"), " | ".join(mats)))
open(unreal.Paths.project_saved_dir() + "NV_kit_bounds.txt", "w", encoding="utf-8").write("\n".join(OUT))
