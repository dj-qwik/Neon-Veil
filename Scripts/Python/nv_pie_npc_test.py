"""PIE experiments on one NPC. args: label mode   mode: hidebody | showbody | origmat | listcomps"""
import sys, unreal
lab, mode = sys.argv[2], sys.argv[3]
pie = unreal.EditorLevelLibrary.get_pie_worlds(False)
w = pie[0]
O = []
for a in unreal.GameplayStatics.get_all_actors_of_class(w, unreal.Character):
    if a.get_actor_label() != lab: continue
    comps = a.get_components_by_class(unreal.PrimitiveComponent)
    for c in comps:
        mats = []
        try: mats = [m.get_name() if m else None for m in c.get_materials()]
        except Exception: pass
        mesh = ""
        if isinstance(c, unreal.SkinnedMeshComponent):
            try: mesh = c.get_skinned_asset().get_name()
            except Exception: pass
        O.append(f"{c.get_name()} [{type(c).__name__}] vis {c.is_visible()} mesh {mesh} mats {mats}")
    body = a.get_editor_property("mesh")
    if mode == "hidebody": body.set_visibility(False, False)
    if mode == "showbody": body.set_visibility(True, False)
    if mode == "origmat":
        n = body.get_skinned_asset().get_path_name().rsplit("/Body/", 1)[0]
        mi = unreal.load_asset(n + "/Body/Materials/MI_Body_Baked_VT")
        body.set_material(0, mi); O.append(f"set {mi}")
open(unreal.Paths.project_saved_dir() + "NV_pie_npc_test.txt", "w").write("\n".join(O))
