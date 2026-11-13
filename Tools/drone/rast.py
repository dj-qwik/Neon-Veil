import numpy as np, sys
from PIL import Image, ImageDraw
d=np.load("mesh.npz");V=d["V"];F=d["F"];fl=np.load("flab.npy")
T=V[F]
N=np.cross(T[:,1]-T[:,0],T[:,2]-T[:,0]);N/=np.linalg.norm(N,axis=1,keepdims=True)+1e-12
rng=np.random.default_rng(3);col=rng.integers(50,255,(fl.max()+1,3))
pal=np.load(sys.argv[2]) if len(sys.argv)>2 else None
views={"front":(np.array([1,0,0]),np.array([0,1,0]),np.array([0,0,1])),
       "back":(np.array([-1,0,0]),np.array([0,1,0]),np.array([0,0,-1])),
       "right":(np.array([0,0,-1]),np.array([0,1,0]),np.array([1,0,0])),
       "left":(np.array([0,0,1]),np.array([0,1,0]),np.array([-1,0,0])),
       "bottom":(np.array([1,0,0]),np.array([0,0,1]),np.array([0,-1,0]))}
S=700
out=[]
for name,(ax_u,ax_v,ax_d) in views.items():
    u=T@ax_u;v=T@ax_v;dep=(T@ax_d).mean(1)
    facing=(N@ax_d)
    o=np.argsort(dep)  # far first (smaller dep = farther if camera at +ax_d)
    px=(u+20)/40*S;py=(20-v)/40*S
    im=Image.new("RGB",(S,S));dr=ImageDraw.Draw(im)
    base=(col if pal is None else pal)[fl]
    sh=np.clip(np.abs(facing),0,1)*0.75+0.25
    cc=(base*sh[:,None]).astype(int)
    for i in o:
        dr.polygon([(px[i,0],py[i,0]),(px[i,1],py[i,1]),(px[i,2],py[i,2])],fill=tuple(cc[i]))
    if pal is None:
        for k in np.unique(fl):
            m=fl==k
            if m.sum()<3000: continue
            vis=m&(facing>0.3)
            if vis.sum()<50: continue
            dr.text((px[vis].mean(),py[vis].mean()),str(k),fill=(255,255,255))
    dr.text((5,5),name,fill=(255,255,0))
    out.append(im)
W=Image.new("RGB",(S*3,S*2))
for i,im in enumerate(out): W.paste(im,((i%3)*S,(i//3)*S))
W.save(sys.argv[1])
