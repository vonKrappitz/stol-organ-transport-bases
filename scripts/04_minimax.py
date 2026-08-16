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

import csv, re, json, math
from itertools import combinations

# audited set AUDYT33 (conservative, after the infrastructure audit)
keep={"small_airport","medium_airport","large_airport"}
ap={}
with open("airports.csv",newline='',encoding="utf-8") as f:
    for r in csv.DictReader(f):
        if r["iso_country"]!="PL" or r["type"] not in keep: continue
        ap[r["ident"]]={"muni":r["municipality"] or r["name"],"icao":r["icao_code"] or r["ident"],
            "lat":float(r["latitude_deg"]),"lon":float(r["longitude_deg"]),"rwys":[]}
HARD=re.compile(r"asph|ashp|aspha|\basp\b|conc|\bcon\b|cement|bitum|tarmac|\btar\b|paved|\bpav|\bpem\b|sealed|\bseal\b|composite|\bcop\b|\bhard\b|macadam|\bpcn\b",re.I)
SOFT=re.compile(r"grass|\bgrs\b|turf|\bgvl\b|gravel|dirt|sand|soil|earth|clay|snow|\bice\b|water|\bsod\b|\bgre\b|unpaved|natural",re.I)
def hard(s):
    if not s: return False
    if SOFT.search(s) and not HARD.search(s): return False
    return bool(HARD.search(s))
with open("runways.csv",newline='',encoding="utf-8") as f:
    for r in csv.DictReader(f):
        a=r["airport_ident"]
        if a not in ap or r["closed"]=="1": continue
        try: ln=int(r["length_ft"])
        except: continue
        ap[a]["rwys"].append((ln,r["surface"]))
AF=[]
for a,d in ap.items():
    h=[ln for ln,s in d["rwys"] if hard(s)]
    if h and max(h)*0.3048>=750:
        AF.append({"icao":d["icao"],"muni":d["muni"],"lat":d["lat"],"lon":d["lon"]})
print("Airfields in the optimum set:",len(AF))

# geo: centroids + centres
g=json.load(open("voivodeship_boundaries.json", encoding="utf-8"))
CENT=g["cent"]; OSR=g["osr"]

# ---------- demand weights, mean 2020-2024 ----------
WD={"dolnośląskie":(2879271,10.0,10.7,7.95,38,53),"kujawsko-pomorskie":(1996003,9.0,9.2,12.43,27,35),
"lubelskie":(2011047,5.0,5.75,7.88,23,22),"lubuskie":(975023,12.0,17.94,14.25,9,21),
"łódzkie":(2362519,4.0,5.36,7.55,15,22),"małopolskie":(3429632,7.0,10.56,11.08,46,54),
"mazowieckie":(5510527,9.0,8.67,10.16,85,101),"opolskie":(936725,10.0,11.30,11.64,11,13),
"podkarpackie":(2071676,4.0,2.84,4.80,13,16),"podlaskie":(1138216,7.0,4.28,15.71,16,27),
"pomorskie":(2359573,20.0,23.87,21.62,67,55),"śląskie":(4320130,13.0,13.64,15.83,73,83),
"świętokrzyskie":(1168499,4.0,5.75,5.92,23,30),"warmińsko-mazurskie":(1357910,19.0,14.89,10.95,23,27),
"wielkopolskie":(3487973,15.0,11.17,15.16,57,67),"zachodniopomorskie":(1631784,13.0,8.32,12.77,40,41)}
def wgt(k):
    p,a,b,c,d,e=WD[k]; return (a*p/1e6+b*p/1e6+c*p/1e6+d+e)/5

# ---------- haversine ----------
def hav(lat1,lon1,lat2,lon2):
    R=6371.0; p1,p2=math.radians(lat1),math.radians(lat2)
    dp=math.radians(lat2-lat1); dl=math.radians(lon2-lon1)
    a=math.sin(dp/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*R*math.asin(math.sqrt(a))

VH,VS=240.0,330.0; STARTUP=5/60  # h ; 104 km zasieg feeder
ORG={"heart":["Gdańsk","Kraków","Poznań","Warszawa","Wrocław","Zabrze"],
"lungs":["Gdańsk","Kraków","Poznań","Szczecin","Warszawa","Zabrze"],
"liver":["Bydgoszcz","Gdańsk","Katowice","Szczecin","Warszawa","Wrocław"]}

def nearest(lat,lon):
    best=None;bd=9e9
    for i,a in enumerate(AF):
        d=hav(lat,lon,a["lat"],a["lon"])
        if d<bd: bd=d;best=i
    return best,bd

# centres -> nearest airfield plus feeder
cair={}
print("\n--- centres: nearest airfield ---")
for c,(la,lo) in OSR.items():
    i,d=nearest(la,lo); cair[c]=(i,d)
    flag=" >104!" if d>104 else ""
    print(f"  {c:11} -> {AF[i]['icao']} {AF[i]['muni'][:18]:18} {d:5.1f} km{flag}")

# sources (centroids) -> nearest airfield, feeder, and the worst eligible centre per organ
print("\n--- sources: nearest airfield + worst target ---")
src=[]
for k,(la,lo) in CENT.items():
    i,d=nearest(la,lo)
    # worst target: max over organs and centres of (transport A_O->A_C)/VS + (feeder C)/VH
    worst=0; wlbl=None
    for g_,cl in ORG.items():
        for c in cl:
            ci,cd=cair[c]
            t=hav(AF[i]["lat"],AF[i]["lon"],AF[ci]["lat"],AF[ci]["lon"])/VS + cd/VH
            if t>worst: worst=t; wlbl=(g_,c)
    src.append({"woj":k,"ai":i,"feeder":d/VH,"helikm":d,"dest":worst,"dlbl":wlbl,"w":wgt(k)})
    fl=" >104!" if d>104 else ""
    print(f"  {k:20} -> {AF[i]['icao']:6} {d:5.1f}km{fl}  worst: {wlbl[0]:7} {wlbl[1]:9} ({worst*60:4.0f} min lot)")

# distance matrix from a base airfield to a source airfield
SA=sorted({s["ai"] for s in src})  # unique source airfields
D=[[hav(AF[b]["lat"],AF[b]["lon"],AF[s["ai"]]["lat"],AF[s["ai"]]["lon"]) for b in range(len(AF))] for s in src]

def minimax(p):
    best=9e9; bestT=None
    for tri in combinations(range(len(AF)),p):
        mx=0
        for si,s in enumerate(src):
            pos=min(D[si][b] for b in tri)/VS
            T=max(s["feeder"], STARTUP+pos)+s["dest"]
            if T>mx: mx=T
            if mx>=best: break
        if mx<best: best=mx; bestT=tri
    return best,bestT

for p in (2,3,4):
    val,tri=minimax(p)
    bases=", ".join(f"{AF[b]['icao']}({AF[b]['muni'][:12]})" for b in tri)
    # which source binds the worst case
    binder=max(src,key=lambda s:max(s["feeder"],STARTUP+min(D[src.index(s)][b] for b in tri)/VS)+s["dest"])
    print(f"\n===== MINIMAX p={p} =====")
    print(f"  Worst flight time (excluding handovers): {val*60:.1f} min  ({val:.2f} h)")
    print(f"  Bases: {bases}")
    if p==3:
        si=src.index(binder)
        pos=min(D[si][b] for b in tri)/VS
        print(f"  Binding voivodeship: {binder['woj']}  (worst target {binder['dlbl'][0]} {binder['dlbl'][1]})")
        print(f"    source feeder {binder['helikm']:.0f}km/{binder['feeder']*60:.0f}min | positioning {pos*VS:.0f}km/{pos*60:.0f}min (startup{'visible' if STARTUP+pos>binder['feeder'] else ' hidden'}) | rest of the flight {binder['dest']*60:.0f}min")
