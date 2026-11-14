"""PIE: walk Ghost through the prologue station route on foot (pathfinding moves on the real collision), using each
terminal as the player would, and log what happens. Start it once PIE is running; it drives itself on slate ticks.
Report (live): Saved/NV_route_walk.txt; photos: Saved/NV_shots/walk_<n>.png"""
import os, time
import unreal

UES = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
W = UES.get_game_world()
PC = unreal.GameplayStatics.get_player_controller(W, 0)
PAWN = unreal.GameplayStatics.get_player_pawn(W, 0)
SAV = unreal.Paths.project_saved_dir()
SHOTS = os.path.join(SAV, "NV_shots")
os.makedirs(SHOTS, exist_ok=True)
LOG = []
def log(*a):
    LOG.append(f"[{time.strftime('%H:%M:%S')}] " + " ".join(str(x) for x in a))
    open(SAV + "NV_route_walk.txt", "w").write("\n".join(LOG))
V = unreal.Vector

def obj_sys():
    for o in unreal.ObjectIterator(unreal.NVObjectiveSubsystem):
        if o.get_current_mission():
            return o
def tag(n):
    t = unreal.GameplayTag(); t.import_text(f'(TagName="{n}")'); return t
def find(label):
    for a in unreal.GameplayStatics.get_all_actors_of_class(W, unreal.Actor):
        if a.get_actor_label() == label:
            return a
def active():
    o = obj_sys()
    return [str(x.get_editor_property("objective_id")) for x in o.get_active_objectives()] if o else []
def shot(n):
    p = os.path.join(SHOTS, f"walk_{n}.png").replace("\\", "/")
    unreal.SystemLibrary.execute_console_command(W, f'HighResShot 1280x720 filename="{p}"')
def face(x, y):
    l = PAWN.get_actor_location()
    PC.set_control_rotation(unreal.Rotator(roll=0, pitch=-5, yaw=unreal.MathLibrary.find_look_at_rotation(l, V(x, y, l.z)).yaw))
def gate_state(label):
    g = find(label)
    return g.is_open() if g else "missing"

# ('move', x, y, z)  ('use', label)  ('note', text)  ('gate', label)  ('wait_obj', id, timeout)  ('tp', x, y, z, yaw)
# ('event', tag)  ('sweep_slide',)  ('shot',)
STEPS = [
    ("event", "NV.Event.M00P.EnteredTransitHub"), ("event", "NV.Event.M00P.LiftArrived"),
    ("tp", 7046, -4080, 500, 90), ("note", "concourse, lift doors behind"),
    ("gate", "G_Gate_East"), ("gate", "G_Gate_South"), ("gate", "G_Gate_North"),
    ("move", 7045, -3200, 400), ("note", "through the X-ray arch"), ("shot",),
    ("move", 6950, 1600, 400), ("use", "I_DepartureBoard"), ("shot",),
    ("move", 6800, 2450, 400), ("move", 6800, 3000, 400), ("move", 6720, 4560, 400), ("use", "I_CrewPass"), ("shot",),
    ("gate", "G_Gate_East"),
    ("move", 6800, 3000, 400), ("move", 6800, 2300, 400), ("move", 8250, 2190, 400), ("use", "I_SecurityDesk"), ("shot",),
    ("gate", "G_Gate_South"),
    ("move", 6550, -2225, 400), ("note", "top of the service stairs"),
    ("move", 4300, -2220, 0), ("shot",),
    ("move", 846, -2400, 0), ("move", 846, -2950, 0), ("move", 750, -3000, 0), ("use", "I_PowerPanel"), ("shot",),
    ("gate", "G_Crossover"),
    ("move", 5150, -1450, 0), ("move", 5150, -700, 0), ("note", "crossed onto Platform One"), ("shot",),
    ("sweep_slide",),
    ("tp", 4000, -615, 120, 180), ("note", "past the shutter (slide checked by sweep)"),
    ("move", 3720, 850, 0), ("use", "I_GearLocker"), ("shot",),
    ("move", 3300, -615, 0), ("tp", 2700, -615, 120, 180), ("note", "past the vault crates"),
    ("move", 1910, -700, 0), ("wait_obj", "M00P-O09", 5), ("shot",),
    ("wait", 14), ("move", 1700, -1000, 0), ("move", 1700, -1330, 0), ("note", "aboard the tram"), ("wait", 10), ("shot",),
]
st = {"i": 0, "t0": 0.0, "goal": None, "last": None, "stall": 0.0, "h": None, "n": 0, "phase": None}
log("start; active:", active())

def finish():
    log("DONE; active:", active())
    unreal.unregister_slate_post_tick_callback(st["h"])

def tick(dt):
    try:
        if st["i"] >= len(STEPS):
            finish(); return
        s = STEPS[st["i"]]
        k = s[0]
        loc = PAWN.get_actor_location()
        if k == "move":
            g = V(s[1], s[2], loc.z)
            if st["phase"] != st["i"]:
                st["phase"] = st["i"]; st["t0"] = 0.0; st["stall"] = 0.0; st["last"] = loc
                path = unreal.NavigationSystemV1.find_path_to_location_synchronously(W, loc, V(s[1], s[2], s[3]))
                pts = list(path.get_editor_property("path_points")) if path else []
                st["pts"] = pts[1:] if len(pts) > 1 else [V(s[1], s[2], s[3])]
                if not pts:
                    log(f"no nav path to ({s[1]},{s[2]}) - walking straight")
            st["t0"] += dt
            # steer along the path with real movement input (collision, steps, doors all apply)
            while st["pts"] and unreal.Vector(st["pts"][0].x - loc.x, st["pts"][0].y - loc.y, 0).length() < 60 and len(st["pts"]) > 1:
                st["pts"].pop(0)
            tgt = st["pts"][0]
            dvec = unreal.Vector(tgt.x - loc.x, tgt.y - loc.y, 0)
            if dvec.length() > 1:
                face(tgt.x, tgt.y)
                PAWN.add_movement_input(dvec.normal(), 1.0, False)
            d = unreal.Vector(loc.x - g.x, loc.y - g.y, 0).length()
            moved = (loc - st["last"]).length()
            st["last"] = loc
            st["stall"] = st["stall"] + dt if moved < 1.0 else 0.0
            if d < 140:
                log(f"arrived ({s[1]},{s[2]}) in {st['t0']:.1f}s")
                st["i"] += 1
            elif st["stall"] > 6.0 or st["t0"] > 90:
                log(f"STUCK going to ({s[1]},{s[2]}) at ({loc.x:.0f},{loc.y:.0f},{loc.z:.0f}), {d:.0f} short -> teleporting on")
                PAWN.set_actor_location(V(s[1], s[2], s[3] + 110), False, True)
                st["i"] += 1
            return
        st["phase"] = None
        if k == "wait":
            st["t0"] = st.get("tw", 0.0) + dt; st["tw"] = st["t0"]
            if st["tw"] < s[1]:
                return
            st["tw"] = 0.0
        elif k == "tp":
            PAWN.set_actor_location(V(s[1], s[2], s[3]), False, True)
            PC.set_control_rotation(unreal.Rotator(roll=0, pitch=0, yaw=s[4]))
        elif k == "event":
            o = obj_sys(); log("event", s[1], o.send_event(tag(s[1])) if o else "no objectives")
        elif k == "note":
            log("note:", s[1], f"@({loc.x:.0f},{loc.y:.0f},{loc.z:.0f})", "active:", active())
        elif k == "gate":
            log("gate", s[1], "open" if gate_state(s[1]) is True else ("closed" if gate_state(s[1]) is False else gate_state(s[1])))
        elif k == "use":
            a = find(s[1])
            if not a:
                log("use: missing", s[1])
            else:
                l2 = a.get_actor_location()
                dd = (l2 - loc).length()
                ok = a.can_interact(PAWN)
                face(l2.x, l2.y)
                if ok:
                    a.interact(PAWN)
                log(f"use {s[1]}: dist {dd:.0f}, can_interact={ok} -> active now {active()}")
        elif k == "wait_obj":
            st["tw"] = st.get("tw", 0.0) + dt
            if s[1] not in active() and st["tw"] < s[2]:
                return
            log("objective", s[1], "active" if s[1] in active() else "NOT active", "after", round(st["tw"], 1), "s")
            st["tw"] = 0.0
        elif k == "sweep_slide":
            sh = find("Shutter_Slide")
            if sh:
                o, e = sh.get_actor_bounds(False)
                floor = 0.0
                hit = unreal.SystemLibrary.capsule_trace_single(W, V(o.x + 250, -615, floor + 60), V(o.x - 250, -615, floor + 60), 34, 58,
                                                                unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [PAWN], unreal.DrawDebugTrace.NONE, True)
                log(f"slide check: shutter bottom z {o.z - e.z:.0f}; crouched capsule passes = {not hit}")
                hit2 = unreal.SystemLibrary.capsule_trace_single(W, V(o.x + 250, -615, floor + 98), V(o.x - 250, -615, floor + 98), 34, 96,
                                                                 unreal.TraceTypeQuery.TRACE_TYPE_QUERY1, False, [PAWN], unreal.DrawDebugTrace.NONE, True)
                log(f"slide check: standing capsule blocked = {bool(hit2)}")
        elif k == "shot":
            st["n"] += 1; shot(st["n"])
        st["i"] += 1
    except Exception as e:
        log("ERROR", e); finish()

st["h"] = unreal.register_slate_post_tick_callback(tick)
