"""Gamepad ADS look scale on BP_NVPlayerCharacter (matches the C++ default). Report: Saved/NV_aim_tune.txt"""
import unreal
bp = unreal.load_asset("/Game/NeonVeil/Core/BP_NVPlayerCharacter")
cdo = unreal.get_default_object(bp.generated_class())
cdo.set_editor_property("gamepad_ads_scale", 0.5)
unreal.EditorAssetLibrary.save_loaded_asset(bp, only_if_is_dirty=False)
open(unreal.Paths.project_saved_dir() + "NV_aim_tune.txt", "w").write("gamepad_ads_scale %.2f" % cdo.get_editor_property("gamepad_ads_scale"))
