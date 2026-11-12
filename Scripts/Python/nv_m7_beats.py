"""NEON VEIL - M7 authored beats for M00 (Bible §4).

 - C00 arrival: ANVTramArrival glides the tram (and the player inside it) 60 m along a new rail into
   the skybridge dock over 14 s; camera stays player-driven; a barrier holds the open front until
   docking; ride loop + dock sound (original, RawAssets/Audio).
 - Operations gallery: ANVScreenGlitch drops the data-wall feed for 180 ms (two pulses) when the
   player first walks in, then AION denies the anomaly.
Re-runnable (folder Beats cleared first). Report: Saved/NV_m7_beats.txt
"""
import os
import unreal

REPORT = []
def log(*a):
    msg = " ".join(str(x) for x in a)
    REPORT.append(msg)
    unreal.log("[NV M7 beats] " + msg)

AT = unreal.AssetToolsHelpers.get_asset_tools()
EAL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
LES = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
V = unreal.Vector
FOLDER = "Beats"
ART = "/Game/NeonVeil/Materials/Art"
AUD = "/Game/NeonVeil/Audio/SFX"

def T(s):
    return unreal.Text(s)

def line(speaker, text, dur=3.8):
    l = unreal.NVSubtitleLine()
    l.set_editor_property("speaker", T(speaker))
    l.set_editor_property("text", T(text))
    l.set_editor_property("duration", dur)
    return l

def find(label):
    for a in EAS.get_all_level_actors():
        if a.get_actor_label() == label:
            return a
    return None

def import_wav(fname, loop):
    name = os.path.splitext(fname)[0]
    path = f"{AUD}/{name}"
    if not EAL.does_asset_exist(path):
        if not EAL.does_directory_exist(AUD):
            EAL.make_directory(AUD)
        t = unreal.AssetImportTask()
        t.set_editor_property("filename", os.path.abspath(os.path.join(unreal.Paths.project_dir(), "RawAssets", "Audio", fname)))
        t.set_editor_property("destination_path", AUD)
        t.set_editor_property("replace_existing", True)
        t.set_editor_property("automated", True)
        t.set_editor_property("save", True)
        AT.import_asset_tasks([t])
    w = unreal.load_asset(path)
    w.set_editor_property("looping", loop)
    EAL.save_loaded_asset(w, only_if_is_dirty=False)
    return w

def glitch_material():
    path = f"{ART}/M_NV_ScreenGlitch"
    if EAL.does_asset_exist(path):
        return unreal.load_asset(path)
    m = AT.create_asset("M_NV_ScreenGlitch", ART, unreal.Material, unreal.MaterialFactoryNew())
    m.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    def x(cls, px, py, **p):
        e = MEL.create_material_expression(m, cls, px, py)
        for k, v in p.items():
            e.set_editor_property(k, v)
        return e
    wp = x(unreal.MaterialExpressionWorldPosition, -900, 0)
    time = x(unreal.MaterialExpressionTime, -900, 150)
    speed = x(unreal.MaterialExpressionConstant3Vector, -900, 250, constant=unreal.LinearColor(0, 0, 4000, 1))
    tv = x(unreal.MaterialExpressionMultiply, -700, 200)
    MEL.connect_material_expressions(time, "", tv, "A"); MEL.connect_material_expressions(speed, "", tv, "B")
    pos = x(unreal.MaterialExpressionAdd, -550, 50)
    MEL.connect_material_expressions(wp, "", pos, "A"); MEL.connect_material_expressions(tv, "", pos, "B")
    noise = x(unreal.MaterialExpressionNoise, -400, 50, scale=0.35, levels=2)
    MEL.connect_material_expressions(pos, "", noise, "Position")
    col = x(unreal.MaterialExpressionConstant3Vector, -400, 250, constant=unreal.LinearColor(0.6, 0.9, 1.0, 1))
    k = x(unreal.MaterialExpressionMultiply, -200, 100)
    MEL.connect_material_expressions(noise, "", k, "A"); MEL.connect_material_expressions(col, "", k, "B")
    g = x(unreal.MaterialExpressionConstant, -200, 250, r=5.0)
    e = x(unreal.MaterialExpressionMultiply, -50, 150)
    MEL.connect_material_expressions(k, "", e, "A"); MEL.connect_material_expressions(g, "", e, "B")
    MEL.connect_material_property(e, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    MEL.recompile_material(m)
    EAL.save_loaded_asset(m, only_if_is_dirty=False)
    log("built", path)
    return m

def box(label, center, size, mat):
    a = EAS.spawn_actor_from_class(unreal.StaticMeshActor, V(*center), unreal.Rotator())
    a.static_mesh_component.set_static_mesh(unreal.load_asset("/Engine/BasicShapes/Cube"))
    a.set_actor_scale3d(V(size[0] / 100.0, size[1] / 100.0, size[2] / 100.0))
    a.static_mesh_component.set_material(0, mat)
    a.set_actor_label(label)
    a.set_folder_path(FOLDER)
    return a

def main():
    for a in EAS.get_all_level_actors():
        if str(a.get_folder_path()) == FOLDER:
            EAS.destroy_actor(a)

    # ---------------- C00 tram arrival
    titan = unreal.load_asset(f"{ART}/MI_DIR_Titanium")
    cyan = unreal.load_asset(f"{ART}/MI_DIR_CyanLight")
    for side in (-1, 1):
        box(f"C00_Rail_{'L' if side < 0 else 'R'}", (-7100, side * 230, -75), (14000, 40, 50), titan)
        box(f"C00_RailGlow_{'L' if side < 0 else 'R'}", (-7100, side * 230, -48), (14000, 6, 4), cyan)
    for i in range(7):
        box(f"C00_Pylon{i}", (-1600 - i * 2000, 0, -2600), (160, 520, 5000), titan)
    parts = []
    for a in EAS.get_all_level_actors():
        lab = a.get_actor_label()
        if lab.startswith(("A_Tram",)):
            root = a.get_editor_property("root_component")
            if root:
                root.set_mobility(unreal.ComponentMobility.MOVABLE)
            parts.append(a)
    tram = EAS.spawn_actor_from_class(unreal.NVTramArrival, V(-700, 0, 100), unreal.Rotator())
    tram.set_editor_property("parts", parts)
    tram.set_editor_property("distance", 6000.0)
    tram.set_editor_property("duration", 14.0)
    tram.set_editor_property("cabin_extent", V(650, 260, 300))
    tram.set_editor_property("ride_sound", import_wav("SFX_Tram_RideLoop.wav", True))
    tram.set_editor_property("dock_sound", import_wav("SFX_Tram_Dock.wav", False))
    fb = tram.get_editor_property("front_barrier")
    fb.set_relative_location(V(620, 0, 150), False, False)
    tram.set_actor_label("C00_TramArrival")
    tram.set_folder_path(FOLDER)
    log("tram arrival: parts", [p.get_actor_label() for p in parts])

    # ---------------- 180 ms surveillance discontinuity in the operations gallery
    screens = [a for a in EAS.get_all_level_actors() if a.get_actor_label().startswith("D_DataScreen")]
    g = EAS.spawn_actor_from_class(unreal.NVScreenGlitch, V(11900, 0, 200), unreal.Rotator())
    g.get_editor_property("volume").set_box_extent(V(150, 380, 220))
    g.set_editor_property("targets", screens)
    g.set_editor_property("glitch_material", glitch_material())
    g.set_editor_property("glitch_duration", 0.18)
    g.set_editor_property("start_delay", 1.4)
    g.set_editor_property("lines_delay", 1.1)
    g.set_editor_property("glitch_sound", unreal.load_asset("/Game/SciFiUISFX/Cues/Glitches/Glitch_13_Cue"))
    g.set_editor_property("lines", [
        line("Ops Monitor", "Gallery feed just dropped. One-eight-zero milliseconds, all cameras.", 3.6),
        line("AION", "Correction. Feed continuity is nominal. No anomaly is recorded.", 3.8),
    ])
    g.set_actor_label("D_SurveillanceDiscontinuity")
    g.set_folder_path(FOLDER)
    log("glitch beat: screens", len(screens))
    LES.save_current_level()

try:
    main()
finally:
    with open(unreal.Paths.project_saved_dir() + "NV_m7_beats.txt", "w", encoding="utf-8") as fh:
        fh.write("\n".join(REPORT))
