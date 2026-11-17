"""Recover the native pixel grid of an upscaled pixel-art logo.

Usage: python3 tools/logo_from_source.py design/logo/logo-source.png native.png preview.png
(then trim and add a 1px margin -> design/logo/logo-icon.png)
Finds the cell size/offset that makes each cell most uniform, samples cell centres, trims, and
centres the result on a 32x32 canvas (build.py scales it x4 into pack.png).
"""
import sys
from PIL import Image
import numpy as np
src=Image.open(sys.argv[1]).convert('RGBA'); a=np.asarray(src).astype(float)
op=a[...,3]>128; ys,xs=np.where(op); x0,y0,x1,y1=xs.min(),ys.min(),xs.max()+1,ys.max()+1
best=None
for s in np.arange(30.0,35.01,0.1):
    for ox in np.arange(0,s,s/8):
        for oy in np.arange(0,s,s/8):
            gx=np.arange(x0-s+ox, x1, s); gy=np.arange(y0-s+oy, y1, s)
            # sample a 5x5 patch around each cell centre; score = within-cell spread
            cx=(gx+s/2).astype(int); cy=(gy+s/2).astype(int)
            cx=cx[(cx>2)&(cx<a.shape[1]-3)]; cy=cy[(cy>2)&(cy<a.shape[0]-3)]
            if len(cx)<5 or len(cy)<5: continue
            sc=0
            for d in (-int(s*0.35), int(s*0.35)):
                sc+=np.abs(a[np.ix_(cy,cx)][...,:]-a[np.ix_(np.clip(cy+d,0,a.shape[0]-1),np.clip(cx+d,0,a.shape[1]-1))]).mean()
            if best is None or sc<best[0]: best=(sc,s,ox,oy,cx,cy)
sc,s,ox,oy,cx,cy=best
print('cell',round(s,2),'grid',len(cx),'x',len(cy))
cells=a[np.ix_(cy,cx)]
img=Image.fromarray(np.where(cells[...,3:4]>128, np.concatenate([cells[...,:3],np.full(cells.shape[:2]+(1,),255)],-1),0).astype(np.uint8),'RGBA')
bb=img.getbbox(); img=img.crop(bb); print('native',img.size)
N=32; can=Image.new('RGBA',(N,N),(0,0,0,0)); can.alpha_composite(img,((N-img.width)//2,(N-img.height)//2))
can.save(sys.argv[2]); can.resize((N*4,N*4),Image.NEAREST).save(sys.argv[3])
