"""Download trailer renders (signed ElevenLabs URLs) to Saved/Trailer. Reads the newest Scripts/Trailer/dl_*.json {name: url}."""
import os, glob, json, urllib.request, unreal
P = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
src = max(glob.glob(os.path.join(P, "Scripts", "Trailer", "dl_*.json")), key=os.path.getmtime)
out_dir = os.path.join(P, "Saved", "Trailer"); os.makedirs(out_dir, exist_ok=True)
log = [f"src {os.path.basename(src)}"]
for name, url in json.load(open(src)).items():
    dst = os.path.join(out_dir, name)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=120) as r, open(dst, "wb") as f:
            f.write(r.read())
        log.append(f"OK {name} {os.path.getsize(dst)}")
    except Exception as e:
        log.append(f"FAIL {name} {e}")
open(os.path.join(out_dir, "_dl_log.txt"), "w").write("\n".join(log))
unreal.log("[nv_trailer_dl] " + " | ".join(log))
