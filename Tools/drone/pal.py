import numpy as np, json
d=np.load('comps.npz');mn,mx,cnt=d['mn'],d['mx'],d['cnt'];K=len(cnt)
ext=(mx-mn).max(1)
cls=np.zeros(K,int)  # 0 white,1 orange,2 dark,3 cyan emis,4 yellow emis
for i in [8,30,29,182,23,5]: cls[i]=1
# small/thin pieces -> dark metal (bolts, cables): elongated tube-like
for i in range(K):
    e=np.sort(mx[i]-mn[i])
    if e[2]>5 and e[1]<1.2: cls[i]=2   # cables/rods
for i in [112,114,116,113,115,117]: cls[i]=2
for i in [184,185]: cls[i]=3
json.dump(cls.tolist(),open('cls.json','w'))
P=np.array([[225,226,228],[235,95,35],[45,47,52],[80,230,255],[255,210,40]])
np.save('pal.npy',P[cls])
