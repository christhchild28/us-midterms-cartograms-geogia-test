import json, math, pickle, sys, time
import numpy as np, shapely
from shapely.geometry import Polygon
from shapely.ops import unary_union
from scipy.fft import dctn, idctn
from scipy.ndimage import map_coordinates, gaussian_filter
LON0=-83.4; KK=math.cos(math.radians(32.7))
def proj(lon,lat): return ((lon-LON0)*KK,-lat)
C=json.load(open('/tmp/ga/build/counties.json')); gj=json.load(open('/tmp/ga/raw/counties.json'))
feat={f['id']:f for f in gj['features'] if f['id'].startswith('13')}
polys=[]
for c in C:
    g=feat[c['fips']]['geometry']; ps=g['coordinates'] if g['type']=='MultiPolygon' else [g['coordinates']]
    L=[]
    for p in ps:
        pg=Polygon([proj(x,y) for x,y in p[0]]); L.append(pg if pg.is_valid else pg.buffer(0))
    polys.append(L)
allarea=np.array([sum(p.area for p in L) for L in polys]); nhex=np.array([max(1,round(c['pop']/10000)) for c in C],float)
state=unary_union([p.buffer(0.002) for L in polys for p in L]).buffer(-0.002)
if state.geom_type=='MultiPolygon': state=max(state.geoms,key=lambda g:g.area)
x0,y0,x1,y1=state.bounds
padx=(x1-x0)*0.45; pady=(y1-y0)*0.45
X0,X1,Y0,Y1=x0-padx,x1+padx,y0-pady,y1+pady
h=0.03; NX=int((X1-X0)/h); NY=int((Y1-Y0)/h); hx=(X1-X0)/NX; hy=(Y1-Y0)/NY
gx=X0+(np.arange(NX)+.5)*hx; gy=Y0+(np.arange(NY)+.5)*hy; GX,GY=np.meshgrid(gx,gy)
meanD=nhex.sum()/allarea.sum()
G=np.ones((NY,NX))
for i,L in enumerate(polys):
    for p in L:
        m=shapely.contains_xy(p,GX.ravel(),GY.ravel()).reshape(NY,NX)
        G[m]=(nhex[i]/allarea[i])/meanD
INS=shapely.contains_xy(state,GX.ravel(),GY.ravel()).reshape(NY,NX)
G0=G.copy()
Lx=X1-X0; Ly=Y1-Y0
I=np.arange(NX)[None,:]; J=np.arange(NY)[:,None]
lam=math.pi**2*((I/Lx)**2+(J/Ly)**2)
# output node grid
HO=0.09; ox0=x0-0.25; oy0=y0-0.25; onx=int((x1-x0+0.5)/HO)+2; ony=int((y1-y0+0.5)/HO)+2
ONX=ox0+np.arange(onx)*HO; ONY=oy0+np.arange(ony)*HO
NODES=np.array([(a,b) for b in ONY for a in ONX])
def smooth(x): x=np.clip(x,0,1); return x*x*(3-2*x)
def field(cx,cy,R,core=0.55,glob=False,sea=1.0):
    G=np.where(INS,G0,sea)
    r=np.hypot(GX-cx,GY-cy); lw=np.ones_like(r) if glob else 1-smooth((r-core*R)/(R*(1-core)))
    rho=gaussian_filter(1+lw*(G-1),1.5,mode='nearest')
    rh=dctn(rho,type=2,norm='ortho')
    def rho_t(t): return idctn(rh*np.exp(-lam*t),type=2,norm='ortho')
    def vel(r,P):
        gyy,gxx=np.gradient(r,hy,hx)
        ix=(P[:,0]-X0)/hx-.5; iy=(P[:,1]-Y0)/hy-.5
        f=lambda a: map_coordinates(a,[iy,ix],order=1,mode='nearest')
        rp=f(r); return np.stack([-f(gxx)/rp,-f(gyy)/rp],1)
    P=NODES.copy(); T=2.2*max(Lx,Ly)**2/math.pi**2; t=0.0
    while t<T:
        r1=rho_t(t); v1=vel(r1,P); vm=np.abs(v1).max()
        dt=min(0.3*min(hx,hy)/max(vm,1e-9),T-t,0.02*T)
        r2=rho_t(t+dt/2); v2=vel(r2,P+0.5*dt*v1); P=P+dt*v2; t+=dt
    U=(P-NODES).reshape(ony,onx,2)
    # fold check: det of mapping on node grid
    px=NODES[:,0].reshape(ony,onx)+U[:,:,0]; py=NODES[:,1].reshape(ony,onx)+U[:,:,1]
    dxx=np.gradient(px,HO,axis=1); dxy=np.gradient(px,HO,axis=0); dyx=np.gradient(py,HO,axis=1); dyy=np.gradient(py,HO,axis=0)
    det=dxx*dyy-dxy*dyx
    return U,det
if __name__=='__main__':
    t=time.time()
    c=[cc for cc in C if cc['name']=='Fulton'][0]
    ctr=max(polys[C.index(c)],key=lambda q:q.area).centroid
    U,det=field(ctr.x,ctr.y,0.7)
    print('time',round(time.time()-t,1),'grid',onx,ony,'max|U|',np.abs(U).max(),'det min/max',det.min(),det.max())
    pickle.dump((U,det,ctr.coords[0]),open('test_atl.pkl','wb'))
