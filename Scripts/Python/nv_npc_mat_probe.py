import sys, unreal
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
lab = sys.argv[2] if len(sys.argv) > 2 else "NPC_St_E1"
O = []
def desc(m, ind="  "):
    if not m: O.append(ind + "None"); return
    O.append(f"{ind}{m.get_path_name()} [{type(m).__name__}]")
    if isinstance(m, unreal.MaterialInstance):
        for p in m.get_editor_property("texture_parameter_values") or []:
            t = p.get_editor_property("parameter_value")
            info = ""
            if t:
                try: info = f"{t.blueprint_get_size_x()}x{t.blueprint_get_size_y()} vt={t.get_editor_property('virtual_texture_streaming')} grp={t.get_editor_property('lod_group')}"
                except Exception as e: info = str(e)[:40]
            O.append(f"{ind}  tex {p.get_editor_property('parameter_info').get_editor_property('name')} = {t.get_path_name() if t else None} {info}")
        for p in (m.get_editor_property("scalar_parameter_values") or [])[:30]:
            O.append(f"{ind}  s {p.get_editor_property('parameter_info').get_editor_property('name')} = {p.get_editor_property('parameter_value')}")
        for p in (m.get_editor_property("vector_parameter_values") or [])[:20]:
            O.append(f"{ind}  v {p.get_editor_property('parameter_info').get_editor_property('name')} = {p.get_editor_property('parameter_value')}")
        par = m.get_editor_property("parent")
        if par: desc(par, ind + "  ")
    else:
        try: O.append(f"{ind}  blend {m.get_editor_property('blend_mode')} usage_skel {m.get_editor_property('used_with_skeletal_mesh')}")
        except Exception: pass
for a in EAS.get_all_level_actors():
    if a.get_actor_label() != lab: continue
    O.append(f"garments {[g.get_name() for g in a.get_editor_property('garments')]}")
    O.append(f"garment_materials {[m.get_name() if m else None for m in a.get_editor_property('garment_materials')]}")
    for g in a.get_editor_property("garments"):
        O.append(f"GARMENT {g.get_path_name()}")
        try:
            for i, sm in enumerate(g.get_editor_property("materials")):
                O.append(f" slot {i}"); desc(sm.get_editor_property("material_interface") if hasattr(sm, "get_editor_property") else sm)
        except Exception as e:
            O.append(f" materials err {e}")
    for m in a.get_editor_property("garment_materials"):
        O.append("ASSIGNED"); desc(m)
    O.append("BODY"); desc(a.get_editor_property("mesh").get_material(0))
open(unreal.Paths.project_saved_dir() + "NV_npc_mat_probe.txt", "w").write("\n".join(O))
