"""Sound classes for the options menu volumes: SC_NV_Music (music packs + NeonVeil/Audio/Music) and SC_NV_Voice
(NeonVeil/Audio/VO). Everything else stays on the engine default class (the "Effects" slider).
Re-runnable; run again after importing new music or VO. Report: Saved/NV_audio_classes.txt"""
import unreal
OUT = []
def log(*a): OUT.append(" ".join(str(x) for x in a))
AT = unreal.AssetToolsHelpers.get_asset_tools()
EAL = unreal.EditorAssetLibrary
MIX = "/Game/NeonVeil/Audio/Mix"

def klass(name):
    p = f"{MIX}/{name}"
    if EAL.does_asset_exist(p):
        return unreal.load_asset(p)
    a = AT.create_asset(name, MIX, unreal.SoundClass, unreal.SoundClassFactory())
    log("created", p)
    return a

MUSIC = klass("SC_NV_Music")
VOICE = klass("SC_NV_Voice")
for c in (MUSIC, VOICE):
    EAL.save_loaded_asset(c, only_if_is_dirty=False)

def assign(folders, cls):
    n = 0
    for f in folders:
        if not EAL.does_directory_exist(f):
            log("no folder", f)
            continue
        for p in EAL.list_assets(f, recursive=True, include_folder=False):
            d = EAL.find_asset_data(p)
            if str(d.asset_class_path.asset_name) not in ("SoundWave", "SoundCue"):
                continue
            a = unreal.load_asset(p)
            if a.get_editor_property("sound_class_object") != cls:
                a.set_editor_property("sound_class_object", cls)
                EAL.save_loaded_asset(a, only_if_is_dirty=False)
                n += 1
    return n

log("music assigned", assign(["/Game/Cyber_Punk_Music_v11", "/Game/Free_Cyber_Metal_Music_Pack", "/Game/NeonVeil/Audio/Music"], MUSIC))
log("voice assigned", assign(["/Game/NeonVeil/Audio/VO"], VOICE))
open(unreal.Paths.project_saved_dir() + "NV_audio_classes.txt", "w").write("\n".join(OUT))
