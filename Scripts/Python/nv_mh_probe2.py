"""Probe MetaHuman presets/content and build params. Report: Saved/NV_mh_probe2.txt"""
import unreal
out = []
AR = unreal.AssetRegistryHelpers.get_asset_registry()
for root in ("/MetaHumanCharacter", "/MetaHumanSDK", "/MetaHumanCoreTechLib", "/Game/MetaHumans"):
    f = unreal.ARFilter(package_paths=[root], recursive_paths=True)
    assets = AR.get_assets(f)
    by = {}
    for a in assets:
        by.setdefault(str(a.asset_class_path.asset_name), []).append(str(a.package_name))
    out.append(f"== {root}: {len(assets)} assets; classes: " + ", ".join(f"{k}:{len(v)}" for k, v in sorted(by.items(), key=lambda x: -len(x[1]))[:25]))
    for k in ("MetaHumanCharacter", "MetaHumanWardrobeItem", "MetaHumanCharacterPalette", "MetaHumanCollection"):
        for p in by.get(k, [])[:60]:
            out.append(f"   {k}: {p}")
for n in ("MetaHumanCharacterEditorBuildParameters", "MetaHumanCharacterEditorSettings", "MetaHumanCharacterTemplateType", "MetaHumanQualityLevel", "MetaHumanDefaultPipelineType", "MetaHumanCharacterAutoRiggingRequestParams", "MetaHumanCharacterTextureRequestParams", "MetaHumanRigType"):
    c = getattr(unreal, n, None)
    if c:
        out.append(f"--- {n}: " + ", ".join(m for m in dir(c) if not m.startswith("_") and m not in dir(unreal.StructBase) and m not in dir(unreal.Object)))
S = unreal.get_editor_subsystem(unreal.MetaHumanCharacterEditorSubsystem)
for fn in ("try_add_object_to_edit", "build_meta_human", "request_auto_rigging", "request_texture_sources", "import_from_template", "spawn_meta_human_actor", "can_build_meta_human"):
    out.append(f"*** {fn}: {getattr(S, fn).__doc__}")
with open(unreal.Paths.project_saved_dir() + "NV_mh_probe2.txt", "w", encoding="utf-8") as fh:
    fh.write("\n".join(out))
