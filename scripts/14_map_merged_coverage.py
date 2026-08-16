# Copyright 2026 Maciej M. Kasperek. Licensed under the Apache License, Version 2.0.
# paths relative to the repository root
import os as _os
try:
    _SCRIPT_DIR = _os.path.dirname(_os.path.abspath(__file__))
except NameError:
    _SCRIPT_DIR = _os.path.dirname(_os.path.abspath(_os.sys.argv[0])) or _os.getcwd()
_REPO_DIR  = _os.path.dirname(_SCRIPT_DIR)          # repository root
_DATA_DIR   = _os.path.join(_REPO_DIR, "data")
RESULTS      = _os.path.join(_REPO_DIR, "results")     # figures and CSV go here
_os.makedirs(RESULTS, exist_ok=True)
_os.chdir(_DATA_DIR)                                  # bare paths read from data/
# end of path block

import csv, json, re, json, math, requests
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from shapely.geometry import shape, Polygon
from shapely.ops import unary_union
# Voivodeship boundaries: local copy first, network second, so
# rerunning works offline.
_GEOJ = _os.path.join(_DANE_DIR, "wojewodztwa.geojson") if "_DANE_DIR" in dir() else "wojewodztwa.geojson"
if _os.path.exists(_GEOJ):
    gj = json.load(open(_GEOJ, encoding="utf-8"))
else:
    gj = requests.get("https://raw.githubusercontent.com/ppatrzyk/polska-geojson/master/wojewodztwa/wojewodztwa-medium.geojson", timeout=30).json()
    try:
        json.dump(gj, open(_GEOJ, "w", encoding="utf-8"))
        print(f"  cached boundaries to {_GEOJ}")
    except Exception:
        pass
polys=[shape(ft["geometry"]) for ft in gj["features"]]
keep={"small_airport","medium_airport","large_airport"}
ap={}
for r in csv.DictReader(open("airports.csv",newline='',encoding="utf-8")):
    if r["iso_country"]!="PL" or r["type"] not in keep: continue
    ap[r["ident"]]={"muni":r["municipality"] or r["name"],"lat":float(r["latitude_deg"]),"lon":float(r["longitude_deg"]),"rw":[]}
HARD=re.compile(r"asph|ashp|aspha|\basp\b|conc|\bcon\b|cement|bitum|tarmac|\btar\b|paved|\bpav|\bpem\b|sealed|\bseal\b|composite|\bcop\b|\bhard\b|macadam|\bpcn\b",re.I)
SOFT=re.compile(r"grass|\bgrs\b|turf|\bgvl\b|gravel|dirt|sand|soil|earth|clay|snow|\bice\b|water|\bsod\b|\bgre\b|unpaved|natural",re.I)
def hd(s):
    if not s:return False
    if SOFT.search(s) and not HARD.search(s):return False
    return bool(HARD.search(s))
for r in csv.DictReader(open("runways.csv",newline='',encoding="utf-8")):
    a=r["airport_ident"]
    if a not in ap or r["closed"]=="1":continue
    try:ln=int(r["length_ft"])
    except:continue
    ap[a]["rw"].append((ln,r["surface"]))

import csv as _csv
_TROJKA=["EPBY","EPML","EPSY"]
_CERT13=["EPWA","EPGD","EPKT","EPKK","EPLL","EPPO","EPRZ","EPSC","EPMO","EPWR","EPZG","EPLB","EPRA"]
AUDYT33=sorted(set(_TROJKA+_CERT13+[r["icao"] for r in _csv.DictReader(open("airfield_audit_thresholds.csv", encoding="utf-8")) if r["prog_kons"]=="1"]))
def _audyt_af_dict(ap,hd):
    def _ic(a,d): return d.get("icao") or a
    AF={_ic(a,d):d for a,d in ap.items() if _ic(a,d) in AUDYT33}
    for _m in set(AUDYT33)-set(AF):
        for a,d in ap.items():
            if _ic(a,d)==_m: AF[_m]=d
    return AF
AF=list(_audyt_af_dict(ap,hd).values())
g=json.load(open("voivodeship_boundaries.json", encoding="utf-8")); OSR=g["osr"]
def circ(lat,lon,km,n=72):
    R=6371.0;d=km/R;la1=math.radians(lat);lo1=math.radians(lon);P=[]
    for i in range(n+1):
        th=math.radians(i*360/n)
        la2=math.asin(math.sin(la1)*math.cos(d)+math.cos(la1)*math.sin(d)*math.cos(th))
        lo2=lo1+math.atan2(math.sin(th)*math.sin(d)*math.cos(la1),math.cos(d)-math.sin(la1)*math.sin(la2))
        P.append((math.degrees(lo2),math.degrees(la2)))
    return Polygon(P)
cover=unary_union([circ(d["lat"],d["lon"],100) for d in AF])  # sum 51 buforow 100 km
pl=unary_union(polys)
fig,ax=plt.subplots(figsize=(8.4,8.8))
# coverage area as a single blob
def drawpoly(geom,**kw):
    gs=[geom] if geom.geom_type=="Polygon" else list(geom.geoms)
    for q in gs:
        x,y=q.exterior.xy; ax.fill(x,y,**kw)
drawpoly(cover,color="#2ca02c",alpha=0.16,zorder=1)
gs=[cover] if cover.geom_type=="Polygon" else list(cover.geoms)
for q in gs:
    x,y=q.exterior.xy; ax.plot(x,y,color="#2ca02c",lw=1.4,alpha=0.85,zorder=2)
for p in polys:
    for q in ([p] if p.geom_type=="Polygon" else list(p.geoms)):
        x,y=q.exterior.xy; ax.plot(x,y,color="#7a7f8a",lw=0.7,zorder=3)
for d in AF: ax.scatter(d["lon"],d["lat"],s=11,color="#1d6b1d",zorder=4)
for c,(la,lo) in OSR.items():
    ax.scatter(lo,la,s=120,marker="*",color="#d62728",edgecolor="white",lw=0.6,zorder=6)
    ax.annotate(c,(lo,la),(4,4),textcoords="offset points",fontsize=8,color="#7a1010",weight="bold")
ax.set_aspect(1.62);ax.set_xticks([]);ax.set_yticks([])
for sp in ax.spines.values():sp.set_visible(False)
ax.set_title(f"Geometric reach of the helicopter feeder\nmerged 100 km radius from the {len(AUDYT33)} airfields of the main set, the whole country inside",fontsize=12.5,weight="bold",color="#1a1a2e")
leg=[Patch(facecolor="#2ca02c",alpha=0.3,edgecolor="#2ca02c",label="helicopter reach (merged 100 km)"),
     Line2D([0],[0],marker="o",color="w",markerfacecolor="#1d6b1d",markersize=9,label=f"airfield ({len(AUDYT33)})"),
     Line2D([0],[0],marker="*",color="w",markerfacecolor="#d62728",markersize=14,label="transplant centre")]
ax.legend(handles=leg,loc="lower left",fontsize=9,frameon=False)
plt.tight_layout();plt.savefig(_os.path.join(RESULTS, "map_helicopter_reach.png"),dpi=145,bbox_inches="tight");plt.close()
print("OK merged coverage map, geometry type:",cover.geom_type)
