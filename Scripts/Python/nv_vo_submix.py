"""Voice bus: every SoundWave under /Game/NeonVeil/Audio/VO plays through SMX_NV_Voice, a submix with a limiter, so the
HUD's VoiceVolume boost (default 2.2x) makes lines louder without clipping. Music / SFX are untouched.
Report: Saved/NV_vo_submix.txt"""
import unreal
OUT = []
EAL = unreal.EditorAssetLibrary
AT = unreal.AssetToolsHelpers.get_asset_tools()
MIX = "/Game/NeonVeil/Audio/Mix"

def get_or_make(name, cls, factory):
    path = f"{MIX}/{name}"
    if EAL.does_asset_exist(path):
        return unreal.load_asset(path)
    return AT.create_asset(name, MIX, cls, factory)

try:
    lim = get_or_make("DP_NV_VoiceLimiter", unreal.SubmixEffectDynamicsProcessorPreset, None)   # AssetTools finds the factory
    st = lim.get_editor_property("settings")
    st.set_editor_property("dynamics_processor_type", unreal.SubmixEffectDynamicsProcessorType.LIMITER)
    st.set_editor_property("threshold_db", -1.5)
    st.set_editor_property("attack_time_msec", 1.0)
    st.set_editor_property("release_time_msec", 120.0)
    st.set_editor_property("look_ahead_msec", 3.0)
    lim.set_editor_property("settings", st)
    EAL.save_loaded_asset(lim, only_if_is_dirty=False)
    OUT.append("limiter %s" % lim.get_path_name())

    mix = get_or_make("SMX_NV_Voice", unreal.SoundSubmix, unreal.SoundSubmixFactory())
    mix.set_editor_property("submix_effect_chain", [lim])
    EAL.save_loaded_asset(mix, only_if_is_dirty=False)
    OUT.append("submix %s" % mix.get_path_name())

    n = 0
    for p in EAL.list_assets("/Game/NeonVeil/Audio/VO", recursive=True, include_folder=False):
        a = unreal.load_asset(p)
        if isinstance(a, unreal.SoundWave):
            a.set_editor_property("sound_submix_object", mix)
            EAL.save_loaded_asset(a, only_if_is_dirty=False)
            n += 1
    OUT.append("voice waves routed: %d" % n)
except Exception:
    import traceback
    OUT.append(traceback.format_exc())
open(unreal.Paths.project_saved_dir() + "NV_vo_submix.txt", "w").write("\n".join(OUT))
