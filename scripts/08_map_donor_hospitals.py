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

import csv, json, re, json, math, requests, time
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import matplotlib.patheffects as _pe
_OBW=[_pe.withStroke(linewidth=2.6, foreground="white")]
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
        ap[r["ident"]]={"icao":r["icao_code"] or r["ident"],"muni":r["municipality"] or r["name"],"lat":float(r["latitude_deg"]),"lon":float(r["longitude_deg"]),"rw":[]}
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

import csv as _csv
_TROJKA=["EPBY","EPML","EPSY"]
_CERT13=["EPWA","EPGD","EPKT","EPKK","EPLL","EPPO","EPRZ","EPSC","EPMO","EPWR","EPZG","EPLB","EPRA"]
AUDYT33=sorted(set(_TROJKA+_CERT13+[r["icao"] for r in _csv.DictReader(open("airfield_audit_thresholds.csv", encoding="utf-8")) if r["prog_kons"]=="1"]))
def _audyt_af_dict(ap,hd):
    AF={d["icao"]:d for a,d in ap.items() if d["icao"] in AUDYT33}
    for _ic in set(AUDYT33)-set(AF):
        for a,d in ap.items():
            if d["icao"]==_ic: AF[_ic]=d
    return AF
AF=_audyt_af_dict(ap,hd)
g=json.load(open("voivodeship_boundaries.json", encoding="utf-8")); OSR=g["osr"]; CENT=g["cent"]
# 18 donor hospitals (report, Table 7, 2024): (city, label, donors)
H=[("Kraków","Szpital Uniw. CM UJ",27),("Kielce","WSZ Kielce",25),("Gdańsk","UCK Gdańsk",24),
("Warszawa","PIM MSWiA",23),("Katowice","GCM Ochojec",23),("Szczecin","SPWSZ Szczecin",17),
("Białystok","USK Białystok",16),("Warszawa","CSK UCK WUM",14),("Police","USK1 PUM Police",14),
("Wrocław","4 WSK Wrocław",13),("Wrocław","USK Wrocław",13),("Gdańsk","Copernicus Gdańsk",11),
("Olsztyn","WSS Olsztyn",11),("Rzeszów","KSW2 Rzeszów",10),("Wrocław","DSS Marciniaka",10),
("Poznań","Szpital Strusia",10),("Konin","WSZ Konin",10),("Zielona Góra","Szpital Uniw. ZG",10)]
# Hospital city coordinates are read from the same data file that script 21
# uses for the calculations, so the map shows exactly the points that the
# optimisation works on.
# the optimisation works on; drawing the map needs no geocoder or network.
citycoord = dict(OSR)
_MIASTA_PLIK = _os.path.join(_DANE_DIR, "hospital_cities.json") if "_DANE_DIR" in dir() else "hospital_cities.json"
if _os.path.exists(_MIASTA_PLIK):
    citycoord.update({k: tuple(v) for k, v in json.load(open(_MIASTA_PLIK, encoding="utf-8")).items()})
_brak = [c for c, _, _ in H if c not in citycoord]
if _brak:
    from geopy.geocoders import Nominatim
    from geopy.extra.rate_limiter import RateLimiter
    gc = RateLimiter(Nominatim(user_agent="lpr_stol_repro").geocode, min_delay_seconds=1.1)
    for city in dict.fromkeys(_brak):
        loc = gc(city + ", Polska")
        if loc:
            citycoord[city] = (round(loc.latitude, 4), round(loc.longitude, 4))
            print("geo", city, citycoord[city])

# spread hospitals in the same city slightly
seen={}
HP=[]
for city,lab,don in H:
    la,lo=citycoord[city]; k=seen.get(city,0); seen[city]=k+1
    # Several hospitals in one city are spread around a circle so points and
    # numbers do not overlap. The shift is purely graphical, noted in the caption.
    ang = k * 2.2
    la2 = la + 0.22 * math.sin(ang)
    lo2 = lo + 0.35 * math.cos(ang)
    HP.append((lo2 if k else lo, la2 if k else la, lab, don, city))
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
fig,ax=plt.subplots(figsize=(8.6,9))
base(ax,"Real sources: 18 leading donor hospitals, numbered by donor count, against centroids")
for ic,d in AF.items(): ax.scatter(d["lon"],d["lat"],s=5,color="#c2c7d0",zorder=3)
for k,(la,lo) in CENT.items(): ax.scatter(lo,la,s=30,marker="o",facecolor="none",edgecolor="#7a7f8a",lw=0.9,zorder=4)
for lo,la,lab,don,city in HP:
    ax.scatter(lo,la,s=22*don,marker="o",color="# e8772e".replace(" ",""),alpha=0.78,edgecolor="white",lw=0.7,zorder=6)
# The map shows numbers only; full hospital names are in the key below.
# With eighteen hospitals in thirteen cities, full names on the map would
# overlap each other and the city names.
_HPS = sorted(HP, key=lambda x: -x[3])
_NUM = {lab: i + 1 for i, (_, _, lab, _, _) in enumerate(_HPS)}
# Number drawn inside the marker, white with a dark outline. The outline
# keeps the digit legible on any background.
# legible also when the point is small or on a light background.
_OBW_CYFRA = [_pe.withStroke(linewidth=2.4, foreground="#7a3006")]
for lo, la, lab, don, city in _HPS:
    ax.annotate(str(_NUM[lab]), (lo, la), (0, 0), textcoords="offset points",
                fontsize=8.5 if _NUM[lab] < 10 else 8.0, color="white", weight="bold",
                ha="center", va="center", zorder=14, path_effects=_OBW_CYFRA)
# City name printed once per city, under its lowest point,
# so the label is not repeated when a city has several hospitals.
_MIASTA = {}
for lo, la, lab, don, city in _HPS:
    if city not in _MIASTA or la < _MIASTA[city][1]:
        _MIASTA[city] = (lo, la)
# Police lies 15 km from Szczecin, so the two labels overlap.
# The Police label goes above the point; the rest stay below.
_NAD = {"Police"}
for city, (lo, la) in _MIASTA.items():
    _off = (0, 13) if city in _NAD else (0, -16)
    _va = "bottom" if city in _NAD else "top"
    ax.annotate(city, (lo, la), _off, textcoords="offset points", fontsize=8.0,
                color="#8a3d0a", weight="bold", ha="center", va=_va, zorder=8,
                path_effects=_OBW)
# The number key is not baked into the image but written as a table, which
# the supplement includes under the figure, so the text stays selectable.
_SPIS_MD = ["| No. | Hospital | City | Donors 2024 |", "|---|---|---|---|"]
for _lo, _la, _lab, _don, _city in _HPS:
    _SPIS_MD.append(f"| {_NUM[_lab]} | {_lab} | {_city} | {_don} |")
with open(_os.path.join(RESULTS, "donor_hospital_list.md"), "w", encoding="utf-8") as _f:
    _f.write("\n".join(_SPIS_MD) + "\n")
print("  wrote the hospital list to results/donor_hospital_list.md")
for c,(la,lo) in OSR.items():
    # centre marker is offset so it does not sit on the hospital dot
    ax.scatter(lo-0.14,la-0.10,s=85,marker="*",color="#d62728",edgecolor="white",lw=0.6,zorder=7)
_OFFB={"EPBK":((10,10),"left"),"EPBY":((-10,10),"right"),"EPML":((10,-16),"left")}
for ic in ["EPBK","EPBY","EPML"]:
    # base marker is shifted slightly up so the hospital number stays readable
    d=AF[ic];ax.scatter(d["lon"],d["lat"]+0.12,s=190,marker="^",color="#1f77b4",edgecolor="white",lw=1.1,zorder=10)
    _o,_h=_OFFB[ic]
    ax.annotate("BASE "+d["muni"],(d["lon"],d["lat"]+0.12),_o,textcoords="offset points",fontsize=9,color="#0d3b66",weight="bold",ha=_h,zorder=11,path_effects=_OBW)
leg=[Line2D([0],[0],marker="o",color="w",markerfacecolor="#e8772e",markersize=12,label="donor hospital, number = rank by donors, size = donors"),
     Line2D([0],[0],marker="o",color="w",markerfacecolor="none",markeredgecolor="#7a7f8a",markersize=9,label="voivodeship centroid (proxy)"),
     Line2D([0],[0],marker="*",color="w",markerfacecolor="#d62728",markersize=14,label="centre"),
     Line2D([0],[0],marker="^",color="w",markerfacecolor="#1f77b4",markersize=12,label="minimax base")]
ax.legend(handles=leg,loc="lower left",fontsize=8.5,frameon=False)
plt.tight_layout();plt.savefig(_os.path.join(RESULTS, "map_donor_hospitals.png"),dpi=350,bbox_inches="tight");plt.close()
print("OK map hospitals")
