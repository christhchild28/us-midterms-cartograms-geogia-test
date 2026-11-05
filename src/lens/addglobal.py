import json,gzip,base64,numpy as np,math,pickle
import lensfield as L
from scipy.ndimage import map_coordinates
from shapely import wkt
import matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt
U,det=L.field(0,0,1,glob=True)
print('global det min/max',det.min(),det.max(),'max|U|',np.abs(U).max())
pickle.dump(U,open('global_U.pkl','wb'))
def warp(pts):
    ix=(pts[:,0]-L.ox0)/L.HO; iy=(pts[:,1]-L.oy0)/L.HO
    return pts+np.stack([map_coordinates(U[:,:,0],[iy,ix],order=1,mode='nearest'),map_coordinates(U[:,:,1],[iy,ix],order=1,mode='nearest')],1)
# bbox of warped counties
allw=[];fig,ax=plt.subplots(figsize=(6,7))
for i,ps in enumerate(L.polys):
    for p in ps:
        w=warp(np.array(p.exterior.coords)); allw.append(w)
        c=L.C[i]; m=(c['d']-c['r'])/(c['d']+c['r']); ax.fill(w[:,0],w[:,1],fc=plt.cm.RdBu(.5+max(-1,min(1,m/.6))*.5),ec='white',lw=.4)
so=np.array(L.state.exterior.coords); ax.plot(so[:,0],so[:,1],'k--',lw=.8)
ax.set_aspect('equal');ax.invert_yaxis();ax.axis('off');plt.savefig('global.png',dpi=70,bbox_inches='tight')
allw=np.vstack(allw); bx0,by0=allw.min(0); bx1,by1=allw.max(0)
sx0,sy0,sx1,sy1=L.state.bounds
print('orig bbox',sx0,sy0,sx1,sy1,'warped',bx0,by0,bx1,by1)
# page viewBox aspect from rings2 bounds
D=json.load(open('/tmp/ga/hp/rings2.json')); B=D['bounds']; vw=B[2]-B[0]; vh=B[3]-B[1]
w=(bx1-bx0)*1.06; h=(by1-by0)*1.06; cx=(bx0+bx1)/2; cy=(by0+by1)/2
if w/h<vw/vh: w=h*vw/vh
else: h=w*vh/vw
w=max(w,vw); h=max(h,vh)
gvb=[cx-w/2,cy-h/2,w,h]; print('gvb',gvb,'base',B)
# merge into lens.json
M=json.load(open('lens.json')); raw=gzip.decompress(base64.b64decode(M['data']))
a=np.round(U*2000).astype(np.int16); assert np.abs(U).max()*2000<32000
d=a.astype(np.int32).copy(); d[:,1:,:]=a[:,1:,:].astype(np.int32)-a[:,:-1,:].astype(np.int32)
raw2=raw+d.astype(np.int16).tobytes()
M['data']=base64.b64encode(gzip.compress(raw2,9)).decode(); M['gvb']=[round(v,4) for v in gvb]
st=L.state.simplify(0.004); xy=np.array(st.exterior.coords)[:-1]
M['outline']=[int(round(v*1000)) for v in xy.reshape(-1)]
json.dump(M,open('lens2.json','w'),separators=(',',':'))
print('outline pts',len(xy),'size MB',len(json.dumps(M))/1e6)
# IoU of warped state vs original
from shapely.ops import unary_union
from shapely.geometry import Polygon
ws=unary_union([Polygon(w_).buffer(0.002) for w_ in [warp(np.array(p.exterior.coords)) for ps in L.polys for p in ps]]).buffer(-0.002)
print('IoU warped state vs original',L.state.intersection(ws).area/L.state.union(ws).area)
