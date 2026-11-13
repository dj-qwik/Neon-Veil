import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
d=np.load("mesh.npz");V=d["V"];F=d["F"]
n=len(V)
r=np.concatenate([F[:,0],F[:,1],F[:,2]]);c=np.concatenate([F[:,1],F[:,2],F[:,0]])
g=coo_matrix((np.ones(len(r)),(r,c)),shape=(n,n))
k,lab=connected_components(g,directed=False)
fl=lab[F[:,0]]
print("components",k)
np.save("flab.npy",fl)
cnt=np.bincount(fl,minlength=k)
# bbox per comp
mn=np.full((k,3),1e9);mx=np.full((k,3),-1e9)
np.minimum.at(mn,lab,V);np.maximum.at(mx,lab,V)
np.savez("comps.npz",mn=mn,mx=mx,cnt=cnt,lab=lab)
o=np.argsort(-cnt)
for i in o[:40]: print(i,cnt[i],mn[i].round(1),mx[i].round(1))
print("sizes>1000:",(cnt>1000).sum(),">100:",(cnt>100).sum())
