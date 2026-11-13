import numpy as np, subprocess, sys, os, json
T="/mnt/user-data/uploads/NeonVeil/Saved/Trailer"
out={}
for f in sys.argv[1:]:
    raw=subprocess.check_output(["ffmpeg","-v","error","-i",f"{T}/{f}","-vf","scale=96:54,fps=24,format=gray","-f","rawvideo","-"])
    a=np.frombuffer(raw,np.uint8).reshape(-1,54,96).astype(np.float32)
    d=np.abs(np.diff(a,axis=0)).mean(axis=(1,2)); d=np.concatenate([[d[0]],d])
    out[f]=d.round(2).tolist()
    pk=np.argsort(-d)[:4]
    print(f, len(d), "mean %.1f"%d.mean(), "peaks", [(round(p/24,2), round(float(d[p]),1)) for p in sorted(pk)])
json.dump(out,open(f"/home/claude/trailer/motion/{os.getpid()}.json","w"))
