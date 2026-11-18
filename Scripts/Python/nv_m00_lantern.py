"""M00 Glass Crown: Operation LANTERN, the op Ghost-7 closed just before the game (Docs/Bible/Continuity.md).
- After-action briefing on the operations gallery data wall (above the D_DataScreen row, opposite the holo-table).
- The sealed research core on a plinth in the antechamber, between the south pillars, with a label and a cyan glow.
- Three lines added to D_HoloTable 'Review assignment' (LAN set), between the assignment and 'Proceed to the antechamber'.
Re-runnable: removes its own actors (folder G_Lantern); keeps its holo-table lines (and their voices) if present. Saves the level.
Run in the full-uproject session only (see Scripts/BUILD_NOTES.md). Report: Saved/NV_m00_lantern.txt"""
import unreal, os, json, math
OUT = []
def log(*a): OUT.append(" ".join(str(x) for x in a))
EAL = unreal.EditorAssetLibrary
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
LES = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
UES = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
AT = unreal.AssetToolsHelpers.get_asset_tools()
MEL = unreal.MaterialEditingLibrary
V = lambda x, y, z: unreal.Vector(x, y, z)
def R(p=0.0, y=0.0, r=0.0): return unreal.Rotator(roll=r, pitch=p, yaw=y)
MAP = "/Game/NeonVeil/Maps/M00/L_M00_GlassCrown"
if not UES.get_editor_world().get_path_name().startswith(MAP):
    LES.load_level(MAP)
PROJ = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
TEX_DIR, MAT_DIR = "/Game/NeonVeil/Textures/Signage", "/Game/NeonVeil/Materials/Signage"
FOLDER, TAG = "G_Lantern", "NVLANTERN"
for a in list(EAS.get_all_level_actors()):
    if str(a.get_folder_path()) == FOLDER or TAG in [str(t) for t in a.tags]:
        EAS.destroy_actor(a)
ACTORS = list(EAS.get_all_level_actors())
def find(label):
    for a in ACTORS:
        if a.get_actor_label() == label: return a
    log("not found:", label)
def tagit(a, label):
    a.set_actor_label(label); a.set_folder_path(FOLDER); a.tags = [unreal.Name(TAG)]; return a

def imp_tex(name):
    t = unreal.AssetImportTask()
    t.filename = os.path.join(PROJ, "Art", "Signage", name + ".png")
    t.destination_path = TEX_DIR; t.destination_name = name
    t.replace_existing = True; t.automated = True; t.save = True
    AT.import_asset_tasks([t])
    tex = unreal.load_asset(f"{TEX_DIR}/{name}")
    tex.set_editor_property("lod_group", unreal.TextureGroup.TEXTUREGROUP_WORLD)
    EAL.save_loaded_asset(tex)
    return tex
def mi(name, tex, scalars):
    path = f"{MAT_DIR}/{name}"
    x = unreal.load_asset(path) if EAL.does_asset_exist(path) else AT.create_asset(name, MAT_DIR, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    MEL.set_material_instance_parent(x, unreal.load_asset(f"{MAT_DIR}/M_NV_SignScreen"))
    MEL.set_material_instance_texture_parameter_value(x, "Tex", tex)
    for k, v in scalars.items(): MEL.set_material_instance_scalar_parameter_value(x, k, v)
    MEL.update_material_instance(x); EAL.save_loaded_asset(x)
    return x
MI_BRIEF = mi("MI_NV_Sign_LanternBrief", imp_tex("T_NV_LanternBrief"), {"Glow": 1.4, "FlickerAmt": 0.03})
MI_LABEL = mi("MI_NV_Sign_LanternLabel", imp_tex("T_NV_LanternLabel"), {"Glow": 1.3, "FlickerAmt": 0.02})
MI_CORE = mi("MI_NV_LanternCore", imp_tex("T_NV_LanternCore"), {"Glow": 6.0, "FlickerAmt": 0.15, "FlickerSpeed": 3.0})

PLANE = unreal.load_asset("/Engine/BasicShapes/Plane")
CUBE = unreal.load_asset("/Engine/BasicShapes/Cube")
SPHERE = unreal.load_asset("/Engine/BasicShapes/Sphere")
CYL = unreal.load_asset("/Engine/BasicShapes/Cylinder")
pl = find("E_Panel_Plinth")
DARK = pl.static_mesh_component.get_material(0) if pl else None

def screen(label, mat, center, normal, w, h, off=3.0):
    n = unreal.Vector(normal.x, normal.y, 0.0).normal()
    a = EAS.spawn_actor_from_object(PLANE, center + n * off, R())
    best = None
    for p in (0.0, 90.0, 180.0, 270.0):
        for yw in range(0, 360, 90):
            for r in (0.0, 90.0, 180.0, 270.0):
                rot = R(p=p, y=yw + math.degrees(math.atan2(n.y, n.x)), r=r)
                a.set_actor_rotation(rot, False)
                if a.get_actor_up_vector().dot(n) > 0.99 and a.get_actor_right_vector().dot(V(0, 0, -1)) > 0.99:
                    best = rot; break
            if best: break
        if best: break
    a.set_actor_rotation(best, False)
    a.set_actor_scale3d(V(w / 100.0, h / 100.0, 1.0))
    c = a.static_mesh_component
    c.set_material(0, mat); c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION); c.set_editor_property("cast_shadow", False)
    log("screen", label, center, best)
    return tagit(a, label)
def shape(label, mesh, center, size, mat, coll=False, rot=None):
    a = EAS.spawn_actor_from_object(mesh, V(*center), rot or R())
    a.set_actor_scale3d(V(size[0] / 100.0, size[1] / 100.0, size[2] / 100.0))
    c = a.static_mesh_component
    if mat: c.set_material(0, mat)
    if not coll: c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    return tagit(a, label)

# --- gallery: after-action briefing above the data screens, facing the holo-table (+Y)
dw = find("D_DataWall")
o, e = dw.get_actor_bounds(False)
face_y = o.y + e.y
screen("L_LanternBrief", MI_BRIEF, V(12550, face_y, 300), V(0, 1, 0), 480, 240)
shape("L_LanternBrief_Frame", CUBE, (12550, face_y + 1, 300), (496, 2, 256), DARK)
lt = EAS.spawn_actor_from_class(unreal.RectLight, V(12550, face_y + 60, 300), R(y=-90))
lt.light_component.set_editor_property("intensity", 6.0); lt.light_component.set_light_color(unreal.LinearColor(0.3, 0.8, 1.0, 1))
lt.light_component.set_editor_property("source_width", 400); lt.light_component.set_editor_property("source_height", 200)
lt.light_component.set_editor_property("attenuation_radius", 500); lt.light_component.set_editor_property("cast_shadows", False)
tagit(lt, "L_LanternBrief_Spill")

# --- antechamber: sealed core case between the south pillars, label facing the walkway (+Y)
CX, CY = 15550.0, -450.0
shape("L_Core_Plinth", CUBE, (CX, CY, 50), (70, 70, 100), DARK, coll=True)
shape("L_Core_Base", CUBE, (CX, CY, 104), (60, 60, 8), DARK)
shape("L_Core_Cap", CUBE, (CX, CY, 166), (60, 60, 8), DARK)
for i, (dx, dy) in enumerate(((-27, -27), (27, -27), (-27, 27), (27, 27))):
    shape("L_Core_Post%d" % i, CUBE, (CX + dx, CY + dy, 135), (5, 5, 56), DARK)
shape("L_Core_Ring", CYL, (CX, CY, 109), (40, 40, 3), MI_CORE)
shape("L_Core_Sphere", SPHERE, (CX, CY, 135), (26, 26, 26), MI_CORE)
screen("L_Core_Label", MI_LABEL, V(CX, CY + 35, 60), V(0, 1, 0), 60, 20, off=1.5)
pt = EAS.spawn_actor_from_class(unreal.PointLight, V(CX, CY + 10, 140), R())
pt.light_component.set_editor_property("intensity", 900.0); pt.light_component.set_light_color(unreal.LinearColor(0.25, 0.85, 1.0, 1))
pt.light_component.set_editor_property("attenuation_radius", 320); pt.light_component.set_editor_property("cast_shadows", False)
tagit(pt, "L_Core_Glow")

# --- holo-table lines
lines = json.load(open(os.path.join(PROJ, "Scripts", "VO", "LAN_lines.json")))
mine = {l["text"] for l in lines}
ht = find("D_HoloTable")
allv = list(ht.get_editor_property("lines_on_use"))
have = {str(l.get_editor_property("text")) for l in allv}
cur = allv
new = []
for l in lines:
    if l["text"] in have:   # already placed (and voiced by nv_vo_hook): keep it as is
        continue
    s = unreal.NVSubtitleLine()
    s.set_editor_property("speaker", unreal.Text(l["speaker"])); s.set_editor_property("text", unreal.Text(l["text"]))
    s.set_editor_property("duration", 5.0)
    new.append(s)
idx = next((i for i, l in enumerate(cur) if str(l.get_editor_property("text")).startswith("Proceed to the antechamber")), len(cur))
if new:
    ht.set_editor_property("lines_on_use", cur[:idx] + new + cur[idx:])
log("holo lines:", [str(l.get_editor_property("text"))[:40] for l in ht.get_editor_property("lines_on_use")])

LES.save_current_level()
open(unreal.Paths.project_saved_dir() + "NV_m00_lantern.txt", "w", encoding="utf-8").write("\n".join(OUT))
unreal.log("NV_LANTERN done")
