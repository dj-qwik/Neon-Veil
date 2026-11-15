"""Ambient Veyra citizens for the prologue (street, lobby, station concourse, platform). v2: dressed.
Each NPC is an ANVGuardCharacter (same patrol/glance AI as the guards, non-hostile, damage-immune) wearing one of the
16 assembled MetaHumans from the MetaHumanCrowdContent plugin as its look (base Manny animates hidden underneath and the
MetaHuman follows via leader pose). A couple wear the P05 helmet as couriers. Nav bounds cover every route.
Idempotent: folder P_NPC / tag NVNPC. Report: Saved/NV_npcs.txt"""
import random
import unreal
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
LES = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
V = unreal.Vector
OUT = []
def log(*a):
    OUT.append(" ".join(str(x) for x in a))
MAP = "/Game/NeonVeil/Maps/M00/L_M00_Prologue"
if not unreal.EditorLevelLibrary.get_editor_world().get_path_name().startswith(MAP):
    LES.load_level(MAP)
FOLDER, TAG = "P_NPC", "NVNPC"
for a in list(EAS.get_all_level_actors()):
    if TAG in a.tags or str(a.get_folder_path()) == FOLDER:
        EAS.destroy_actor(a)

ROOT = "/MetaHumanCrowdContent/Characters/Assembled"
LOOKS = []
# only the body shapes the crowd wardrobe is fitted to (med height): tall/short bodies poke through the garments
for shape in ("AverageFemale", "AverageMale", "HeavysetFemale", "HeavysetMale"):
    for h in ("01", "02"):
        cls = unreal.load_object(None, f"{ROOT}/{shape}_Head{h}/BP_{shape}_Head{h}.BP_{shape}_Head{h}_C")
        if cls:
            LOOKS.append(cls)
        else:
            log("missing look", shape, h)
log("looks:", len(LOOKS))
rng = random.Random(11)
rng.shuffle(LOOKS)
MANNY = unreal.load_asset("/Game/Characters/Mannequins/Meshes/SKM_Manny_Simple")
ABP = unreal.NVBodyAnimInstance.static_class()   # native foot-synced body animation (was ABP_Unarmed)
HELMET = unreal.load_asset("/Game/SciFi_Armor_Pack_05/Mesh/Parts/SKM_SciFi_Helmet_v1_P05")
IMMUNE = unreal.GameplayTagContainer()
IMMUNE.import_text('(GameplayTags=((TagName="NV.Damage.Ballistic"),(TagName="NV.Damage.Training"),(TagName="NV.Damage.Melee")))')
ZS = -12000.0

# label, start (x, y, floor z), route (world xy), waits, speed, courier?
NPCS = [
    # street, west sidewalk (facades at x 5150, bollards at 6180)
    ("NPC_St_W1", (5600, -15200, ZS), [(5600, -15200), (5650, -7600)], (0.5, 2.0), 150.0, False),
    ("NPC_St_W2", (5550, -8200, ZS), [(5550, -8200), (5600, -14800)], (0.5, 1.5), 140.0, True),
    ("NPC_St_W3", (5700, -11400, ZS), [(5700, -11400), (5650, -12300), (5750, -10700)], (3.0, 7.0), 110.0, False),
    # street, east sidewalk (bollards 7912, facades 8942)
    ("NPC_St_E1", (8450, -15000, ZS), [(8450, -15000), (8400, -7700)], (0.5, 2.0), 145.0, False),
    ("NPC_St_E2", (8500, -8000, ZS), [(8500, -8000), (8450, -15300)], (0.5, 1.5), 155.0, False),
    # crossing at the south crosswalk
    ("NPC_St_X1", (6100, -13400, ZS), [(6100, -13400), (8050, -13400), (8400, -12600), (8050, -13400)], (2.0, 5.0), 135.0, False),
    # transit hub lobby (x 5846..8246, y -4924..-6524)
    ("NPC_Lb_1", (6300, -5400, ZS), [(6300, -5400), (7800, -5450), (7900, -6200), (6300, -6100)], (1.5, 4.0), 120.0, False),
    ("NPC_Lb_2", (7900, -6250, ZS), [(7900, -6250), (7950, -5300)], (4.0, 9.0), 100.0, False),
    # station concourse main hall (floor z 400, x 6250..7250)
    ("NPC_Cn_1", (6900, 600, 400.0), [(6900, 600), (6850, -2900)], (1.0, 3.0), 140.0, False),
    ("NPC_Cn_3", (7150, 2300, 400.0), [(7150, 2300), (7100, 1600), (7000, 1300)], (5.0, 10.0), 100.0, False),   # reading the board
    # north service corridor (x 6550..6900, narrow): one station tech on post against the wall, out of the way
    ("NPC_Cn_2", (6580, 3650, 400.0), [(6580, 3650)], (5.0, 9.0), 100.0, True),
    # east wing (wide): a second officer pacing the security office
    ("NPC_Cn_4", (7700, 2050, 400.0), [(7700, 2050), (8100, 2350), (7600, 2350)], (3.0, 6.0), 110.0, False),
    # east wing security office: officer on post
    ("NPC_Sec_1", (8300, 2000, 400.0), [(8300, 2000)], (5.0, 9.0), 90.0, False),
    # Platform One (north, walk surface z 0, y -250..-1000; track pit y -1130..-1720 is off limits)
    ("NPC_Pf_1", (1200, -600, 40.0), [(1200, -600), (2500, -700), (1200, -600)], (6.0, 12.0), 95.0, False),
    # Platform Two (south, y -1850..-2550): maintenance crew
    ("NPC_Pf_2", (3600, -2250, 40.0), [(3600, -2250), (2200, -2300)], (6.0, 12.0), 100.0, False),
    ("NPC_Pf_3", (1500, -2900, 40.0), [(1500, -2900), (2700, -2950)], (4.0, 8.0), 105.0, True),
]
# Wardrobe from the crowd pack: fitted per sex and build (nrw = regular, ovw = heavyset); darker pieces favoured.
O = "/MetaHumanCrowdContent/Outfits"
# loose, full-cover pieces only: tight or cropped ones (yoga pants, slim jeans, tucked tee, custom tee) let the
# MetaHuman body show through and read as torn clothing
TOPS = ["Tops/OA_Hoodie/Hoodie/meshes", "Tops/OA_Sweater/Sweater/meshes", "Tops/OA_TshirtLngSlv/TshirtLngSlv/Meshes"]
BOTTOMS_M = ["Bottoms/OA_Cargopants/Cargopants/meshes", "Bottoms/OA_Jeans/Jeans/meshes"]
BOTTOMS_F = BOTTOMS_M
SHOES = ["Shoes/OA_Boots/Boots/meshes", "Shoes/OA_Hightop/Hightop/meshes", "Shoes/OA_Runningshoes/Runningshoes/meshes",
         "Shoes/OA_Oxfords/Oxfords/meshes", "Shoes/OA_Loafers/Loafers/meshes", "Shoes/OA_CasualSneakers/CasualSneakers/meshes"]

AR = unreal.AssetRegistryHelpers.get_asset_registry()
# Hair: the MetaHuman grooms ship hair-card static meshes (CardsMesh_Group0_LODn) built around the bind-pose head in
# model space. Cheap, and plenty for passers-by: one card mesh rides each citizen's head bone (see groom_head_offset).
HAIR = "/MetaHumanCharacter/Optional/Grooms/GroomAssets/Hair"
HAIR_F = ["Hair_M_BobStraight", "Hair_S_LowPonytail", "Hair_L_Straight", "Hair_M_BobCurly", "Hair_S_Pixie",
          "Hair_M_TwistedBraids", "Hair_S_UpdoBuns", "Hair_M_Layered", "Hair_L_StraightBangs", "Hair_S_BobLayered"]
HAIR_M = ["Hair_S_BuzzCut", "Hair_S_Casual", "Hair_S_SlickBack", "Hair_S_AfroFade", "Hair_S_CurlyFade",
          "Hair_S_SideSweptFringe", "Hair_S_Messy", "Hair_S_BrushCut", "Hair_S_Clean", "Hair_S_RecedeMessy"]
_HEAD_CS = {}
def groom_head_offset(name):
    """Hair cards are authored around the groom's own reference head (the binding's source mesh: a female or male
    groom head). Their offset from the head bone is the inverse of that head bone's component-space reference
    transform on that mesh; every MetaHuman head shares the bone's frame, so it seats the cards on any citizen."""
    b = unreal.load_asset(f"/MetaHumanCharacter/Optional/Grooms/Bindings/Hair/{name}_Binding")
    m = b.get_editor_property("source_skeletal_mesh") if b else None
    m = m or unreal.load_asset("/MetaHumanCharacter/Optional/Grooms/GroomMesh/SKM_Groom_Head_Legacy01")
    key = m.get_path_name()
    if key not in _HEAD_CS:
        t = EAS.spawn_actor_from_class(unreal.SkeletalMeshActor, V(0, 0, -50000))
        c = t.skeletal_mesh_component
        c.set_skinned_asset_and_update(m)
        _HEAD_CS[key] = c.get_socket_transform("head", unreal.RelativeTransformSpace.RTS_COMPONENT)
        EAS.destroy_actor(t)
        log("groom head", m.get_name(), _HEAD_CS[key].translation)
    return _HEAD_CS[key].inverse()
def hair_cards(name):
    for lod in (1, 0, 2):
        p = f"{HAIR}/{name}/{name}_CardsMesh_Group0_LOD{lod}"
        if unreal.EditorAssetLibrary.does_asset_exist(p):
            return unreal.load_asset(p)
    return None
import importlib.util as _ilu, os as _os
_spec = _ilu.spec_from_file_location("nv_npc_bodymat", _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "nv_npc_bodymat.py"))
BODYMAT = _ilu.module_from_spec(_spec); _spec.loader.exec_module(BODYMAT)

def look_meshes(look_cls):
    """BP_<Shape>_HeadNN -> (body mesh, face mesh) of that assembled MetaHuman."""
    if not look_cls:
        return None, None
    n = look_cls.get_name()[3:-2]             # BP_AverageFemale_Head01_C -> AverageFemale_Head01
    base = f"{ROOT}/{n}"
    body = unreal.load_asset(f"{base}/Body/SKM_MHC_{n}_BodyMesh")
    face = unreal.load_asset(f"{base}/Face/SKM_MHC_{n}_FaceMesh")
    if not body:   # case differences in the pack (e.g. head02 lower-case)
        for ad in AR.get_assets(unreal.ARFilter(package_paths=[base], recursive_paths=True,
                                class_paths=[unreal.TopLevelAssetPath("/Script/Engine", "SkeletalMesh")])):
            nm = str(ad.asset_name).lower()
            if nm.endswith("_bodymesh"): body = unreal.load_asset(str(ad.package_name))
            if nm.endswith("_facemesh"): face = unreal.load_asset(str(ad.package_name))
    return body, face

# let the mannequin AnimBP drive MetaHuman skeletons (skeleton compatibility, set on the project's mannequin skeleton)
_mk = unreal.load_asset("/Game/Characters/Mannequins/Meshes/SK_Mannequin")
_mhsk = set()
for _shape in ("AverageFemale", "AverageMale", "HeavysetFemale", "HeavysetMale"):
    for _h in ("01", "02"):
        _b, _f = look_meshes(unreal.load_object(None, f"{ROOT}/{_shape}_Head{_h}/BP_{_shape}_Head{_h}.BP_{_shape}_Head{_h}_C"))
        if _b:
            _mhsk.add(_b.get_editor_property("skeleton"))
_compat = list(_mk.get_editor_property("compatible_skeletons"))
for _sk in _mhsk:
    if _sk and _sk not in _compat:
        _compat.append(_sk)
_mk.set_editor_property("compatible_skeletons", _compat)
unreal.EditorAssetLibrary.save_loaded_asset(_mk)
log("mannequin compatible skeletons:", [x.get_path_name() for x in _compat])
CLOTH = unreal.TopLevelAssetPath("/Script/ChaosClothAssetEngine", "ChaosClothAsset")

def garment(folder, sex, build):
    """The pack's Chaos cloth garment fitted to this sex/build (folder = OA_x/Name)."""
    root = f"{O}/{folder.rsplit('/', 1)[0]}"
    for ad in AR.get_assets(unreal.ARFilter(package_paths=[root], recursive_paths=True, class_paths=[CLOTH])):
        if str(ad.asset_name).endswith(f"_{sex}_med_{build}"):
            return unreal.load_asset(str(ad.package_name))
    return None

MIC = unreal.TopLevelAssetPath("/Script/Engine", "MaterialInstanceConstant")
def material_for(g, sex, build):
    """The garment's own standalone material instance. The cloth assets default to the MI_crowd_* instances, which
    expect the crowd renderer's per-instance data and draw patchy and see-through ('tattered') on a normal actor."""
    root = g.get_path_name().split("/ClothAssets/")[0] + "/Materials"
    names = [str(a.package_name) for a in AR.get_assets(unreal.ARFilter(package_paths=[root], recursive_paths=True, class_paths=[MIC]))]
    def score(n):
        b = n.split("/")[-1].lower()
        sc = 0 if b.startswith("mi_crowd") else 8
        fem = b.startswith(("m_f_", "f_")) or "/female/" in n.lower()
        sc += 2 if fem == (sex == "f") else 0
        sc += 1 if ("ovw" in b) == (build == "ovw") else 0
        return sc
    names.sort(key=score, reverse=True)
    m = unreal.load_asset(names[0]) if names else None
    return m if (m and not m.get_name().lower().startswith("mi_crowd")) else None

def outfit_for(look_cls):
    n = look_cls.get_name() if look_cls else ""
    sex = "f" if "Female" in n else "m"
    build = "ovw" if "Heavyset" in n else "nrw"
    picks = [rng.choice(TOPS), rng.choice(BOTTOMS_F if sex == "f" else BOTTOMS_M), rng.choice(SHOES)]
    gs = [g for g in (garment(f, sex, build) for f in picks) if g]
    return gs, [material_for(g, sex, build) for g in gs]

for i, (label, (x, y, z), route, waits, speed, courier) in enumerate(NPCS):
    yaw = {"NPC_Sec_1": 180.0, "NPC_Cn_2": 0.0}.get(label, 0.0)
    g = EAS.spawn_actor_from_class(unreal.NVGuardCharacter, V(x, y, z + 100), unreal.Rotator(roll=0, pitch=0, yaw=yaw))
    g.set_actor_label(label); g.set_folder_path(FOLDER); g.tags = [TAG]
    look = LOOKS[i % len(LOOKS)] if LOOKS else None
    # The MetaHuman body itself is the animated mesh (the mannequin AnimBP runs on it through skeleton
    # compatibility), so its twist/corrective bones follow their parents. Leader-posing it to the mannequin left those
    # bones in their rest pose and the body broke through the clothes. The face rides along on the body's head.
    body, face = look_meshes(look)
    if body:
        g.set_editor_property("body_mesh_asset", body)
        g.set_editor_property("appearance_class", None)
    else:
        g.set_editor_property("body_mesh_asset", MANNY)
        g.set_editor_property("appearance_class", look)
    g.set_editor_property("body_anim_class", ABP)
    g.set_editor_property("appearance_offset", unreal.Transform(V(0, 0, -92), unreal.Rotator(roll=0, pitch=0, yaw=-90), V(1, 1, 1)))
    g.set_editor_property("hide_body_under_outfit", False)
    garments, gmats = outfit_for(look)
    parts = ([face] if (body and face) else []) + ([HELMET] if (courier and HELMET) else [])
    g.set_editor_property("outfit_materials", [])
    g.set_editor_property("outfit_parts", parts)
    g.set_editor_property("garment_materials", gmats)
    g.set_editor_property("garments", garments)
    if body and garments:
        try:
            g.get_editor_property("mesh").set_material(0, BODYMAT.body_material(label, body, garments))
        except Exception as e:
            log("body material failed", label, e)
    g.set_editor_property("simulate_garments", False)
    g.set_editor_property("garment_fit", V(1.045, 1.045, 1.0))
    g.set_editor_property("hide_body_under_outfit", False)
    g.set_editor_property("battery_mesh_asset", None)
    hair, hair_off = None, unreal.Transform()
    if not courier:
        female = "Female" in (look.get_name() if look else "")
        hname = (HAIR_F if female else HAIR_M)[i % 10]
        hair = hair_cards(hname)
        if hair:
            hair_off = groom_head_offset(hname)
    g.set_editor_property("helmet_mesh_asset", hair)
    g.set_editor_property("helmet_socket", "head")
    g.set_editor_property("helmet_offset", hair_off)
    g.set_editor_property("helmet_in_model_space", False)
    g.set_editor_property("non_hostile", True)
    g.set_editor_property("glance_radius", 380.0)
    g.set_editor_property("patrol_points", [V(px - x, py - y, 0) for (px, py) in route])
    g.set_editor_property("wait_time_range", unreal.Vector2D(*waits))
    g.set_editor_property("walk_speed", max(170.0, min(235.0, 110.0 + speed * 0.85)) * rng.uniform(0.95, 1.04))  # walk cycle is authored at ~300 cm/s
    try:
        g.get_editor_property("health").set_editor_property("immune_damage_types", IMMUNE)
    except Exception as e:
        log("immune fail", label, e)
    g.set_actor_location(g.get_actor_location(), False, False)
    log(label, "hair", hair.get_name() if hair else None)
    log(label, "look", look.get_name() if look else None, "garments", [x.get_name() for x in garments], [m.get_name() if m else None for m in gmats], "helmet" if parts else "")

NAV = [("NPC_Nav_Street", (7046, -11400, ZS + 200), (3900, 9400, 600)),
       ("NPC_Nav_Lobby", (7046, -5724, ZS + 200), (2500, 1700, 600)),
       ("NPC_Nav_Concourse", (7500, 430, 600), (3400, 9600, 600)),
       ("NPC_Nav_Platform", (2350, -1200, 100), (8000, 5600, 700))]   # both platforms, SW control rooms, crew room annex, service stairs
for label, c, size in NAV:
    nv = EAS.spawn_actor_from_class(unreal.NavMeshBoundsVolume, V(*c))
    nv.set_actor_label(label); nv.set_folder_path(FOLDER); nv.tags = [TAG]
    nv.set_actor_scale3d(V(size[0] / 200.0, size[1] / 200.0, size[2] / 200.0))
# the tram track pit (between the platforms, west of the buffer-end crossover) is never walkable for citizens
for label, c, size in (("NPC_NoNav_Track", (1500, -1425, 0), (6200, 600, 400)),):
    m = EAS.spawn_actor_from_class(unreal.NavModifierVolume, V(*c))
    m.set_actor_label(label); m.set_folder_path(FOLDER); m.tags = [TAG]
    m.set_actor_scale3d(V(size[0] / 200.0, size[1] / 200.0, size[2] / 200.0))
    m.set_editor_property("area_class", unreal.NavArea_Null)
unreal.SystemLibrary.execute_console_command(unreal.EditorLevelLibrary.get_editor_world(), "RebuildNavigation")
LES.save_current_level()
open(unreal.Paths.project_saved_dir() + "NV_npcs.txt", "w").write("\n".join(OUT))
