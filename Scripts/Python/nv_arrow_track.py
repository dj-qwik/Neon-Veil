"""PIE: log NavArrow component state every ~0.25 s for 6 s (Saved/NV_arrow_track.txt)."""
import unreal, time
w = unreal.EditorLevelLibrary.get_pie_worlds(False)[0]
a = unreal.GameplayStatics.get_all_actors_of_class(w, unreal.NVNavArrow)[0]
st = {"t0": time.time(), "last": 0.0, "out": []}
def tick(dt):
    t = time.time() - st["t0"]
    if t - st["last"] >= 0.25:
        st["last"] = t
        try:
            c = a.get_components_by_class(unreal.StaticMeshComponent)[1]
            o, e, r = unreal.SystemLibrary.get_component_bounds(c)
            wl = c.get_world_location(); ws = c.get_world_scale()
            st["out"].append(f"{t:5.2f} {c.get_name()} wl ({wl.x:.0f},{wl.y:.0f},{wl.z:.1f}) ws ({ws.x:.2f},{ws.y:.2f},{ws.z:.2f}) b o({o.x:.0f},{o.y:.0f},{o.z:.0f}) e({e.x:.0f},{e.y:.0f},{e.z:.1f}) vis {c.is_visible()} hig {c.get_editor_property('hidden_in_game')} rr {c.was_recently_rendered(0.1)} mat {c.get_material(0).get_name()}")
        except Exception as ex:
            st["out"].append(str(ex))
    if t > 6:
        unreal.unregister_slate_post_tick_callback(st["h"])
        open(unreal.Paths.project_saved_dir() + "NV_arrow_track.txt", "w").write("\n".join(st["out"]))
st["h"] = unreal.register_slate_post_tick_callback(tick)
