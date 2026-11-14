"""Temporary lineup of civilian candidate meshes in the Crown atrium for a look (arg 'clear' removes it)."""
import sys
import unreal
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for a in list(EAS.get_all_level_actors()):
    if a.get_actor_label().startswith("LINEUP_"):
        EAS.destroy_actor(a)
if sys.argv[-1] != "clear":
    W = "/Game/Mercenary_Male_WaveforceStudio/Mesh/Modular/"
    O = "/Game/Outfits/"
    AR = unreal.AssetRegistryHelpers.get_asset_registry()
    def find(name, root):
        for d in AR.get_assets_by_path(root, recursive=True):
            if str(d.asset_name) == name:
                return d.get_asset()
    SETS = [
        ("merc", [W + p for p in ("SK_MER_ME_Body", "SK_MER_ME_Outer01", "SK_MER_ME_Pant01", "SK_MER_ME_Shoes01",
                                  "SK_MER_ME_Common", "SK_MER_ME_Hair01", "SK_MER_ME_Glass01")]),
        ("mercfull", [W + p for p in ("SK_MER_ME_Body", "SK_MER_ME_Outfit01", "SK_MER_ME_Common", "SK_MER_ME_Hair01")]),
        ("shapeA", ["bodyShapeAof4_CombinedSkelMesh"]), ("shapeB", ["bodyShapeBof4_CombinedSkelMesh"]),
        ("shapeC", ["bodyShapeCof4_CombinedSkelMesh"]), ("shapeD", ["bodyShapeDof4_CombinedSkelMesh"]),
        ("david", ["David_CombinedSkelMesh"]), ("tall", ["SK_Metahuman_Tall_Normal_Male"]), ("soldier", ["Soldier_Outfit_v1"]),
        ("quinn", ["/Game/Characters/Mannequins/Meshes/SKM_Quinn_Simple"]),
    ]
    out = []
    for i, (n, parts) in enumerate(SETS):
        x = 3800 + i * 170
        for j, p in enumerate(parts):
            m = unreal.load_asset(p) if p.startswith("/Game/") else find(p, O)
            if not m:
                out.append("missing " + p); continue
            a = EAS.spawn_actor_from_class(unreal.SkeletalMeshActor, unreal.Vector(x, -500, 4), unreal.Rotator(0, 0, 0))
            a.skeletal_mesh_component.set_skeletal_mesh_asset(m)
            a.set_actor_label(f"LINEUP_{n}_{j}")
        out.append(f"{n} at x={x}")
    open(unreal.Paths.project_saved_dir() + "NV_npc_lineup.txt", "w").write("\n".join(out))
