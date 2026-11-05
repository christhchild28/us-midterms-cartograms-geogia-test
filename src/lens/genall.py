import numpy as np, json, gzip, base64, math, time, sys
import lensfield as L
from shapely.geometry import Point
SP=float(sys.argv[1]) if len(sys.argv)>1 else 0.35
x0,y0,x1,y1=L.state.bounds
xs=np.arange(x0-0.1,x1+0.1+1e-9,SP); ys=np.arange(y0-0.1,y1+0.1+1e-9,SP)
centers=[(i,j) for j in range(len(ys)) for i in range(len(xs)) if L.state.distance(Point(xs[i],ys[j]))<0.28]
print('grid',len(xs),len(ys),'centers',len(centers))
out={}
t=time.time()
for R in (0.45,0.8):
    arr=np.zeros((len(ys),len(xs),L.ony,L.onx,2),np.int16); have=np.zeros((len(ys),len(xs)),bool); dmin=9
    for (i,j) in centers:
        U,det=L.field(xs[i],ys[j],R); dmin=min(dmin,det.min())
        arr[j,i]=np.round(U*2000).astype(np.int16); have[j,i]=True
        assert np.abs(U).max()*2000<32000
    out[R]=(arr,have); print('R',R,'done',round(time.time()-t),'min det',round(dmin,3),flush=True)
# pack: list of centers in order, per radius
def enc(a):
    d=a.astype(np.int32).copy(); d[:,1:,:]=a[:,1:,:].astype(np.int32)-a[:,:-1,:].astype(np.int32)
    return d.astype(np.int16).tobytes()
blob=b''.join(enc(out[R][0][j,i]) for R in (0.45,0.8) for (i,j) in centers)
gz=gzip.compress(blob,9)
print('raw MB',len(blob)/1e6,'gz MB',len(gz)/1e6,'b64 MB',len(gz)*4/3/1e6)
meta=dict(h=L.HO,ox=L.ox0,oy=L.oy0,nx=L.onx,ny=L.ony,scale=2000,sx=float(xs[0]),sy=float(ys[0]),sp=SP,gx=len(xs),gy=len(ys),
          centers=[[int(i),int(j)] for (i,j) in centers],radii=[0.45,0.8],data=base64.b64encode(gz).decode())
json.dump(meta,open('lens.json','w'),separators=(',',':'))
# interpolation error check: midpoint between two neighbouring centers vs direct
(i,j)=[c for c in centers if (c[0]+1,c[1]) in centers][len(centers)//4]
mx=(xs[i]+xs[i+1])/2; my=ys[j]
Ud,_=L.field(mx,my,0.8)
Ua=(out[0.8][0][j,i].astype(float)+out[0.8][0][j,i+1].astype(float))/2/2000
print('interp err: max',np.abs(Ud-Ua).max(),'rms',np.sqrt(((Ud-Ua)**2).mean()),'of max|U|',np.abs(Ud).max())
