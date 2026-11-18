"""PIE check for the Nov 18 combat fixes (start PIE, run nv_pie_m01.py once to reach the gallery, then run this).
Pass 1 (gallery): turns the nearest guard hostile, fires the player's own gun at him from 3 m and reports his health,
then kills the player and, once the checkpoint reload hands back control, checks full health and the 5 s respawn
protection (one run covers both).
Report: Saved/NV_pie_combatfix.txt"""
import os
import unreal

UES = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
w = UES.get_game_world()
pc = unreal.GameplayStatics.get_player_controller(w, 0)
SAVED = unreal.Paths.project_saved_dir()
REPORT = os.path.join(SAVED, "NV_pie_combatfix.txt")
out = []
st = {"t": 0.0, "i": 0, "h": None, "g": None, "fire": False, "lastshot": 0.0}

def cmd(c):
    unreal.SystemLibrary.execute_console_command(w, c, pc)

def pawn():
    return pc.get_controlled_pawn()

def health(a):
    return a.get_component_by_class(unreal.NVHealthComponent) if a else None

def note(s):
    h = health(pawn())
    out.append("%5.1f %s | player hp %s invuln %s" % (st["t"], s, "%.0f" % h.get_health() if h else "-", h.is_invulnerable() if h else "-"))

def aim():
    g = st["g"]
    if g:
        cam = pc.player_camera_manager.get_camera_location()
        tgt = g.get_actor_location() + unreal.Vector(0, 0, 30)
        pc.set_control_rotation(unreal.MathLibrary.find_look_at_rotation(cam, tgt))

def setup():
    cmd("NVGod 1")
    p = pawn()
    best, bd = None, 1e12
    for g in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.NVGuardCharacter):
        if "Director" in g.get_actor_label() or health(g).is_dead():
            continue
        d = (g.get_actor_location() - p.get_actor_location()).length()
        if d < bd:
            best, bd = g, d
    st["g"] = best
    if not best:
        out.append("no guard found")
        return
    best.set_hostile(True)
    loc = best.get_actor_location() + best.get_actor_forward_vector() * 300.0
    p.teleport(loc, unreal.Rotator(0, 0, 0))
    wc = p.get_component_by_class(unreal.NVWeaponComponent)
    if wc.is_holstered():
        wc.equip_slot(0)
    out.append("target %s (%s) hp %.0f at %.0f cm" % (best.get_actor_label(), best.get_name(), health(best).get_health(), bd))

def fire_on():
    st["fire"] = True

def fire_off():
    st["fire"] = False
    pawn().get_component_by_class(unreal.NVWeaponComponent).stop_fire()
    g = st["g"]
    if g:
        h = health(g)
        out.append("after the volley: %s hp %.0f dead=%s" % (g.get_actor_label(), h.get_health(), h.is_dead()))

def die():
    cmd("NVGod 0")
    cmd("NVHurtSelf 999")
    note("killed on purpose; waiting for the reload")
    st["wait_reload"] = w.get_name() + str(id(w))
    st["old_pawn"] = pawn().get_name() if pawn() else ""

def hurt(label):
    cmd("NVHurtSelf 10")
    note(label)

def done():
    pass

AFTER = [(0.0, lambda: note("restored")), (1.0, lambda: hurt("hurt 10 at 1 s (protected)")),
             (6.5, lambda: hurt("hurt 10 at 6.5 s (protection over)")), (7.0, done)]
STEPS = [(0.2, setup), (1.0, fire_on), (4.5, fire_off), (5.5, die)]

def tick(dt):
    global w, pc, STEPS
    st["t"] += dt
    if st.get("wait_reload"):
        # the death reload replaces the PIE world; pick the new one up as soon as the restored player has control
        nw = UES.get_game_world()
        npc = unreal.GameplayStatics.get_player_controller(nw, 0) if nw else None
        np = npc.get_controlled_pawn() if npc else None
        h = health(np)
        if not np or not h or h.is_dead() or nw.get_name() + str(id(nw)) == st["wait_reload"] and np.get_name() == st["old_pawn"]:
            return
        w, pc = nw, npc
        st["wait_reload"] = None
        out.append("-- after reload --")
        STEPS, st["i"], st["t"] = AFTER, 0, 0.0
    if st["fire"]:
        aim()
        if st["t"] - st["lastshot"] > 0.25:
            st["lastshot"] = st["t"]
            wc = pawn().get_component_by_class(unreal.NVWeaponComponent)
            wc.stop_fire()
            wc.start_fire()
    while st["i"] < len(STEPS) and st["t"] >= STEPS[st["i"]][0]:
        try:
            STEPS[st["i"]][1]()
        except Exception as e:
            out.append("step %d failed: %s" % (st["i"], e))
        st["i"] += 1
    if st["i"] >= len(STEPS):
        open(REPORT, "w").write("\n".join(out))
        if not st.get("wait_reload"):
            unreal.unregister_slate_post_tick_callback(st["h"])

st["h"] = unreal.register_slate_post_tick_callback(tick)
