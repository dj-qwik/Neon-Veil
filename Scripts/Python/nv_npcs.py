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
for shape in ("AverageFemale", "AverageMale", "TallFemale", "TallMale", "ShortFemale", "ShortMale", "HeavysetFemale", "HeavysetMale"):
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
ABP = unreal.load_object(None, "/Game/Characters/Mannequins/Anims/Unarmed/ABP_Unarmed.ABP_Unarmed_C")
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
    # station concourse (floor z 400 walkable at x 6250..7250; east of 7300 is open void)
    ("NPC_Cn_1", (6900, 600, 400.0), [(6900, 600), (6950, 4600)], (1.0, 3.0), 140.0, False),
    ("NPC_Cn_2", (6600, 4600, 400.0), [(6600, 4600), (6650, 700)], (1.0, 3.0), 135.0, True),
    ("NPC_Cn_3", (7150, 2300, 400.0), [(7150, 2300), (7100, 1600), (7000, 1300)], (5.0, 10.0), 100.0, False),   # reading the board
    ("NPC_Cn_4", (6800, 3200, 400.0), [(6800, 3200), (7100, 3900), (6700, 4700)], (2.0, 5.0), 125.0, False),
    # platform (walk surface z ~ -40; west half x 1000..2600 at y -1420)
    ("NPC_Pf_1", (1200, -1400, 40.0), [(1200, -1400), (2600, -1450), (1200, -1400)], (6.0, 12.0), 95.0, False),
    ("NPC_Pf_2", (2400, -1460, 40.0), [(2400, -1460), (1700, -1430)], (6.0, 12.0), 100.0, False),
]
# Wardrobe from the crowd pack: fitted per sex and build (nrw = regular, ovw = heavyset); darker pieces favoured.
O = "/MetaHumanCrowdContent/Outfits"
TOPS = ["Tops/OA_Hoodie/Hoodie/meshes", "Tops/OA_Sweater/Sweater/meshes", "Tops/OA_TshirtLngSlv/TshirtLngSlv/Meshes",
        "Tops/OA_Customt/Customt/Meshes", "Tops/OA_TshirtTkPushCufSlv/OA_TshirtTkPushCufSlv/meshes"]
BOTTOMS_M = ["Bottoms/OA_Cargopants/Cargopants/meshes", "Bottoms/OA_Jeans/Jeans/meshes", "Bottoms/OA_Jeans_slm/Jeans_slm/meshes"]
BOTTOMS_F = BOTTOMS_M + ["Bottoms/OA_Yogaful/Yogaful/meshes"]
SHOES = ["Shoes/OA_Boots/Boots/meshes", "Shoes/OA_Hightop/Hightop/meshes", "Shoes/OA_Runningshoes/Runningshoes/meshes",
         "Shoes/OA_Oxfords/Oxfords/meshes", "Shoes/OA_Loafers/Loafers/meshes", "Shoes/OA_CasualSneakers/CasualSneakers/meshes"]

AR = unreal.AssetRegistryHelpers.get_asset_registry()
CLOTH = unreal.TopLevelAssetPath("/Script/ChaosClothAssetEngine", "ChaosClothAsset")

def garment(folder, sex, build):
    """The pack's Chaos cloth garment fitted to this sex/build (folder = OA_x/Name)."""
    root = f"{O}/{folder.rsplit('/', 1)[0]}"
    for ad in AR.get_assets(unreal.ARFilter(package_paths=[root], recursive_paths=True, class_paths=[CLOTH])):
        if str(ad.asset_name).endswith(f"_{sex}_med_{build}"):
            return unreal.load_asset(str(ad.package_name))
    return None

def outfit_for(look_cls):
    n = look_cls.get_name() if look_cls else ""
    sex = "f" if "Female" in n else "m"
    build = "ovw" if "Heavyset" in n else "nrw"
    picks = [rng.choice(TOPS), rng.choice(BOTTOMS_F if sex == "f" else BOTTOMS_M), rng.choice(SHOES)]
    return [g for g in (garment(f, sex, build) for f in picks) if g]

for i, (label, (x, y, z), route, waits, speed, courier) in enumerate(NPCS):
    yaw = 0.0
    g = EAS.spawn_actor_from_class(unreal.NVGuardCharacter, V(x, y, z + 100), unreal.Rotator(roll=0, pitch=0, yaw=yaw))
    g.set_actor_label(label); g.set_folder_path(FOLDER); g.tags = [TAG]
    g.set_editor_property("body_mesh_asset", MANNY)
    g.set_editor_property("body_anim_class", ABP)
    g.set_editor_property("appearance_class", LOOKS[i % len(LOOKS)] if LOOKS else None)
    look = LOOKS[i % len(LOOKS)] if LOOKS else None
    garments = outfit_for(look)
    parts = [HELMET] if (courier and HELMET) else []
    g.set_editor_property("outfit_materials", [])
    g.set_editor_property("outfit_parts", parts)
    g.set_editor_property("garments", garments)
    g.set_editor_property("simulate_garments", False)
    g.set_editor_property("hide_body_under_outfit", False)
    g.set_editor_property("battery_mesh_asset", None)
    g.set_editor_property("helmet_mesh_asset", None)
    g.set_editor_property("non_hostile", True)
    g.set_editor_property("glance_radius", 380.0)
    g.set_editor_property("patrol_points", [V(px - x, py - y, 0) for (px, py) in route])
    g.set_editor_property("wait_time_range", unreal.Vector2D(*waits))
    g.set_editor_property("walk_speed", speed * rng.uniform(0.92, 1.06))
    try:
        g.get_editor_property("health").set_editor_property("immune_damage_types", IMMUNE)
    except Exception as e:
        log("immune fail", label, e)
    g.set_actor_location(g.get_actor_location(), False, False)
    log(label, "look", look.get_name() if look else None, "garments", [x.get_name() for x in garments], "helmet" if parts else "")

NAV = [("NPC_Nav_Street", (7046, -11400, ZS + 200), (3900, 9400, 600)),
       ("NPC_Nav_Lobby", (7046, -5724, ZS + 200), (2500, 1700, 600)),
       ("NPC_Nav_Concourse", (7246, 430, 600), (2900, 9400, 600)),
       ("NPC_Nav_Platform", (2830, -1525, 100), (5000, 3700, 700))]
for label, c, size in NAV:
    nv = EAS.spawn_actor_from_class(unreal.NavMeshBoundsVolume, V(*c))
    nv.set_actor_label(label); nv.set_folder_path(FOLDER); nv.tags = [TAG]
    nv.set_actor_scale3d(V(size[0] / 200.0, size[1] / 200.0, size[2] / 200.0))
unreal.SystemLibrary.execute_console_command(unreal.EditorLevelLibrary.get_editor_world(), "RebuildNavigation")
LES.save_current_level()
open(unreal.Paths.project_saved_dir() + "NV_npcs.txt", "w").write("\n".join(OUT))
