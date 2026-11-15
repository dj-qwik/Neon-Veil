"""NEON VEIL - prologue station walkthrough v2: every room of the Crown Line station is on the critical path.

Route (each step unlocks the next; nothing can be skipped):
  lift -> concourse south hall (X-ray) -> north hall: departure board says Platform One is locked for a track inspection
  -> north service corridor (Station Ops): pick up a crew pass
  -> east wing security office: register the pass (east wing gate opens after the pass)
  -> back down the hall to the south service stairs (open after registering) -> Platform Two
  -> Platform Two control room (south-west rooms): restore Platform One power
  -> buffer-end crossover (opens after power) -> Platform One: slide under the shutter
  -> crew room (north annex): collect your gear -> vault the crates -> Platform One boarding point -> tram.
The north stairs (Platform One) stay sealed for the inspection, so the player always arrives along the platforms.

Run after nv_l1_build_prologue.py (which it is called from). Idempotent: its own actors live in folder P_Route.
Report: Saved/NV_station_route.txt"""
import unreal

OUT = []
def log(*a):
    OUT.append(" ".join(str(x) for x in a))

EAL = unreal.EditorAssetLibrary
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
LES = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
V = lambda x, y, z: unreal.Vector(x, y, z)
def R(p=0.0, y=0.0, r=0.0):
    return unreal.Rotator(roll=r, pitch=p, yaw=y)
def T(s):
    return unreal.Text(s)
def tag(n):
    t = unreal.GameplayTag(); t.import_text(f'(TagName="{n}")'); return t
def line(spk, txt, d=4.0):
    l = unreal.NVSubtitleLine(); l.set_editor_property("speaker", T(spk)); l.set_editor_property("text", T(txt))
    l.set_editor_property("duration", d)
    return l
def load(p):
    a = unreal.load_asset(p)
    if not a:
        log("MISSING", p)
    return a
def sp(o, name, val):
    try:
        o.set_editor_property(name, val); return True
    except Exception as e:
        log("SET FAIL", type(o).__name__, name, e); return False

MAP = "/Game/NeonVeil/Maps/M00/L_M00_Prologue"
if not unreal.EditorLevelLibrary.get_editor_world().get_path_name().startswith(MAP):
    LES.load_level(MAP)

FOLDER, TAG = "P_Route", "NVROUTE"
for a in list(EAS.get_all_level_actors()):
    if str(a.get_folder_path()) == FOLDER or TAG in [str(t) for t in a.tags]:
        EAS.destroy_actor(a)

def find(label):
    for a in EAS.get_all_level_actors():
        if a.get_actor_label() == label:
            return a
    log("not found:", label)
    return None

def spawn(cls, label, loc, rot=None):
    a = EAS.spawn_actor_from_class(cls, V(*loc), rot or R())
    a.set_actor_label(label); a.set_folder_path(FOLDER); a.tags = [unreal.Name(TAG)]
    return a

TS = "/Game/SciFiTramStation"
CONSOLE = load("/Game/ModularScifiInterior/Meshes/Props/SM_Console")
HOLO = load(f"{TS}/Meshes/SM_Holoscreen_A")
CUBE = load("/Engine/BasicShapes/Cube")
M_DOOR = load(f"{TS}/Materials/MI_Door_A")
M_SIGNTEXT = None
for a in EAS.get_all_level_actors():
    if a.get_actor_label() == "S_Board":
        M_SIGNTEXT = a.text_render.get_material(0)

# ------------------------------------------------------------------ mission
mission = load("/Game/NeonVeil/Data/Missions/DA_Mission_M00P")
def obj(oid, text, event, prereq=None):
    o = unreal.NVObjectiveDef()
    o.set_editor_property("objective_id", oid); o.set_editor_property("display_text", T(text))
    o.set_editor_property("completion_event_tag", tag(event)); o.set_editor_property("prerequisites", [prereq] if prereq else [])
    o.set_editor_property("checkpoint_policy", unreal.NVCheckpointPolicy.NONE)
    return o
mission.set_editor_property("objectives", [
    obj("M00P-O01", "Head to the Veyra Central transit hub", "NV.Event.M00P.EnteredTransitHub"),
    obj("M00P-O02", "Take the lift to the Crown Line concourse", "NV.Event.M00P.LiftArrived", "M00P-O01"),
    obj("M00P-O03", "Check the Crown Line departure board", "NV.Event.M00P.DeparturesChecked", "M00P-O02"),
    obj("M00P-O04", "Collect your crew pass from Station Ops (north service corridor)", "NV.Event.M00P.PassCollected", "M00P-O03"),
    obj("M00P-O05", "Register the pass at the security office (east wing)", "NV.Event.M00P.PassRegistered", "M00P-O04"),
    obj("M00P-O06", "Restore Platform One power from the Platform Two control room", "NV.Event.M00P.PlatformPowered", "M00P-O05"),
    obj("M00P-O07", "Collect your gear from the Platform One crew room", "NV.Event.M00P.GearCollected", "M00P-O06"),
    obj("M00P-O08", "Go to the Platform One boarding point", "NV.Event.M00P.PlatformReached", "M00P-O07"),
    obj("M00P-O09", "Board the tram to the Glass Crown", "NV.Event.M00P.TramBoarded", "M00P-O08"),
])
EAL.save_loaded_asset(mission)
log("mission objectives:", len(mission.get_editor_property("objectives")))

# ------------------------------------------------------------------ concourse: board, ops pass, security desk
board = find("I_DepartureBoard")
if board:
    sp(board, "lines_on_use", [
        line("Ops Monitor", "Crown Line, Platform One. Locked down for a track inspection, Ghost-7.", 4.6),
        line("Ops Monitor", "Station Ops left a crew pass for you in the north service corridor. That gets you down the service side.", 5.8)])

def terminal(label, loc, yaw, prompt, event, objective, lines, mesh=None, scale=None):
    t = spawn(unreal.NVInteractableActor, label, loc, R(y=yaw))
    m = t.get_editor_property("mesh")
    m.set_static_mesh(mesh or CONSOLE)
    if scale:
        sp(m, "relative_scale3d", V(*scale))
    sp(t, "prompt", T(prompt))
    sp(t, "completion_event_tag", tag(event))
    sp(t, "required_active_objective", objective)
    sp(t, "lines_on_use", lines)
    return t

terminal("I_CrewPass", (6720, 4780, 400), -90, "Collect crew pass", "NV.Event.M00P.PassCollected", "M00P-O04", [
    line("Station Ops", "Crew pass, Ghost-7. Have Security register it in the east wing before you go anywhere near the tracks.", 6.0)])
terminal("I_SecurityDesk", (8470, 2190, 400), 180, "Register crew pass", "NV.Event.M00P.PassRegistered", "M00P-O05", [
    line("Security", "Pass registered. Service stairs to Platform Two are open.", 3.8),
    line("Security", "Platform One is dark. Throw the breaker in the Platform Two control room, then cross at the buffer end.", 6.0)])
terminal("I_PowerPanel", (650, -3050, 0), 90, "Restore Platform One power", "NV.Event.M00P.PlatformPowered", "M00P-O06", [
    line("Ops Monitor", "Platform One is live again. Crossover at the buffer end is open.", 4.4),
    line("Ops Monitor", "Your kit's in the crew room off Platform One. Pick it up on your way.", 4.4)])
terminal("I_GearLocker", (3720, 1000, 0), 0, "Collect your gear", "NV.Event.M00P.GearCollected", "M00P-O07", [
    line("Ops Monitor", "That's everything. Your car is inbound. Platform One, west end.", 4.2)])

# ------------------------------------------------------------------ gates
def gate(label, loc, yaw, width, open_when):
    d = spawn(unreal.NVObjectiveDoor, label, loc, R(y=yaw))
    half = width / 4.0
    for comp_name, s in (("panel_left", -1), ("panel_right", 1)):
        c = d.get_editor_property(comp_name)
        c.set_static_mesh(CUBE)
        sp(c, "relative_location", V(0, s * half, 175))
        sp(c, "relative_scale3d", V(0.1, width / 200.0, 3.5))
        c.set_material(0, M_DOOR)
    if open_when:
        sp(d, "open_when_complete", open_when)
    sp(d, "slide_distance", width / 2.0)
    return d
gate("G_Gate_East", (7390, 2190, 400), 0, 720, "M00P-O04")          # east wing, after the pass
gate("G_Crossover", (5060, -1450, 0), 90, 820, "M00P-O06")          # buffer-end crossover, after power
for lab, ow in (("G_Gate_South", "M00P-O05"), ("G_Gate_North", "")):
    g = find(lab)
    if g:
        sp(g, "open_when_complete", ow)
# full-width, full-height stair gates + side blockers (nv_stair_gates.py)
import os
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "nv_stair_gates.py")).read(), {"__name__": "nv_stair_gates"})

# ------------------------------------------------------------------ tutorials, triggers, tram
def retune(label, **kw):
    a = find(label)
    if not a:
        return
    for k, v in kw.items():
        if k == "center":
            a.set_actor_location(V(*v), False, False)
        elif k == "extent":
            a.get_editor_property("volume").set_box_extent(V(*v))
        else:
            sp(a, k, v)
retune("Tut_Sprint", center=(2600, -2220, 120), extent=(1700, 330, 150), required_active_objective="M00P-O06")
retune("Tut_Slide", required_active_objective="M00P-O07")
retune("Tut_Vault", required_active_objective="M00P-O08")
retune("T_PlatformOne", required_active_objective="M00P-O08")
retune("B_TramService", arrive_on_objective="M00P-O09")
p2 = spawn(unreal.NVObjectiveTrigger, "T_PlatformTwo", (4300, -2220, 120))
p2.get_editor_property("volume").set_box_extent(V(400, 380, 150))
sp(p2, "required_active_objective", "M00P-O06")
sp(p2, "lines_on_complete", [line("Station PA", "Platform Two is closed for maintenance. Authorised personnel only.", 4.2)])

# slide shutter: the crouched/sliding capsule is 116 cm tall, the old 115 cm gap stopped it dead
sh = find("Shutter_Slide")
if sh:
    l = sh.get_actor_location()
    sh.set_actor_location(V(l.x, l.y, 140 + 150), False, False)

# platform-to-car gap fillers: the docked car stands ~10 cm off each platform edge over a 4.5 m pit; walk-on plates
# (invisible, pawn-only) keep anyone from dropping between platform and doors
for lab, y0, y1 in (("Plat_GapFill_N", -1190, -1060), ("Plat_GapFill_S", -1840, -1650)):
    a = EAS.spawn_actor_from_object(CUBE, V(2200, (y0 + y1) / 2, -5), R())
    a.set_actor_scale3d(V(4400 / 100.0, (y1 - y0) / 100.0, 0.1))
    a.set_actor_label(lab); a.set_folder_path(FOLDER); a.tags = [unreal.Name(TAG)]
    c = a.static_mesh_component
    c.set_collision_profile_name("InvisibleWall")
    a.set_actor_hidden_in_game(True)
    c.set_editor_property("can_ever_affect_navigation", False)

# the station's BP_Door_A only senses people on ONE side (its trigger box sits 70 cm off-centre), so the north
# service corridor door could not be opened from the concourse. Centre the trigger and make it reach both sides.
for a in EAS.get_all_level_actors():
    if a.get_class().get_name() == "BP_Door_A_C":
        for c in a.get_components_by_class(unreal.BoxComponent):
            sp(c, "relative_location", V(0, 0, 170))
            c.set_box_extent(V(160, 260, 170))
        log("door trigger centred:", a.get_actor_label())

# ------------------------------------------------------------------ signs
def sign(label, text, loc, yaw, size=30.0, color=(0.35, 0.95, 1.0)):
    a = spawn(unreal.TextRenderActor, label, loc, R(y=yaw))
    t = a.text_render
    sp(t, "text", T(text)); sp(t, "world_size", size)
    sp(t, "horizontal_alignment", unreal.HorizTextAligment.EHTA_CENTER)
    sp(t, "vertical_alignment", unreal.VerticalTextAligment.EVRTA_TEXT_CENTER)
    sp(t, "text_render_color", unreal.Color(int(color[0] * 255), int(color[1] * 255), int(color[2] * 255), 255))
    if M_SIGNTEXT:
        t.set_material(0, M_SIGNTEXT)
    return a
ORANGE = (1.0, 0.55, 0.15)
for lab, txt, col in (("S_StairsN", "PLATFORM 1 STAIRS  ·  CLOSED  ·  TRACK INSPECTION", ORANGE),
                      ("S_StairsS", "SERVICE STAIRS  ·  PLATFORM 2  ·  CREW ONLY", ORANGE)):
    s = find(lab)
    if s:
        sp(s.text_render, "text", T(txt))
sign("S_OpsCorridor", "STATION OPS  ·  SERVICE CORRIDOR", (6740, 2560, 700), -90, 26)
sign("S_EastWing", "SECURITY OFFICE  ·  EAST WING", (7330, 2190, 700), 180, 26)
sign("S_P2Control", "PLATFORM 2  ·  CONTROL ROOM", (500, -2480, 330), 180, 24, ORANGE)
sign("S_Crossover", "CROSSOVER  ·  PLATFORM 1", (5060, -1830, 330), -90, 24)
sign("S_CrewRoom", "CREW ROOM", (3880, -230, 330), 0, 24)

# ------------------------------------------------------------------ X-ray arch: walk-through collision
for a in EAS.get_all_level_actors():
    if a.get_actor_label().startswith("XRay_") and isinstance(a, unreal.StaticMeshActor):
        m = a.static_mesh_component.static_mesh
        bs = m.get_editor_property("body_setup")
        bs.set_editor_property("collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
        EAL.save_loaded_asset(m)
        log("xray collision -> complex:", m.get_name())

LES.save_current_level()
open(unreal.Paths.project_saved_dir() + "NV_station_route.txt", "w").write("\n".join(OUT))
