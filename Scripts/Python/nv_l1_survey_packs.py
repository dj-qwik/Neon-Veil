"""Survey for the dressing / Etherion / armor / FPS / X-ray passes. Report: Saved/NV_l1_survey_packs.txt"""
import unreal
EAL = unreal.EditorAssetLibrary
AR = unreal.AssetRegistryHelpers.get_asset_registry()
OUT = []
def log(*a):
    OUT.append(" ".join(str(x) for x in a))

def assets(path, cls=None):
    f = unreal.ARFilter(package_paths=[path], recursive_paths=True)
    if cls:
        f = unreal.ARFilter(package_paths=[path], recursive_paths=True, class_paths=[unreal.TopLevelAssetPath(*cls)])
    return AR.get_assets(f)

# --- Etherion ModularScifiInterior: static meshes with sizes, materials, BPs, maps
log("==== ETHERION")
for a in assets("/Game/ModularScifiInterior", ("/Script/Engine", "StaticMesh")):
    # registry tags only: loading every mesh crashed the GPU (VRAM)
    log("SM %s | size %s | tris %s" % (a.package_name, a.get_tag_value("ApproxSize"), a.get_tag_value("Triangles")))
for cls in (("/Script/Engine", "Blueprint"), ("/Script/Engine", "World"), ("/Script/Engine", "MaterialInstanceConstant")):
    for a in assets("/Game/ModularScifiInterior", cls):
        log(cls[1], a.package_name)

# --- KINEMATION + armor
for root in ("/Game/KINEMATION", "/Game/SciFi_Armor_Pack_05"):
    log("====", root)
    for cls in (("/Script/Engine", "SkeletalMesh"), ("/Script/Engine", "AnimBlueprint"), ("/Script/Engine", "Blueprint"),
                ("/Script/Engine", "Skeleton"), ("/Script/Engine", "World")):
        for a in assets(root, cls):
            extra = ""
            if cls[1] == "SkeletalMesh":
                extra = "skeleton=%s" % a.get_tag_value("Skeleton")
            log(cls[1], a.package_name, extra)
    seqs = assets(root, ("/Script/Engine", "AnimSequence"))
    log("anim sequences:", len(seqs))
    for a in seqs[:120]:
        log("  SEQ", a.package_name)

# --- X-ray materials + textures
log("==== XRAY")
for a in assets("/Game/NeonVeil/Art/XRay"):
    log(a.asset_class_path.asset_name, a.package_name)
m = unreal.load_asset("/Game/NeonVeil/Art/XRay/Security_Checkpoint")
if m:
    for i, s in enumerate(m.static_materials):
        log("slot", i, s.material_slot_name, s.material_interface.get_path_name() if s.material_interface else None)
    b = m.get_bounding_box(); log("xray bounds", b.min, b.max)
for p in ("/Game/NeonVeil/Art/XRay/Security_X-Ray", "/Game/NeonVeil/Art/XRay/Property_Scanner_001"):
    mat = unreal.load_asset(p)
    if mat:
        try:
            if isinstance(mat, unreal.MaterialInstance):
                tv = [(str(v.parameter_info.name), v.parameter_value.get_path_name() if v.parameter_value else None) for v in mat.get_editor_property("texture_parameter_values")]
                sv = [(str(v.parameter_info.name), v.parameter_value) for v in mat.get_editor_property("scalar_parameter_values")]
                vv = [(str(v.parameter_info.name), str(v.parameter_value)) for v in mat.get_editor_property("vector_parameter_values")]
                log("MI", p, "parent", mat.get_editor_property("parent").get_path_name(), "tex", tv, "scal", sv, "vec", vv)
            else:
                log("mat", p, [t.get_name() for t in unreal.MaterialEditingLibrary.get_used_textures(mat)])
        except Exception as e:
            log("mat err", p, e)

# --- characters
log("==== CHARACTERS")
for p in ("/Game/NeonVeil/Core/BP_NVPlayerCharacter", "/Game/NeonVeil/AI/BP_NVGuard", "/Game/NeonVeil/Characters/BP_NVGuard"):
    if EAL.does_asset_exist(p):
        cls = EAL.load_blueprint_class(p)
        cdo = unreal.get_default_object(cls)
        log("BP", p, cls.get_name())
        for c in cdo.get_components_by_class(unreal.ActorComponent):
            extra = ""
            if isinstance(c, unreal.SkeletalMeshComponent):
                sm = c.get_skeletal_mesh_asset()
                extra = "mesh=%s anim=%s" % (sm.get_path_name() if sm else None, c.get_editor_property("anim_class"))
            if isinstance(c, unreal.StaticMeshComponent):
                extra = "mesh=%s" % (c.static_mesh.get_path_name() if c.static_mesh else None)
            log("   comp", c.get_name(), c.get_class().get_name(), extra)
for a in assets("/Game/NeonVeil", ("/Script/Engine", "Blueprint")):
    n = str(a.asset_name)
    if "Guard" in n or "Enemy" in n or "Player" in n or "Weapon" in n:
        log("BPLIST", a.package_name)

# --- traffic stream class props
log("==== TRAFFIC")
try:
    t = unreal.get_default_object(unreal.NVTrafficStream)
    for n in ("lane_length", "speed", "count", "car_mesh", "spacing", "lanes", "car_material"):
        try:
            log(n, t.get_editor_property(n))
        except Exception as e:
            pass
except Exception as e:
    log("traffic err", e)
open(unreal.Paths.project_saved_dir() + "NV_l1_survey_packs.txt", "w").write("\n".join(OUT))
