import numpy as np, sys
src=sys.argv[1]
V=[];F=[];VT=[];VN=[];FT=[];FN=[]
with open(src) as f:
    for line in f:
        if line.startswith("v "): V.append(line.split()[1:4])
        elif line.startswith("vt "): VT.append(line.split()[1:3])
        elif line.startswith("vn "): VN.append(line.split()[1:4])
        elif line.startswith("f "):
            parts=line.split()[1:]
            if len(parts)!=3: 
                # triangulate fan
                pass
            ids=[p.split("/") for p in parts]
            for k in range(1,len(ids)-1):
                tri=[ids[0],ids[k],ids[k+1]]
                F.append([int(t[0]) for t in tri])
                FT.append([int(t[1]) if len(t)>1 and t[1] else 0 for t in tri])
                FN.append([int(t[2]) if len(t)>2 and t[2] else 0 for t in tri])
V=np.array(V,float);F=np.array(F)-1
np.savez("mesh.npz",V=V,F=F,VT=np.array(VT,float) if VT else np.zeros((0,2)),VN=np.array(VN,float) if VN else np.zeros((0,3)),FT=np.array(FT)-1,FN=np.array(FN)-1)
print(V.shape,F.shape,len(VT),len(VN))
