import numpy as np, json
d=np.load("mesh.npz");V=d["V"];F=d["F"];VT=d["VT"];FT=d["FT"];fl=np.load("flab.npy")
cls=np.array(json.load(open("cls.json")))
for i in [118,119,120,121,122,123,112,114,116,113,115,117]: cls[i]=2
for i in [10,20,100,109]: cls[i]=4
CORE=[67,105,106,107,108,176,180,181,185]
names=["MI_Drone_WhitePaint","MI_Drone_OrangePaint","MI_Drone_DarkMetal","MI_Drone_GlowCyan","MI_Drone_GlowYellow"]
fc=cls[fl]; core=np.isin(fl,CORE)
def write(path,mask):
    idx=np.where(mask)[0]
    used=np.unique(F[idx]); remap=np.full(len(V),-1); remap[used]=np.arange(len(used))
    usedt=np.unique(FT[idx]); rt=np.full(len(VT),-1); rt[usedt]=np.arange(len(usedt))
    with open(path,"w") as f:
        f.write("mtllib Drone_NV.mtl\no %s\n"%path[:-4])
        f.write("".join("v %.5f %.5f %.5f\n"%tuple(p) for p in V[used]))
        f.write("".join("vt %.5f %.5f\n"%tuple(t) for t in VT[usedt]))
        for c in range(5):
            sel=idx[fc[idx]==c]
            if not len(sel): continue
            f.write("usemtl %s\n"%names[c])
            a=remap[F[sel]]+1; b=rt[FT[sel]]+1
            f.write("".join("f %d/%d %d/%d %d/%d\n"%(x[0],y[0],x[1],y[1],x[2],y[2]) for x,y in zip(a,b)))
    print(path,len(idx),"tris",{names[c]:int((fc[idx]==c).sum()) for c in range(5)})
write("SM_SimDrone_Body.obj",~core)
write("SM_SimDrone_Core.obj",core)
cols=[(0.8,0.8,0.82),(0.9,0.25,0.05),(0.05,0.05,0.06),(0.2,0.9,1),(1,0.8,0.1)]
open("Drone_NV.mtl","w").write("".join("newmtl %s\nKd %.2f %.2f %.2f\n\n"%((n,)+c) for n,c in zip(names,cols)))
P=np.array([[225,226,228],[235,95,35],[45,47,52],[80,230,255],[255,210,40]]);np.save("pal2.npy",P[cls])
print("core bbox",V[np.unique(F[core])].min(0),V[np.unique(F[core])].max(0))
