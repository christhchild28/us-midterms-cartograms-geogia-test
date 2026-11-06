import json, math, pickle, sys, time, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from common import cfg as cfg_
cfg = cfg_.load()
import numpy as np, shapely
from shapely.geometry import Polygon
from shapely.ops import unary_union
from scipy.fft import dctn, idctn
from scipy.ndimage import map_coordinates, gaussian_filter
proj=cfg.proj
C=json.load(open(cfg.tmp('counties.json'))); feat=cfg.features()
polys=[]
for c in C:
    g=feat[c['fips']]['geometry']; ps=g['coordinates'] if g['type']=='MultiPolygon' else [g['coordinates']]
    L=[]
    for p in ps:
        pg=Polygon([proj(x,y) for x,y in p[0]]); q=pg if pg.is_valid else pg.buffer(0)
        if q.geom_type=='MultiPolygon': L.extend(q.geoms)   # an invalid ring can repair into several parts
        else: L.append(q)
    polys.append(L)
allarea=np.array([sum(p.area for p in L) for L in polys]); nhex=np.array([max(1,round(c['pop']/cfg.unit)) for c in C],float)
SB=float(cfg.lens.get('state_buffer',0.002))   # bridge gaps up to ~2*SB when joining land into one 'state' (islands like Staten Island need more)
state=unary_union([p.buffer(SB) for L in polys for p in L]).buffer(-SB)
if state.geom_type=='MultiPolygon': state=max(state.geoms,key=lambda g:g.area)
x0,y0,x1,y1=state.bounds
F=cfg.lens_scale(max(x1-x0,y1-y0))   # all lens lengths scale with the state's extent (Georgia = 1.0)
padx=(x1-x0)*0.45; pady=(y1-y0)*0.45
X0,X1,Y0,Y1=x0-padx,x1+padx,y0-pady,y1+pady
h=float(os.environ.get('LENS_GRID',cfg.lens['grid']))*F; NX=int((X1-X0)/h); NY=int((Y1-Y0)/h); hx=(X1-X0)/NX; hy=(Y1-Y0)/NY
gx=X0+(np.arange(NX)+.5)*hx; gy=Y0+(np.arange(NY)+.5)*hy; GX,GY=np.meshgrid(gx,gy)
meanD=nhex.sum()/allarea.sum()
G=np.ones((NY,NX)); LAB=-np.ones((NY,NX),int)   # LAB = county index per grid cell (-1 = none)
for i,L in enumerate(polys):
    for p in L:
        m=shapely.contains_xy(p,GX.ravel(),GY.ravel()).reshape(NY,NX)
        G[m]=(nhex[i]/allarea[i])/meanD; LAB[m]=i
INS=shapely.contains_xy(state,GX.ravel(),GY.ravel()).reshape(NY,NX)
G0=G.copy()
Lx=X1-X0; Ly=Y1-Y0
I=np.arange(NX)[None,:]; J=np.arange(NY)[:,None]
lam=math.pi**2*((I/Lx)**2+(J/Ly)**2)
# output node grid
HO=cfg.lens['node']*F; ox0=x0-0.25*F; oy0=y0-0.25*F; onx=int((x1-x0+0.5*F)/HO)+2; ony=int((y1-y0+0.5*F)/HO)+2
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
