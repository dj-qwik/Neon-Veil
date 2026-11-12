"""NEON VEIL - M5 art pass: set dressing and hero props for M00 (Bible §13 props, §4 spaces A-E).

Uses the free Fab packs added in M4/M5:
  Clinic (Medical Clinic and Laboratory Futuristic Sci-Fi), SciFI_Lite_Assets (Sci-Fi Lite Sample
  Pack), Sci_Fi_Light (Sci-Fi Light Pack), HologramShader.
Every prop is fitted from its real mesh bounds (no hand-typed scales), sits on its surface, and is
placed in folder Art_Props. Gameplay interactables keep their actors/logic; only their visible
mesh changes. Re-runnable. Report: Saved/NV_m5_props.txt
"""
import unreal

REPORT = []
def log(*a):
    msg = " ".join(str(x) for x in a)
    REPORT.append(msg)
    unreal.log("[NV M5 props] " + msg)

EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
LES = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
EAL = unreal.EditorAssetLibrary
FOLDER = "Art_Props"
V = unreal.Vector

CL = "/Game/Clinic/Meshes"
LT = "/Game/SciFI_Lite_Assets/StaticMeshes"
SL = "/Game/Sci_Fi_Light/Static_Meshes"
def sl(name):
    return f"{SL}/{name}/Mesh/{name}"

_cache = {}
def mesh(path):
    if path not in _cache:
        m = unreal.load_asset(path)
        if m is None:
            log("MISSING", path)
        _cache[path] = m
    return _cache[path]

def dims(sm):
    bb = sm.get_bounding_box()
    return bb.min, bb.max, V(bb.max.x - bb.min.x, bb.max.y - bb.min.y, bb.max.z - bb.min.z)

def fit(sm, height=None, length=None, width=None):
    """Uniform scale so the mesh matches the given height (Z), length (longest horizontal) or
    width (shortest horizontal) in cm."""
    _, _, s = dims(sm)
    if height:
        return height / max(s.z, 0.01)
    if length:
        return length / max(s.x, s.y, 0.01)
    if width:
        return width / max(min(s.x, s.y), 0.01)
    return 1.0

def prop(label, path, x, y, z, yaw=0.0, height=None, length=None, width=None, scale=None,
         anchor="bottom", along=None, mat=None):
    """Spawn a static mesh prop. anchor='bottom' rests it on z; 'top' hangs it from z (ceiling);
    'center' centres it on z. along='x'/'y' rotates the mesh so its long axis runs along that axis."""
    sm = mesh(path)
    if sm is None:
        return None
    s = scale or fit(sm, height, length, width)
    mn, mx, sz = dims(sm)
    if along:
        long_is_x = sz.x >= sz.y
        want_x = along == "x"
        if long_is_x != want_x:
            yaw += 90.0
    a = EAS.spawn_actor_from_class(unreal.StaticMeshActor, V(x, y, z), unreal.Rotator(yaw=yaw))
    c = a.static_mesh_component
    c.set_static_mesh(sm)
    a.set_actor_scale3d(V(s, s, s))
    if anchor == "bottom":
        dz = -mn.z * s
    elif anchor == "top":
        dz = -mx.z * s
    else:
        dz = -(mn.z + mx.z) / 2 * s
    a.set_actor_location(V(x, y, z + dz), False, False)
    if mat:
        c.set_material(0, mat)
    a.set_actor_label(label)
    a.set_folder_path(FOLDER)
    return a

def find(label):
    for a in EAS.get_all_level_actors():
        if a.get_actor_label() == label:
            return a
    return None

def restyle_interactable(label, path, x, y, z, yaw=0.0, height=None, length=None, width=None, mat=None):
    """Swap the visible mesh of an NVInteractableActor (its mesh component is the root)."""
    a = find(label)
    sm = mesh(path)
    if not a or not sm:
        log("skip interactable", label)
        return
    m = a.get_editor_property("mesh")
    m.set_static_mesh(sm)
    s = fit(sm, height, length, width)
    m.set_editor_property("relative_scale3d", V(s, s, s))
    if mat:
        m.set_material(0, mat)
    else:
        for i in range(m.get_num_materials()):
            m.set_material(i, sm.get_material(i))
    mn, _, _ = dims(sm)
    a.set_actor_location(V(x, y, z - mn.z * s), False, False)
    a.set_actor_rotation(unreal.Rotator(yaw=yaw), False)
    log("interactable", label, "->", path.split("/")[-1], f"scale {s:.2f}")

def main():
    removed = 0
    for a in EAS.get_all_level_actors():
        if str(a.get_folder_path()) == FOLDER:
            EAS.destroy_actor(a); removed += 1
    log("cleared", removed)
    n0 = len(EAS.get_all_level_actors())

    # ---------------- A. Skybridge: ceiling light strips between the ribs, baseboard light lines
    for i in range(7):
        x = 475 + i * 450
        prop(f"A_CeilStrip{i}", sl("SM_Sci_Fi_Corridor_Ceiling_Strip"), x, 0, 450, length=380, anchor="top", along="x")
    for i in range(7):
        x = 475 + i * 450
        for side in (-1, 1):
            prop(f"A_Baseboard{i}_{'L' if side < 0 else 'R'}", sl("SM_Sci_Fi_Linear_Baseboard_Light"),
                 x, side * 280, 0, yaw=0 if side > 0 else 180, length=360, along="x")

    # ---------------- B. Atrium
    # colonnade under the mezzanine
    for i in range(6):
        prop(f"B_Column{i}", f"{LT}/SM_Column_Single_01", 3800 + i * 500, -790, 0, height=1200)
    # security arch flanked by monolith lights
    for side in (-1, 1):
        prop(f"B_ArchMonolith_{'L' if side < 0 else 'R'}", sl("SM_Sci_Fi_Monolith_Light"), 6080, side * 360, 0, yaw=180, height=260)
    # visitor lounge west of the guard loop, facing the sculpture
    prop("B_Lounge_Sofa", f"{CL}/Props/SM_Entrance_Sofa01", 3720, 0, 0, yaw=0, length=240)
    prop("B_Lounge_ChairN", f"{CL}/Props/SM_Entrance_ArmChair01", 3900, 330, 0, yaw=-60, length=95)
    prop("B_Lounge_ChairS", f"{CL}/Props/SM_Entrance_ArmChair01", 3900, -330, 0, yaw=60, length=95)
    prop("B_Lounge_Table", f"{CL}/Props/SM_Entrance_MiddleTable", 3930, 0, 0, length=120)
    # info kiosk near the arch queue
    prop("B_InfoKiosk", sl("SM_Sci_Fi_Info_Terminal"), 5600, -420, 0, yaw=180, height=180)
    # ceiling luminaires
    for i, (x, y) in enumerate(((4200, -400), (4200, 400), (5600, -400), (5600, 400))):
        prop(f"B_Luminaire{i}", sl("SM_Sci_Fi_Hub_Luminaire"), x, y, 1200, length=260, anchor="top")
    # news feed screens (optional interactions) become wall monitors
    restyle_interactable("B_Opt_NewsFeed", f"{CL}/Props/SM_Entrance_BigMonitor", 4000, -1060, 140, yaw=90, length=180)
    restyle_interactable("B_Opt_ProtestClip", f"{CL}/Props/SM_Entrance_BigMonitor", 5400, -1060, 140, yaw=90, length=180)

    # ---------------- C. Simulation suite
    for i, x in enumerate((6900, 8300, 9700)):
        prop(f"C_CeilBeam{i}", sl("SM_Segmented_Ceiling_Beam"), x, 0, 900, length=2960, anchor="top", along="y")
    for i, x in enumerate((7000, 8300, 9600)):
        for side in (-1, 1):
            prop(f"C_Beacon{i}_{'S' if side < 0 else 'N'}", sl("SM_Sci_Fi_Heavy_Duty_Linear_Beacon"),
                 x, side * 1470, 700, yaw=0 if side < 0 else 180, length=220, anchor="center", along="x")
    prop("C_ControlDesk", f"{LT}/SM_WorkStation_01", 6650, -1250, 0, yaw=90, length=220)
    restyle_interactable("C_RelayTerminal", sl("SM_Sci_Fi_Info_Terminal"), 9820, 1380, 415, yaw=180, height=170)

    # ---------------- D. Operations gallery
    base = find("D_HoloTable_Base")
    if base:
        EAS.destroy_actor(base)
    prop("D_HoloMachine", f"{CL}/Props/SM_RoomMapMachine_Machine", 12550, 0, 0, length=320)
    holo_mi = unreal.load_asset("/Game/Clinic/Materials/MaterialInstances/MI_Hologram")
    h = find("D_HoloTable")
    if h and holo_mi:
        h.get_editor_property("mesh").set_material(0, holo_mi)
    for i, x in enumerate((11900, 12900, 13900)):
        prop(f"D_WorkTable{i}", f"{CL}/Props/SM_RoomWorkTable_Table", x, 300, 0, yaw=180, length=200)
        prop(f"D_WorkMonitor{i}", f"{CL}/Props/SM_RoomWorkTable_ControlMonitor01", x, 300, 0, yaw=180, length=180)
    for i in range(5):
        prop(f"D_CeilStrip{i}", sl("SM_Sci_Fi_Corridor_Ceiling_Strip"), 10750 + i * 900, 0, 500, length=700, anchor="top", along="x")
    restyle_interactable("D_Opt_TerminalLog", f"{CL}/Props/SM_RoomWorkTable_SmallMonitor", 11200, 330, 90, yaw=180, length=80)

    # ---------------- E. Director antechamber (symmetrical)
    for side in (-1, 1):
        prop(f"E_WallLight_{'S' if side < 0 else 'N'}", sl("SM_Sci_Fi_Patterned_Wall_Light"),
             15600, side * 670, 330, yaw=90 if side < 0 else -90, height=220, anchor="center")
        prop(f"E_Monolith_{'S' if side < 0 else 'N'}", sl("SM_Sci_Fi_Monolith_Light"), 16250, side * 560, 0, yaw=180, height=300)
    restyle_interactable("E_BiometricPanel", f"{CL}/Props/SM_Entrance_FingersScreen", 16250, 0, 120, yaw=180, height=60)

    log("props placed:", len(EAS.get_all_level_actors()) - n0)
    LES.save_current_level()

try:
    main()
finally:
    with open(unreal.Paths.project_saved_dir() + "NV_m5_props.txt", "w", encoding="utf-8") as fh:
        fh.write("\n".join(REPORT))
