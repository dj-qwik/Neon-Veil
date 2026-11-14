"""PIE: report NPC body state (anim class, visibility, bone positions) for a few NPCs. Report: Saved/NV_npc_pose.txt"""
import unreal
ues = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
world = ues.get_game_world()
OUT = []
n = 0
for a in list(unreal.GameplayStatics.get_all_actors_of_class(world, unreal.NVPlayerCharacter)) + list(unreal.GameplayStatics.get_all_actors_of_class(world, unreal.NVGuardCharacter)):
    lab = a.get_actor_label()
    if not (lab.startswith("NPC_") or isinstance(a, unreal.NVPlayerCharacter)):
        continue
    m = a.get_editor_property("mesh")
    ai = m.get_anim_instance()
    loc = a.get_actor_location()
    def b(name):
        try:
            v = m.get_socket_location(name)
            return f"({v.x - loc.x:.0f},{v.y - loc.y:.0f},{v.z - loc.z:.0f})"
        except Exception as e:
            return "?"
    o, e = a.get_actor_bounds(False)
    try:
        mb = m.get_editor_property("bounds")
    except Exception:
        mb = None
    OUT.append(f"   mesh bounds: {(mb.origin.x - loc.x, mb.origin.y - loc.y, mb.origin.z - loc.z, mb.box_extent.x, mb.box_extent.y, mb.box_extent.z) if mb else None}")
    comps = a.get_components_by_class(unreal.PrimitiveComponent)
    for c in comps:
        try:
            co, ce, cr = unreal.SystemLibrary.get_component_bounds(c)
            if abs(co.x - loc.x) + abs(co.y - loc.y) > 60:
                OUT.append(f"   far comp {c.get_name()} {c.get_class().get_name()} off=({co.x - loc.x:.0f},{co.y - loc.y:.0f},{co.z - loc.z:.0f}) ext=({ce.x:.0f},{ce.y:.0f},{ce.z:.0f}) vis={c.is_visible()}")
        except Exception as ex:
            pass
    try:
        bb = m.get_editor_property("bounds_scale")
    except Exception:
        bb = "?"
    rl = m.get_editor_property("relative_location")
    OUT.append(f"   bounds origin-actor=({o.x - loc.x:.0f},{o.y - loc.y:.0f},{o.z - loc.z:.0f}) extent=({e.x:.0f},{e.y:.0f},{e.z:.0f}) bscale={bb} meshrel={rl} recent={m.was_recently_rendered(0.2)}")
    OUT.append(f"{lab}: anim={ai.get_class().get_name() if ai else None} vis={m.is_visible()} hidden={m.get_editor_property('hidden_in_game')} mesh={m.get_skeletal_mesh_asset().get_name() if m.get_skeletal_mesh_asset() else None} speed={a.get_velocity().length():.0f} head={b('head')} pelvis={b('pelvis')} foot_l={b('foot_l')} foot_r={b('foot_r')} hand_r={b('hand_r')}")
    n += 1
    if n > 6:
        break
open(unreal.Paths.project_saved_dir() + "NV_npc_pose.txt", "w").write("\n".join(OUT) or "none")
