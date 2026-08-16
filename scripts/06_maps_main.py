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
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import matplotlib.patheffects as _pe
_OBW=[_pe.withStroke(linewidth=2.8, foreground="white")]
# Shapely is used only to draw voivodeship outlines. Without it,
# coordinates are read straight from the GeoJSON; the result is the same.
try:
    from shapely.geometry import shape
    _MA_SHAPELY = True
except ImportError:
    _MA_SHAPELY = False
    def shape(g):
        return g

# voivodeship boundaries
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

# airfields of the optimum set
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

def base(ax,title):
    for p in polys:
        if _MA_SHAPELY:
            _pier=[q.exterior.coords for q in ([p] if p.geom_type=="Polygon" else list(p.geoms))]
        elif p["type"]=="Polygon":
            _pier=[p["coordinates"][0]]
        else:
            _pier=[c[0] for c in p["coordinates"]]
        for _c in _pier:
            _xy=list(_c); ax.plot([t[0] for t in _xy],[t[1] for t in _xy],color="#c8ccd4",lw=0.6,zorder=1)
    for ic,d in AF.items(): ax.scatter(d["lon"],d["lat"],s=7,color="#9aa0aa",zorder=2)
    ax.set_aspect(1.62); ax.set_xticks([]); ax.set_yticks([])
    ax.margins(x=0.10, y=0.05)
    for sp in ax.spines.values(): sp.set_visible(False)
    ax.set_title(title,fontsize=8.6,weight="bold",color="#1a1a2e")

MET={
"Minimax":(["EPBK","EPBY","EPML"],"#1f77b4"),
"Weighted p-median":(["EPBC","EPKM","EPPO"],"#d62728"),
"Geographic p-median":(["EPKA","EPPO","EPSY"],"#2ca02c"),
"Worst-case coverage":(["EPKR","EPLB","EPPI"],"#9467bd"),
}

# ---- Figure 1: main result ----
fig,ax=plt.subplots(figsize=(4.51,4.73))
base(ax,"Minimax, 3 STOL bases  |  worst case 143.5 min (audited set)")
# centres
for c,(la,lo) in OSR.items():
    ax.scatter(lo,la,s=120,marker="*",color="#d62728",edgecolor="white",lw=0.6,zorder=4)
    if c=="Bydgoszcz": continue
    # Zabrze, Katowice and Krakow lie close together, so their labels fan
    # out in different directions. The rest go right and up.
    _KIER_OSR = {"Zabrze": ((-8, 4), "right"), "Katowice": ((-8, -12), "right"),
                 "Kraków": ((8, -12), "left"), "Wrocław": ((8, -2), "left"),
                 "Bydgoszcz": ((-8, 4), "right")}
    _oo, _hh = _KIER_OSR.get(c, ((7, 5), "left"))
    ax.annotate(c,(lo,la),_oo,textcoords="offset points",fontsize=5.8,color="#7a1010",weight="bold",ha=_hh,zorder=8,path_effects=_OBW)
# minimax bases
for ic in MET["Minimax"][0]:
    d=AF[ic]; ax.scatter(d["lon"],d["lat"],s=240,marker="^",color="#1f77b4",edgecolor="white",lw=1.2,zorder=5)
    # Label direction follows the neighbourhood. Bialystok sits at the frame edge,
    # so its label goes left. Mielec has Krakow to the west, so right.
    _KIER = {"EPBK": ((-12, -2), "right"), "EPML": ((12, -4), "left"), "EPBY": ((-12, -2), "right")}
    _o, _h = _KIER.get(ic, ((0, -24), "center"))
    ax.annotate(f"BASE {d['muni']}",(d["lon"],d["lat"]),_o,textcoords="offset points",fontsize=6.5,color="#0d3b66",weight="bold",ha=_h,zorder=9,path_effects=_OBW)
# binding diagonal: Lubelskie centroid -> Szczecin
ll=CENT["lubelskie"]; sz=OSR["Szczecin"]
ax.plot([ll[1],sz[1]],[ll[0],sz[0]],"--",color="#ff7f0e",lw=2,zorder=3)
ax.scatter(ll[1],ll[0],s=70,color="#ff7f0e",zorder=4,edgecolor="white")
leg=[Line2D([0],[0],marker="^",color="w",markerfacecolor="#1f77b4",markersize=13,label="STOL base (minimax)"),
     Line2D([0],[0],marker="*",color="w",markerfacecolor="#d62728",markersize=15,label="transplant centre"),
     Line2D([0],[0],marker="o",color="w",markerfacecolor="#9aa0aa",markersize=8,label="candidate airfield (33)"),
     Line2D([0],[0],color="#ff7f0e",lw=2,ls="--",label="worst case, Lublin region to Szczecin, lungs")]
# Legend below the map, not on it; at the enlarged figure size the legend
# text overlapped centre labels in southern Poland.
ax.legend(handles=leg,loc="upper center",bbox_to_anchor=(0.5,-0.01),ncol=2,fontsize=6.5,frameon=False)
plt.tight_layout(); plt.savefig(_os.path.join(RESULTS, "map_minimax_placement.png"),dpi=350,bbox_inches="tight", pad_inches=0.05); plt.close()

# ---- Figure 2: the four methods in a two-by-two layout ----
fig,axs=plt.subplots(2,2,figsize=(6.6,6.93))
for ax,(nm,(bs,col)) in zip(axs.flat,MET.items()):
    base(ax,nm)
    for c,(la,lo) in OSR.items():
        ax.scatter(lo,la,s=55,marker="*",color="#d0a0a0",edgecolor="white",lw=0.4,zorder=4)
    for ic in bs:
        d=AF[ic]; ax.scatter(d["lon"],d["lat"],s=210,marker="^",color=col,edgecolor="white",lw=1.1,zorder=5)
        disp=d["muni"].replace("Warsaw","Warszawa")[:12]
        off,ha=((0,-22),"center")
        ax.annotate(disp,(d["lon"],d["lat"]),off,textcoords="offset points",fontsize=7.6,color=col,weight="bold",ha=ha,zorder=9,path_effects=_OBW)
plt.tight_layout(); plt.savefig(_os.path.join(RESULTS, "map_four_methods.png"),dpi=350,bbox_inches="tight", pad_inches=0.05); plt.close()
print("OK written dwie mapy")
print("airfields:",len(AF),"| centres:",len(OSR))
