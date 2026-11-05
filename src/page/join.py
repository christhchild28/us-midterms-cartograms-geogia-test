import csv, json, math
sen={r['county']:r for r in csv.DictReader(open('/tmp/ga/senate.csv'))}
uid={}
for r in csv.DictReader(open('/tmp/ga/raw/uid.csv')):
    if r['Province_State']=='Georgia' and r['FIPS'] and r['Admin2']:
        uid[r['Admin2']]=(r['FIPS'].split('.')[0].zfill(5), int(float(r['Population'] or 0)))
gj=json.load(open('/tmp/ga/raw/counties.json'))
feat={f['id']:f for f in gj['features'] if f['id'].startswith('13')}
def centroid(geom):
    polys=geom['coordinates'] if geom['type']=='MultiPolygon' else [geom['coordinates']]
    A=cx=cy=0
    for p in polys:
        ring=p[0]
        for i in range(len(ring)-1):
            x0,y0=ring[i];x1,y1=ring[i+1]
            c=x0*y1-x1*y0;A+=c;cx+=(x0+x1)*c;cy+=(y0+y1)*c
    A/=2;return cx/(6*A),cy/(6*A)
out=[];miss=[]
for name,r in sen.items():
    key=name
    if key not in uid: miss.append(name);continue
    fips,pop=uid[key]
    if fips not in feat: miss.append(name+'(geo)');continue
    lon,lat=centroid(feat[fips]['geometry'])
    out.append(dict(name=name,fips=fips,pop=pop,lon=round(lon,4),lat=round(lat,4),d=int(r['ossoff']),r=int(r['collins'])))
print(len(out),'missing',miss)
print('pop total',sum(o['pop'] for o in out))
print(sorted(out,key=lambda o:-o['pop'])[:6])
print([o for o in out if o['pop']<=0])
json.dump(out,open('/tmp/ga/build/counties.json','w'))
