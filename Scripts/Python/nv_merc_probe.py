"""Probe the Waveforce mercenary pack: skeleton bones vs Manny, BP_MER_ME components, material params."""
import unreal

out = []
P = "/Game/Mercenary_Male_WaveforceStudio/"
ELL = unreal.EditorLevelLibrary
world = unreal.EditorLevelLibrary.get_editor_world()


def bones(mesh_path):
    m = unreal.load_asset(mesh_path)
    if not m:
        return None, None
    a = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.SkeletalMeshActor, unreal.Vector(0, 0, -50000))
    c = a.skeletal_mesh_component
    c.set_skinned_asset_and_update(m) if hasattr(c, "set_skinned_asset_and_update") else c.set_skeletal_mesh(m)
    names = [str(c.get_bone_name(i)) for i in range(c.get_num_bones())]
    a.destroy_actor()
    return m, names


manny, mb = bones("/Game/Characters/Mannequins/Meshes/SKM_Manny_Simple")
out.append("Manny bones %d skel %s" % (len(mb), manny.get_editor_property("skeleton").get_path_name()))
for part in ["Mesh/Modular/SK_MER_ME_Body", "Mesh/Modular/SK_MER_ME_Outer01", "Mesh/Modular/SK_MER_ME_Pant01",
             "Mesh/Modular/SK_MER_ME_Glass01", "Mesh/Modular/SK_MER_ME_Hair01", "Mesh/Modular/SK_MER_ME_ACC01",
             "Mesh/Modular/SK_MER_ME_Common", "Mesh/Modular/SK_MER_ME_Gloves01", "Mesh/Modular/SK_MER_ME_Shoes01",
             "Mesh/SK_MER_ME_Outfit01"]:
    m, b = bones(P + part)
    if not m:
        out.append("%s MISSING" % part)
        continue
    missing = [x for x in b if x not in mb]
    out.append("%s bones %d skel %s notInManny %d %s" % (part, len(b), m.get_editor_property("skeleton").get_name(),
                                                          len(missing), missing[:12]))
    for i, mat in enumerate(m.get_editor_property("materials")):
        mi = mat.get_editor_property("material_interface")
        out.append("   mat%d %s" % (i, mi.get_path_name() if mi else None))

# Material params of the instances
mel = unreal.MaterialEditingLibrary
for mi_name in ["MI_MER_ME_Outer01", "MI_MER_ME_Pant01", "MI_MER_ME_Body", "MI_MER_ME_Common", "MI_MER_ME_ACC01",
                "MI_MER_ME_Glass01", "MI_MER_ME_Gloves01", "MI_MER_ME_Shoes01", "MI_MER_ME_Head01", "MI_MER_ME_Hair01"]:
    mi = unreal.load_asset(P + "Materials/Materials_Instance/" + mi_name)
    if not mi:
        out.append(mi_name + " missing")
        continue
    vs = [str(n) for n in mel.get_vector_parameter_names(mi)]
    ss = [str(n) for n in mel.get_scalar_parameter_names(mi)]
    ts = [str(n) for n in mel.get_texture_parameter_names(mi)]
    out.append("%s parent %s" % (mi_name, mi.get_editor_property("parent").get_name()))
    out.append("   V " + ", ".join("%s=%s" % (v, mel.get_material_instance_vector_parameter_value(mi, v)) for v in vs))
    out.append("   S " + ", ".join(ss))
    out.append("   T " + ", ".join(ts))

# BP components
bp = unreal.load_asset(P + "BluePrint/BP_MER_ME")
try:
    sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    handles = sds.k2_gather_subobject_data_for_blueprint(bp)
    for h in handles:
        d = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h)
        o = unreal.SubobjectDataBlueprintFunctionLibrary.get_object(d)
        line = "  comp %s %s" % (o.get_name() if o else None, o.get_class().get_name() if o else "")
        if isinstance(o, unreal.SkinnedMeshComponent):
            sa = o.get_editor_property("skinned_asset") if hasattr(o, "get_editor_property") else None
            line += " asset=%s" % (sa.get_name() if sa else None)
            try:
                line += " anim=%s" % o.get_editor_property("anim_class")
            except Exception:
                pass
            try:
                line += " hidden=%s visible=%s" % (o.get_editor_property("hidden_in_game"), o.get_editor_property("visible"))
            except Exception:
                pass
        out.append(line)
except Exception as e:
    out.append("BP comps failed: %r" % e)

for a in ["Animation/MER_ABP_Manny", "Animation/ABP_MER_PostProcess", "Rig/RTG_ME_MER_Manny"]:
    o = unreal.load_asset(P + a)
    s = ""
    try:
        s = o.get_editor_property("target_skeleton").get_path_name()
    except Exception:
        pass
    out.append("%s %s %s" % (a, o.get_class().get_name() if o else None, s))

open(unreal.Paths.project_saved_dir() + "NV_nv_merc_probe.txt", "w").write("\n".join(out))
