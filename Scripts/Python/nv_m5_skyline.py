"""NEON VEIL - M5 art pass: Veyra-9 skyline (Bible §4 hero shot, spaces A and B).

Replaces the near TEMP skyline blocks with City Sample hero/reference buildings (packed level
blueprints, Nanite). The Crown sits at the top of the Directorate tower, so towers are placed with
deep bases (hidden in the height fog) and staggered tops around eye level, building the tiered,
layered skyline the Bible asks for. Far TEMP blocks stay as distant massing.

Re-runnable (clears folder Skyline_CS first). Report: Saved/NV_m5_skyline.txt
"""
import math, random
import unreal

REPORT = []
def log(*a):
    msg = " ".join(str(x) for x in a)
    REPORT.append(msg)
    unreal.log("[NV M5 sky] " + msg)

EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
LES = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
EAL = unreal.EditorAssetLibrary
FOLDER = "Skyline_CS"
ROOTS = ["/Game/CitySampleBuildings/Building/Library/Kit_Hero_Bldg/LevelInstance",
         "/Game/CitySampleBuildings/Building/Library/Kit_Ref_Bldg/LevelInstance"]
CENTER = unreal.Vector(5000, 0, 0)          # atrium; the hero view looks north (+Y)
NEAR_CLEAR = 26000.0                         # TEMP blocks closer than this are removed

def classes():
    out = []
    for root in ROOTS:
        for p in EAL.list_assets(root, recursive=False):
            name = p.split("/")[-1].split(".")[0]
            if not name.startswith("BPP_") or "Level01" in name:
                continue
            gen = EAL.load_blueprint_class(p.split(".")[0])
            if gen:
                out.append((name, gen))
    return out

def mesh_bounds(actor):
    """World AABB of every (instanced) static mesh in a packed level actor."""
    lo = [1e18, 1e18, 1e18]; hi = [-1e18, -1e18, -1e18]
    n = 0
    for c in actor.get_components_by_class(unreal.StaticMeshComponent):
        sm = c.get_editor_property("static_mesh")
        if not sm:
            continue
        bb = sm.get_bounding_box()
        corners = [unreal.Vector(x, y, z) for x in (bb.min.x, bb.max.x) for y in (bb.min.y, bb.max.y) for z in (bb.min.z, bb.max.z)]
        if isinstance(c, unreal.InstancedStaticMeshComponent):
            xfs = [c.get_instance_transform(i, True) for i in range(c.get_instance_count())]
        else:
            xfs = [c.get_world_transform()]
        for t in xfs:
            for v in corners:
                w = t.transform_location(v)
                lo = [min(lo[0], w.x), min(lo[1], w.y), min(lo[2], w.z)]
                hi = [max(hi[0], w.x), max(hi[1], w.y), max(hi[2], w.z)]
                n += 1
    if not n:
        return None
    o = unreal.Vector((lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, (lo[2] + hi[2]) / 2)
    e = unreal.Vector((hi[0] - lo[0]) / 2, (hi[1] - lo[1]) / 2, (hi[2] - lo[2]) / 2)
    return o, e

def main():
    random.seed(9)
    # clear previous pass + near TEMP blocks
    removed = 0
    for a in EAS.get_all_level_actors():
        folder = str(a.get_folder_path())
        label = a.get_actor_label()
        if folder == FOLDER:
            EAS.destroy_actor(a); removed += 1
        elif folder == "Skyline" and label.startswith("City"):
            d = (a.get_actor_location() - CENTER)
            if math.hypot(d.x, d.y) < NEAR_CLEAR:
                EAS.destroy_actor(a); removed += 1
    log("removed", removed)

    cls = classes()
    log("building classes:", len(cls))
    if not cls:
        log("ERROR no City Sample BPP classes found")
        return
    # measure each class once
    sizes = {}
    for name, c in cls:
        a = EAS.spawn_actor_from_class(c, unreal.Vector(0, 0, 0), unreal.Rotator())
        mb = mesh_bounds(a)
        EAS.destroy_actor(a)
        if mb and mb[1].z > 1500:          # keep real buildings (>30 m)
            sizes[name] = mb
    cls = [t for t in cls if t[0] in sizes]
    tall = sorted(cls, key=lambda t: -sizes[t[0]][1].z)
    for name, _ in tall:
        o, e = sizes[name]
        log(f"  {name}: footprint {2*e.x/100:.0f}x{2*e.y/100:.0f} m, height {2*e.z/100:.0f} m")

    placed = 0
    occupied = []
    def free(x, y, r):
        return all(math.hypot(x - ox, y - oy) > (r + orr) for ox, oy, orr in occupied)

    # rings: north (hero glazing) dense, south and east sparser
    plan = [(+1, 40, 7000, 45000), (-1, 22, 7000, 40000)]
    for side, count, rmin, rmax in plan:
        tries = 0
        n = 0
        while n < count and tries < 2000:
            tries += 1
            name, c = random.choice(tall[: max(6, len(tall))])
            o, e = sizes[name]
            scale = random.uniform(1.0, 1.7)
            foot = max(e.x, e.y) * scale
            x = CENTER.x + random.uniform(-26000, 34000)
            y = side * random.uniform(rmin, rmax)
            if not free(x, y, foot + 600):
                continue
            # tops staggered around the Crown's eye level; nearer towers sit lower (looking down)
            dist = math.hypot(x - CENTER.x, y)
            top = random.uniform(-9000, 2500) + (dist / 45000.0) * 9000.0
            h = 2 * e.z * scale
            base_z = top - h
            if base_z > -9000:          # bases must stay deep in the fog
                scale *= (top + 9000) / h
                h = 2 * e.z * scale
                base_z = top - h
            yaw = random.choice([0, 90, 180, 270]) + random.uniform(-4, 4)
            a = EAS.spawn_actor_from_class(c, unreal.Vector(x, y, 0), unreal.Rotator(yaw=yaw))
            a.set_actor_scale3d(unreal.Vector(scale, scale, scale))
            # actor origin -> mesh bottom offset (scaled)
            bottom_off = (o.z - e.z) * scale
            a.set_actor_location(unreal.Vector(x, y, base_z - bottom_off), False, False)
            a.set_folder_path(FOLDER)
            a.set_actor_label(f"CS_{name.replace('BPP_', '')}_{placed:02d}")
            occupied.append((x, y, foot))
            placed += 1
            n += 1
    log("placed", placed, "buildings")
    LES.save_current_level()

try:
    main()
finally:
    with open(unreal.Paths.project_saved_dir() + "NV_m5_skyline.txt", "w", encoding="utf-8") as fh:
        fh.write("\n".join(REPORT))
