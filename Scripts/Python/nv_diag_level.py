"""Read-only: dump lights, targets and the player BP viewmodel setup to Saved/NV_diag.txt."""
import unreal
out = []
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for a in EAS.get_all_level_actors():
    lbl = a.get_actor_label()
    if isinstance(a, unreal.Light):
        lc = a.get_component_by_class(unreal.LightComponent)
        out.append(f"LIGHT {lbl} {a.get_class().get_name()} int={lc.get_editor_property('intensity')} mob={lc.get_editor_property('mobility')} rot={a.get_actor_rotation()}")
    if lbl.startswith("NV_Target"):
        out.append(f"TARGET {lbl} loc={a.get_actor_location()} hidden={a.is_hidden_ed()}")
        for c in a.get_components_by_class(unreal.StaticMeshComponent):
            out.append(f"   {c.get_name()} mesh={c.static_mesh.get_name() if c.static_mesh else None} mat={c.get_material(0).get_name() if c.get_material(0) else None} rel={c.get_editor_property('relative_location')} scale={c.get_editor_property('relative_scale3d')} vis={c.is_visible()}")
cls = unreal.EditorAssetLibrary.load_blueprint_class("/Game/NeonVeil/Core/BP_NVPlayerCharacter")
cdo = unreal.get_default_object(cls)
for n in ["weapon_static_mesh", "viewmodel_root", "first_person_camera"]:
    c = cdo.get_editor_property(n)
    out.append(f"PLAYER {n} rel={c.get_editor_property('relative_location')} scale={c.get_editor_property('relative_scale3d')} fpt={c.get_editor_property('first_person_primitive_type') if hasattr(c,'first_person_primitive_type') else '-'}")
w = unreal.load_asset("/Game/NeonVeil/Data/Weapons/DA_Weapon_VX9")
out.append(f"VX9 scale={w.get_editor_property('viewmodel_scale')} hip={w.get_editor_property('viewmodel_hip_offset')}")
open(unreal.Paths.project_saved_dir() + "NV_diag.txt", "w").write("\n".join(out))
