"""Glass Crown guards v2: longer, more varied routes (world coords, converted to the guard-relative PatrolPoints),
new gallery + antechamber guards (cloned look from B_Guard_Loop), nav bounds for D and E. Movement feel (acceleration,
turn rate) lives in ANVGuardCharacter. Idempotent (G2_ prefix / tag NVG2 for what it adds). Report: Saved/NV_guards2.txt"""
import math
import unreal
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
LES = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
V = unreal.Vector
OUT = []
def log(*a):
    OUT.append(" ".join(str(x) for x in a))
MAP = "/Game/NeonVeil/Maps/M00/L_M00_GlassCrown"
if not unreal.EditorLevelLibrary.get_editor_world().get_path_name().startswith(MAP):
    LES.load_level(MAP)
TAG = "NVG2"
for a in list(EAS.get_all_level_actors()):
    if TAG in a.tags:
        EAS.destroy_actor(a)

def rel_route(actor, pts):
    loc, yaw = actor.get_actor_location(), actor.get_actor_rotation().yaw
    c, s = math.cos(math.radians(-yaw)), math.sin(math.radians(-yaw))
    out = []
    for (wx, wy) in pts:
        dx, dy = wx - loc.x, wy - loc.y
        out.append(V(dx * c - dy * s, dx * s + dy * c, 0))
    return out

def setup(g, route, waits, speed, glance=450.0):
    g.set_editor_property("patrol_points", rel_route(g, route))
    g.set_editor_property("wait_time_range", unreal.Vector2D(*waits))
    g.set_editor_property("walk_speed", speed)
    g.set_editor_property("glance_radius", glance)
    g.set_actor_location(g.get_actor_location(), False, False)

guards = {a.get_actor_label(): a for a in EAS.get_all_level_actors() if isinstance(a, unreal.NVGuardCharacter)}
log("guards:", sorted(guards))
# Atrium (x 3500..5850, y -1100..1100; sculpture in the middle, arch at x 5900)
ROUTES = {
    # strolls the whole atrium perimeter, brief pauses at the corners
    "B_Guard_Loop": ([(3800, -820), (4900, -880), (5600, -650), (5650, 50), (5550, 760), (4600, 860), (3800, 650), (3750, -100)],
                     (0.6, 2.2), 135.0),
    # walks the glazing, stopping to look out over the city
    "B_Guard_Glazing": ([(3750, 860), (4500, 900), (5400, 880), (4500, 900)], (3.0, 6.5), 115.0),
    # keeps the arch, shifting between both sides and a step back
    "B_Guard_Arch": ([(5750, 330), (5720, 700), (5560, 420), (5750, -330), (5720, -700), (5560, -420)], (2.5, 5.0), 105.0),
}
for name, (route, waits, speed) in ROUTES.items():
    if name in guards:
        setup(guards[name], route, waits, speed)
        log("route", name, len(route), "points")

# new guards, cloned from the loop guard's look
src = guards.get("B_Guard_Loop")
COPY = ("body_mesh_asset", "body_anim_class", "outfit_parts", "hide_body_under_outfit", "battery_mesh_asset",
        "battery_offset", "appearance_class", "helmet_mesh_asset", "non_hostile")
NEW = [
    # gallery (x 10650..14800, y -400..400; data wall on the south side): slow beat along the exhibits
    ("G2_D_Guard_Gallery", (11000, 160, 100), 0.0, [(11000, 160), (12500, 200), (14300, 140), (12500, 200)], (2.5, 5.0), 110.0, "D_Gallery"),
    # antechamber (x 14800..16400, y -700..700; pillars at x 15200/15900 y +-450): sentry by the dark glass
    ("G2_E_Guard_Sentry", (16050, -560, 100), 90.0, [(16050, -560), (16050, -160), (15600, -600)], (4.0, 8.0), 95.0, "E_Antechamber"),
]
for label, loc, yaw, route, waits, speed, folder in NEW:
    g = EAS.spawn_actor_from_class(unreal.NVGuardCharacter, V(*loc), unreal.Rotator(roll=0, pitch=0, yaw=yaw))
    g.set_actor_label(label); g.set_folder_path(folder); g.tags = [TAG]
    if src:
        for k in COPY:
            try:
                g.set_editor_property(k, src.get_editor_property(k))
            except Exception as e:
                log("copy fail", k, e)
        try:
            g.get_editor_property("health").set_editor_property(
                "immune_damage_types", src.get_editor_property("health").get_editor_property("immune_damage_types"))
        except Exception as e:
            log("immune copy fail", e)
    setup(g, route, waits, speed)
    log("spawned", label)

for label, c, size in (("G2_D_NavBounds", (12725, 0, 250), (4300, 820, 520)), ("G2_E_NavBounds", (15600, 0, 300), (1620, 1420, 620))):
    nv = EAS.spawn_actor_from_class(unreal.NavMeshBoundsVolume, V(*c))
    nv.set_actor_label(label); nv.tags = [TAG]
    nv.set_actor_scale3d(V(size[0] / 200.0, size[1] / 200.0, size[2] / 200.0))
unreal.SystemLibrary.execute_console_command(unreal.EditorLevelLibrary.get_editor_world(), "RebuildNavigation")
LES.save_current_level()
open(unreal.Paths.project_saved_dir() + "NV_guards2.txt", "w").write("\n".join(OUT))
