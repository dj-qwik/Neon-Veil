"""Import RawAssets/VO/<set>/*.wav as SoundWaves (/Game/NeonVeil/Audio/VO/<set>) and hook each to its subtitle line
(matched by text via Scripts/VO/<set>_lines.json). Subtitle duration is raised to fit the audio + 0.35 s.
Report: Saved/NV_vo_import.txt"""
import unreal, json, os, sys
SET = sys.argv[1] if len(sys.argv) > 1 else "M00"
proj = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
lines = json.load(open(os.path.join(proj, "Scripts", "VO", SET + "_lines.json")))
src = os.path.join(proj, "RawAssets", "VO", SET)
DST = "/Game/NeonVeil/Audio/VO/" + SET
AT = unreal.AssetToolsHelpers.get_asset_tools()
log = []
by_text = {}
for l in lines:
    wav = os.path.join(src, l["id"] + ".wav")
    if not os.path.exists(wav):
        log.append("missing wav %s" % l["id"]); continue
    t = unreal.AssetImportTask()
    t.filename = wav; t.destination_path = DST; t.destination_name = "VO_" + l["id"]
    t.automated = True; t.replace_existing = True; t.save = True
    AT.import_asset_tasks([t])
    s = unreal.load_asset(DST + "/VO_" + l["id"])
    if s:
        by_text[l["text"].strip()] = s
        log.append("imported %s %.2fs" % (l["id"], s.get_editor_property("duration")))

def fix(arr):
    n = 0
    for ln in arr:
        s = by_text.get(str(ln.get_editor_property("text")).strip())
        if s:
            ln.set_editor_property("voice", s)
            ln.set_editor_property("duration", max(ln.get_editor_property("duration"), s.get_editor_property("duration") + 0.35))
            n += 1
    return n

total = 0
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for a in EAS.get_all_level_actors():
    for prop in ("lines_on_complete", "lines", "lines_on_use"):
        try:
            arr = a.get_editor_property(prop)
        except Exception:
            continue
        if arr and isinstance(arr[0], unreal.NVSubtitleLine):
            k = fix(arr)
            if k:
                a.set_editor_property(prop, arr); total += k; log.append("%s.%s: %d" % (a.get_actor_label(), prop, k))
    try:
        steps = a.get_editor_property("steps")
    except Exception:
        steps = None
    if steps:
        k = 0
        for st in steps:
            for sp in ("lines", "fail_lines"):
                arr = st.get_editor_property(sp)
                kk = fix(arr)
                if kk:
                    st.set_editor_property(sp, arr); k += kk
        if k:
            a.set_editor_property("steps", steps); total += k; log.append("%s.steps: %d" % (a.get_actor_label(), k))
log.append("lines voiced: %d of %d" % (total, len(lines)))
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
open(unreal.Paths.project_saved_dir() + "NV_vo_import.txt", "w").write("\n".join(log))
