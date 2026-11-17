"""List the components of the ModularScifiInterior holo table / planet hologram (to reuse as the Glass Crown centerpiece)."""
import unreal
out = []
for path in ("/Game/ModularScifiInterior/Blueprints/BP_HoloTable",):
    cls = unreal.EditorAssetLibrary.load_blueprint_class(path)
    w = unreal.EditorLevelLibrary.get_editor_world()
    a = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).spawn_actor_from_class(cls, unreal.Vector(0, 0, -50000))
    for c in a.get_components_by_class(unreal.ActorComponent):
        extra = ""
        if isinstance(c, unreal.StaticMeshComponent):
            sm = c.get_editor_property("static_mesh")
            extra = " mesh=%s mats=%s rel=%s" % (sm.get_name() if sm else None, [m.get_name() if m else None for m in c.get_materials()], c.get_relative_transform())
        if isinstance(c, unreal.RotatingMovementComponent):
            extra = " rate=%s" % c.get_editor_property("rotation_rate")
        out.append("%s [%s]%s" % (c.get_name(), c.get_class().get_name(), extra))
    b = a.get_actor_bounds(False)
    out.append("bounds %s %s" % (b[0], b[1]))
    a.destroy_actor()
for p in ("/Game/ModularScifiInterior/Meshes/Props/SM_Hologram_PlanetSystem", "/Game/ModularScifiInterior/Meshes/Props/SM_HoloTable"):
    sm = unreal.load_asset(p)
    bb = sm.get_bounding_box()
    out.append("%s bounds %s %s mats %s" % (p, bb.min, bb.max, [s.get_editor_property("material_interface").get_name() for s in sm.get_editor_property("static_materials")]))
open(unreal.Paths.project_saved_dir() + "NV_inspect_holotable.txt", "w").write("\n".join(out))
