"""Download ElevenLabs takes listed in Scripts/VO/<set>_takes.json ({line_id: url}) to Saved/VO_raw/<line_id>.mp3.
Runs on the user's PC (the signed URLs expire after a few hours). arg: set name, default M00."""
import unreal, json, os, sys, urllib.request
SET = sys.argv[-1] if len(sys.argv) > 1 and not sys.argv[-1].startswith("nv_") else "M00"
proj = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
takes = json.load(open(os.path.join(proj, "Scripts", "VO", SET + "_takes.json")))
dst = os.path.join(proj, "Saved", "VO_raw"); os.makedirs(dst, exist_ok=True)
log = []
for lid, url in takes.items():
    p = os.path.join(dst, lid + ".mp3")
    try:
        urllib.request.urlretrieve(url, p)
        log.append("%s %d bytes" % (lid, os.path.getsize(p)))
    except Exception as e:
        log.append("%s FAILED %s" % (lid, e))
open(unreal.Paths.project_saved_dir() + "NV_vo_get.txt", "w").write("\n".join(log))
