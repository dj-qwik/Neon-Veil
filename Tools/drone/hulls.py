"""Collision proxy: one convex hull per part (<=64 farthest-point samples), lower lens excluded."""
import numpy as np
from scipy.spatial import ConvexHull
d=np.load("mesh.npz");V=d["V"]
c=np.load("comps.npz");ext=(c["mx"]-c["mn"]).max(1);lab=c["lab"]
CORE=[67,105,106,107,108,176,180,181,185]
outV=[];outF=[];off=0
for k in range(len(ext)):
    if ext[k]<1.0 or k in CORE: continue
    P=V[lab==k]
    try: hp=P[ConvexHull(P).vertices]
    except Exception: continue
    if len(hp)>64:
        sel=[0]; dist=np.linalg.norm(hp-hp[0],axis=1)
        for _ in range(63):
            i=int(dist.argmax()); sel.append(i); dist=np.minimum(dist,np.linalg.norm(hp-hp[i],axis=1))
        hp=hp[sel]
    try: h2=ConvexHull(hp)
    except Exception: continue
    idx=np.unique(h2.simplices); rm=np.full(len(hp),-1); rm[idx]=np.arange(len(idx)); hp=hp[idx]; hs=rm[h2.simplices]
    cen=hp.mean(0); a,b,cc=hp[hs[:,0]],hp[hs[:,1]],hp[hs[:,2]]
    flip=((a-cen)*np.cross(b-a,cc-a)).sum(1)<0; hs[flip]=hs[flip][:,[0,2,1]]
    outV.append(hp);outF.append(hs+off);off+=len(hp)
V2=np.concatenate(outV);F2=np.concatenate(outF)
with open("SM_SimDrone_BodyCol.obj","w") as f:
    f.write("o SM_SimDrone_BodyCol\n")
    f.write("".join("v %.4f %.4f %.4f\n"%tuple(p) for p in V2))
    f.write("".join("f %d %d %d\n"%tuple(t+1) for t in F2))
