"""PIE smoke test for M01 Black Protocol (L_M00_GlassCrown). Start PIE, then run this. It fast-forwards M00 with
cheats, lets the betrayal play, kills the lockdown drones, walks the objective chain by teleporting through each
area, and grabs HighResShots at the beats. The player is made invulnerable (NVGod) so enemy fire can't end the run.
Report: Saved/NV_pie_m01.txt (plus the LogNeonVeil lines in the editor log); shots Saved/NV_shots/m01_*.png
The whole chain runs in ~90 s."""
import os
import unreal

w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
pc = unreal.GameplayStatics.get_player_controller(w, 0)
SHOTS = os.path.join(unreal.Paths.project_saved_dir(), "NV_shots")
out = []

def cmd(c):
    unreal.SystemLibrary.execute_console_command(w, c, pc)
    out.append("  > " + c)

def pawn():
    return pc.get_controlled_pawn()

def actor(label):
    for a in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.Actor):
        if a.get_actor_label() == label:
            return a
    return None

def tp(x, y, z, yaw):
    p = pawn()
    p.teleport(unreal.Vector(x, y, z), unreal.Rotator(roll=0, pitch=0, yaw=yaw))
    pc.set_control_rotation(unreal.Rotator(roll=0, pitch=-5, yaw=yaw))

SHOTS_ON = False   # HighResShot pushed an 8 GB GPU over its video-memory budget (device removed); off by default
def shot(name):
    if not SHOTS_ON:
        return
    cmd('HighResShot 1280x720 filename="%s"' % os.path.join(SHOTS, "m01_" + name + ".png").replace("\\", "/"))

def look_at(label, pitch=None):
    a = actor(label)
    if a:
        cam = pc.player_camera_manager.get_camera_location()
        r = unreal.MathLibrary.find_look_at_rotation(cam, a.get_actor_location())
        if pitch is not None:
            r.pitch = pitch
        pc.set_control_rotation(r)

def kill(cls):
    n = 0
    for a in unreal.GameplayStatics.get_all_actors_of_class(w, cls):
        h = a.get_component_by_class(unreal.NVHealthComponent)
        if h and not h.is_dead():
            t = unreal.GameplayTag()
            t.import_text('(TagName="NV.Damage.Ballistic")')
            h.apply_damage(9999.0, pawn(), t, False)
            n += 1
    out.append("  killed %d %s" % (n, cls.__name__))

def note(s):
    p = pawn()
    l = p.get_actor_location() if p else None
    h = p.get_component_by_class(unreal.NVHealthComponent) if p else None
    out.append("%6.1f %s | player %s hp %s" % (st["t"], s, "(%d,%d,%d)" % (l.x, l.y, l.z) if l else "-", "%.0f" % h.get_health() if h else "-"))

def drone_state():
    for d in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.NVSecurityDrone):
        l = d.get_actor_location()
        out.append("    drone %s destroyed=%s at (%d,%d,%d)" % (d.get_actor_label(), d.is_destroyed(), l.x, l.y, l.z))

def cab_state():
    c = actor("C_Cab_Floor")
    if c:
        h = actor("C_Cab_EastHatch")
        out.append("    cab at z %d, hatch collision=%s" % (c.get_actor_location().z, h.get_actor_enable_collision() if h else "-"))

# Two passes, like a real session: the first run (player still on the prologue tram) completes M00-O01..O03 and
# reloads the gallery checkpoint, so the tram/city section is no longer resident; run the script again after the
# reload for the M01 chain.
PHASE1 = pawn().get_actor_location().x < 10000
PRE = [
    (1.0, lambda: (cmd("NVComplete M00-O01"), cmd("NVComplete M00-O02"), cmd("NVComplete M00-O03"), note("M00 fast-forward"))),
    (2.0, lambda: (cmd("NVLoad"), note("reloading the gallery checkpoint; run this script again once it is up"))),
]
STEPS = [
    (1.0, lambda: (cmd("r.ScreenPercentage 70"), cmd("NVGod 1"), note("start"))),
    (2.5, lambda: (tp(15300, 0, 100, 0), note("in the antechamber"))),
    (3.5, lambda: (cmd("NVComplete M00-O04"), note("handshake: M00 complete"))),
    (7.5, lambda: (look_at("E_DarkGlass", 5), shot("a_lockdown"), note("lockdown"))),
    (11.0, lambda: (look_at("A_Drone_0"), shot("a_drone"), drone_state(), note("drones deployed?"))),
    (14.0, lambda: (cmd("NVEnemies"), note("enemies"))),
    (15.0, lambda: (kill(unreal.NVSecurityDrone), note("drones killed"))),
    (17.5, lambda: (look_at("A_EmergencyDoor", 0), shot("a_emergency_open"), note("emergency door"))),
    (20.5, lambda: (cmd("NVEnemies"), look_at("Door_D_to_E", 0), shot("a_troopers"), note("designation + troopers"))),
    (23.0, lambda: (kill(unreal.NVGuardCharacter), note("troopers killed (all guards)"))),
    (24.0, lambda: (tp(15600, 900, 100, 90), note("through the emergency door"))),
    (26.0, lambda: (tp(15600, 1300, 100, 90), shot("b_artery_turret"), cmd("NVEnemies"), note("artery, turret should be hostile"))),
    (28.0, lambda: (tp(16050, 2600, 100, 0), note("alcove"))),
    (29.0, lambda: (cmd("NVEvent NV.Event.M01.TurretRerouted"), note("reroute event"))),
    (30.5, lambda: (cmd("NVEnemies"), tp(15600, 4800, 100, 90), shot("b_turret_rerouted"), note("turret rerouted?"))),
    (32.0, lambda: (tp(15500, 6900, 100, 90), note("into the lift cab"))),
    (36.0, lambda: (cab_state(), note("cab cruising"))),
    (40.0, lambda: (cab_state(), shot("c_lift_falling"), note("cab"))),
    (46.0, lambda: (cab_state(), look_at("C_Ledge_P1", 0), shot("c_lift_braked"), note("cab braked, hatch open?"))),
    (48.0, lambda: (tp(16150, 6860, -2700, 90), note("on ledge P1"))),
    (49.0, lambda: (tp(16150, 7000, -4400, 0), note("shaft bottom"))),
    (51.0, lambda: (tp(16550, 7000, -4400, 0), note("into the surgical bay"))),
    (56.0, lambda: (shot("d_reclamation"), note("reclamation running"))),
    (70.0, lambda: (shot("d_after"), note("reclamation over"))),
    (71.0, lambda: (tp(17150, 7000, -4400, 0), note("at the tag"))),
    (71.5, lambda: look_at("D_AgencyTag")),   # a frame after the teleport, so the camera has moved
    (72.5, lambda: (cmd("NVUse"), note("take tag"))),
    (74.0, lambda: (tp(19200, 7000, -4400, 0), shot("e_conduit"), cmd("NVEnemies"), note("conduit"))),
    (76.0, lambda: (cmd("NVGod 0"), cmd("NVHurtSelf 999"), note("killed on purpose: checkpoint reload test (run the script again after the reload)"))),
]
# pass 3, after the death reload at CP_M01_Suite: the world must come back in the post-reclamation state (QA-03)
POST = [
    (1.0, lambda: (cmd("NVGod 1"), cmd("NVEnemies"), cab_state(), note("restored at the suite checkpoint"))),
    (1.5, lambda: (ability_state(), note("abilities after reload"))),
    (3.0, lambda: (tp(28200, 7000, -4400, 0), note("spillway top"))),
    (5.0, lambda: (tp(30900, 7000, -4880, 0), note("end trigger"))),
    (12.0, lambda: note("end card should be up")),
]
def ability_state():
    p = pawn()
    ab = p.get_component_by_class(unreal.NVAbilityComponent)
    for n in ("NV.Ability.OpticalDisruption", "NV.Ability.KineticShield", "NV.Ability.DroneUplink"):
        t = unreal.GameplayTag()
        t.import_text('(TagName="%s")' % n)
        out.append("    %s disabled=%s" % (n, ab.is_ability_disabled(t)))

loc0 = pawn().get_actor_location()
if PHASE1:
    STEPS = PRE
elif loc0.z < -4000:
    STEPS = POST
st = {"t": 0.0, "i": 0, "h": None}

def tick(dt):
    st["t"] += dt
    while st["i"] < len(STEPS) and st["t"] >= STEPS[st["i"]][0]:
        try:
            STEPS[st["i"]][1]()
        except Exception as e:
            out.append("  step %d failed: %s" % (st["i"], e))
        st["i"] += 1
    if st["i"] >= len(STEPS) or st["t"] - st.get("last", 0) > 4.0:
        st["last"] = st["t"]
        open(os.path.join(unreal.Paths.project_saved_dir(), "NV_pie_m01.txt"), "w").write("\n".join(out))
        if st["i"] >= len(STEPS):
            unreal.unregister_slate_post_tick_callback(st["h"])

st["h"] = unreal.register_slate_post_tick_callback(tick)
