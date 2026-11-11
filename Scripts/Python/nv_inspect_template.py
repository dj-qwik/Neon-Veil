"""Dump the First Person template's character, input and anim setup to Saved/NV_inspect.txt.
Read-only: changes nothing in the project."""
import unreal

out = []
def w(*a):
    out.append(" ".join(str(x) for x in a))

def dump_props(obj, names):
    for n in names:
        try:
            w("   ", n, "=", obj.get_editor_property(n))
        except Exception as e:
            w("   ", n, "<err>", e)

bp_path = "/Game/FirstPerson/Blueprints/BP_FirstPersonCharacter"
bp = unreal.load_asset(bp_path)
w("== Blueprint", bp_path, "parent:", unreal.BlueprintEditorLibrary.get_generated_class(bp).get_super_class() if hasattr(unreal.BlueprintEditorLibrary, "get_generated_class") else "?")

# Components through the subobject data subsystem
sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
handles = sds.k2_gather_subobject_data_for_blueprint(bp)
for h in handles:
    data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h)
    obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_object(data)
    if obj is None:
        continue
    w("-- component", obj.get_name(), obj.get_class().get_name())
    if isinstance(obj, unreal.SkeletalMeshComponent):
        dump_props(obj, ["skeletal_mesh_asset", "anim_class", "animation_mode", "first_person_primitive_type",
                         "only_owner_see", "owner_no_see", "cast_shadow", "relative_location", "relative_rotation"])
        try:
            w("    attach parent socket:", obj.get_attach_socket_name())
        except Exception:
            pass
    elif isinstance(obj, unreal.CameraComponent):
        dump_props(obj, ["field_of_view", "enable_first_person_field_of_view", "first_person_field_of_view",
                         "enable_first_person_scale", "first_person_scale", "relative_location", "use_pawn_control_rotation"])
        try:
            w("    attach socket:", obj.get_attach_socket_name())
        except Exception:
            pass

# Class defaults (input actions etc.)
gen = unreal.load_object(None, bp_path + ".BP_FirstPersonCharacter_C")
cdo = unreal.get_default_object(gen)
for prop in ["jump_action", "move_action", "look_action", "mouse_look_action", "default_mapping_context", "first_person_mesh"]:
    try:
        w("cdo", prop, "=", cdo.get_editor_property(prop))
    except Exception as e:
        w("cdo", prop, "<none>")

# Input mapping contexts
for imc_path in ["/Game/Input/IMC_Default", "/Game/Input/IMC_MouseLook"]:
    imc = unreal.load_asset(imc_path)
    w("== IMC", imc_path)
    try:
        maps = imc.get_editor_property("mappings")
    except Exception:
        maps = imc.get_editor_property("default_key_mappings").get_editor_property("mappings")
    for m in maps:
        action = m.get_editor_property("action")
        key = m.get_editor_property("key")
        mods = [x.get_class().get_name() for x in m.get_editor_property("modifiers")]
        w("  ", action.get_name() if action else None, key.get_editor_property("key_name"), mods)

# Player controller BP: which contexts it adds
pc_bp = unreal.load_object(None, "/Game/FirstPerson/Blueprints/BP_FirstPersonPlayerController.BP_FirstPersonPlayerController_C")
pcdo = unreal.get_default_object(pc_bp)
for prop in ["default_mapping_contexts", "mobile_excluded_mapping_contexts"]:
    try:
        w("pc", prop, "=", pcdo.get_editor_property(prop))
    except Exception:
        w("pc", prop, "<none>")

# Anim assets available
ar = unreal.AssetRegistryHelpers.get_asset_registry()
for path in ["/Game/FirstPerson/Anims", "/Game/Characters/Mannequins/Anims/Pistol", "/Game/Characters/Mannequins/Anims/Rifle"]:
    assets = ar.get_assets_by_path(path, recursive=True)
    w("== assets in", path)
    for a in assets:
        w("  ", a.asset_class_path.asset_name, a.package_name)

proj = unreal.Paths.project_saved_dir()
with open(proj + "NV_inspect.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out))
unreal.log("NV inspect written: " + proj + "NV_inspect.txt")
