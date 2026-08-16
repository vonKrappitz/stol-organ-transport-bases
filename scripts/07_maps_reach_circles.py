# Copyright 2026 Maciej M. Kasperek. Licensed under the Apache License, Version 2.0.
# paths relative to the repository root
import os as _os
try:
    _SCRIPT_DIR = _os.path.dirname(_os.path.abspath(__file__))
except NameError:
    _SCRIPT_DIR = _os.path.dirname(_os.path.abspath(_os.sys.argv[0])) or _os.getcwd()
_REPO_DIR  = _os.path.dirname(_SCRIPT_DIR)          # repository root
_DATA_DIR   = _os.path.join(_REPO_DIR, "data")
RESULTS      = _os.path.join(_REPO_DIR, "figures")     # figures and CSV go here
_os.makedirs(RESULTS, exist_ok=True)
_os.chdir(_DATA_DIR)                                  # bare paths read from data/
# end of path block

import csv, json, re, json, math, requests
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
# Shapely is used only to draw voivodeship outlines. Without it,
# coordinates are read straight from the GeoJSON; the result is the same.
try:
    from shapely.geometry import shape
    _MA_SHAPELY = True
except ImportError:
    _MA_SHAPELY = False
    def shape(g):
        return g
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
with open("airports.csv",newline='',encoding="utf-8") as f:
    for r in csv.DictReader(f):
        if r["iso_country"]!="PL" or r["type"] not in keep: continue
        ap[r["ident"]]={"icao":r["icao_code"] or r["ident"],"muni":r["municipality"] or r["name"],
            "lat":float(r["latitude_deg"]),"lon":float(r["longitude_deg"]),"rw":[]}
HARD=re.compile(r"asph|ashp|aspha|\basp\b|conc|\bcon\b|cement|bitum|tarmac|\btar\b|paved|\bpav|\bpem\b|sealed|\bseal\b|composite|\bcop\b|\bhard\b|macadam|\bpcn\b",re.I)
SOFT=re.compile(r"grass|\bgrs\b|turf|\bgvl\b|gravel|dirt|sand|soil|earth|clay|snow|\bice\b|water|\bsod\b|\bgre\b|unpaved|natural",re.I)
def hd(s):
    if not s:return False
    if SOFT.search(s) and not HARD.search(s):return False
    return bool(HARD.search(s))
with open("runways.csv",newline='',encoding="utf-8") as f:
    for r in csv.DictReader(f):
        a=r["airport_ident"]
        if a not in ap or r["closed"]=="1":continue
        try:ln=int(r["length_ft"])
        except:continue
        ap[a]["rw"].append((ln,r["surface"]))
AF={d["icao"]:d for a,d in ap.items() if [l for l,s in d["rw"] if hd(s)] and max([l for l,s in d["rw"] if hd(s)])*0.3048>=750}
# KOREKTA AUDYTU R10 (2026-07-18): EPBK Krywlany ma pas twardy 1350x30 (2018), brak w OurAirports
if "EPBK" not in AF and "EPBK" in ap: AF["EPBK"]=ap["EPBK"]
g=json.load(open("voivodeship_boundaries.json", encoding="utf-8")); OSR=g["osr"]; CENT=g["cent"]
def circ(lat,lon,km,n=120):
    R=6371.0;d=km/R;la1=math.radians(lat);lo1=math.radians(lon);xs=[];ys=[]
    for i in range(n+1):
        th=math.radians(i*360/n)
        la2=math.asin(math.sin(la1)*math.cos(d)+math.cos(la1)*math.sin(d)*math.cos(th))
        lo2=lo1+math.atan2(math.sin(th)*math.sin(d)*math.cos(la1),math.cos(d)-math.sin(la1)*math.sin(la2))
        xs.append(math.degrees(lo2));ys.append(math.degrees(la2))
    return xs,ys
def base(ax,title):
    for p in polys:
        if _MA_SHAPELY:
            _pier=[q.exterior.coords for q in ([p] if p.geom_type=="Polygon" else list(p.geoms))]
        elif p["type"]=="Polygon":
            _pier=[p["coordinates"][0]]
        else:
            _pier=[c[0] for c in p["coordinates"]]
        for _c in _pier:
            _xy=list(_c); ax.plot([t[0] for t in _xy],[t[1] for t in _xy],color="#b9bec8",lw=0.6,zorder=2)
    ax.set_aspect(1.62);ax.set_xticks([]);ax.set_yticks([])
    for sp in ax.spines.values():sp.set_visible(False)
    ax.set_title(title,fontsize=12,weight="bold",color="#1a1a2e")

# ---- map A: bases minimax + circles 100 km ----
fig,ax=plt.subplots(figsize=(8.4,8.8))
base(ax,"Minimax  |  100 km helicopter reach around 3 bases (zero-positioning zone)")
for ic,d in AF.items(): ax.scatter(d["lon"],d["lat"],s=6,color="#9aa0aa",zorder=3)
BAZY=["EPBK","EPBY","EPML"]
for ic in BAZY:
    d=AF[ic];xs,ys=circ(d["lat"],d["lon"],100)
    ax.fill(xs,ys,color="#1f77b4",alpha=0.13,zorder=1);ax.plot(xs,ys,color="#1f77b4",lw=1.1,alpha=0.6,zorder=4)
for c,(la,lo) in OSR.items():
    ax.scatter(lo,la,s=120,marker="*",color="#d62728",edgecolor="white",lw=0.6,zorder=6)
    if c=="Bydgoszcz": continue
    ax.annotate(c,(lo,la),(4,4),textcoords="offset points",fontsize=8,color="#7a1010",weight="bold")
for ic in BAZY:
    d=AF[ic];ax.scatter(d["lon"],d["lat"],s=230,marker="^",color="#1f77b4",edgecolor="white",lw=1.2,zorder=7)
    ax.annotate(d["muni"],(d["lon"],d["lat"]),(7,-13),textcoords="offset points",fontsize=9,color="#0d3b66",weight="bold")
leg=[Line2D([0],[0],marker="^",color="w",markerfacecolor="#1f77b4",markersize=13,label="STOL base"),
     Line2D([0],[0],marker="*",color="w",markerfacecolor="#d62728",markersize=15,label="centre"),
     Line2D([0],[0],marker="o",color="w",markerfacecolor="#1f77b4",alpha=0.3,markersize=13,label="feeder reach 100 km")]
ax.legend(handles=leg,loc="lower left",fontsize=9,frameon=False)
plt.tight_layout();plt.savefig(_os.path.join(RESULTS, "map_zero_positioning_zones.png"),dpi=350,bbox_inches="tight");plt.close()

# ---- map B: all 33 airfields set main + circles 100 km = full coverage ----
fig,ax=plt.subplots(figsize=(8.4,8.8))
base(ax,"Full helicopter feeder coverage  |  100 km circles around 33 airfields")
for ic,d in AF.items():
    xs,ys=circ(d["lat"],d["lon"],100)
    ax.fill(xs,ys,color="#2ca02c",alpha=0.06,zorder=1);ax.plot(xs,ys,color="#2ca02c",lw=0.4,alpha=0.25,zorder=2)
for ic,d in AF.items(): ax.scatter(d["lon"],d["lat"],s=8,color="#3a7d3a",zorder=4)
for c,(la,lo) in OSR.items():
    ax.scatter(lo,la,s=120,marker="*",color="#d62728",edgecolor="white",lw=0.6,zorder=6)
    ax.annotate(c,(lo,la),(4,4),textcoords="offset points",fontsize=8,color="#7a1010",weight="bold")
leg=[Line2D([0],[0],marker="o",color="w",markerfacecolor="#3a7d3a",markersize=9,label="airfield (33)"),
     Line2D([0],[0],marker="*",color="w",markerfacecolor="#d62728",markersize=15,label="centre"),
     Line2D([0],[0],marker="o",color="w",markerfacecolor="#2ca02c",alpha=0.25,markersize=13,label="feeder reach 100 km")]
ax.legend(handles=leg,loc="lower left",fontsize=9,frameon=False)
plt.tight_layout();plt.savefig(_os.path.join(RESULTS, "map_helicopter_reach.png"),dpi=350,bbox_inches="tight");plt.close()
print("OK dwie mapy z okregami")
