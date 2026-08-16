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

# -*- coding: utf-8 -*-
# minimax on three source sets
# (16 centroids / 18 hospitals / 34 combined), same airfield set AUDYT33
import csv, json, math
from itertools import combinations

CERT13=["EPWA","EPGD","EPKT","EPKK","EPLL","EPPO","EPRZ","EPSC","EPMO","EPWR","EPZG","EPLB","EPRA"]
TROJKA=["EPBY","EPML","EPSY"]
ad4={r["icao"]:r for r in csv.DictReader(open("airfield_audit_thresholds.csv", encoding="utf-8"))}
AUD=sorted(set(TROJKA+CERT13+[ic for ic,r in ad4.items() if r["prog_kons"]=="1"]))
coords={}
for r in csv.DictReader(open("airports.csv",encoding="utf-8")):
    ic=r["icao_code"] or r["ident"]
    if ic in AUD or ic=="EPBK": coords[ic]=(float(r["latitude_deg"]),float(r["longitude_deg"]))
AF=[{"icao":ic,"lat":coords[ic][0],"lon":coords[ic][1]} for ic in AUD if ic in coords]
if "EPBK" in coords and not any(a["icao"]=="EPBK" for a in AF): AF.append({"icao":"EPBK","lat":coords["EPBK"][0],"lon":coords["EPBK"][1]})

g=json.load(open("voivodeship_boundaries.json", encoding="utf-8")); CENT=g["cent"]; OSR=g["osr"]
VS,VH,STARTUP=330.0,240.0,5/60
ORG={"heart":["Gdańsk","Kraków","Poznań","Warszawa","Wrocław","Zabrze"],
"lungs":["Gdańsk","Kraków","Poznań","Szczecin","Warszawa","Zabrze"],
"liver":["Bydgoszcz","Gdańsk","Katowice","Szczecin","Warszawa","Wrocław"]}
def hav(a,b,c,d):
    R=6371.0;p1,p2=math.radians(a),math.radians(c);dp=math.radians(c-a);dl=math.radians(d-b)
    x=math.sin(dp/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2;return 2*R*math.asin(math.sqrt(x))

# hospital city coordinates (public, hard-coded so no network is needed)
CITY={"Kraków":(50.0647,19.9450),"Kielce":(50.8661,20.6286),"Gdańsk":(54.3520,18.6466),
"Warszawa":(52.2297,21.0122),"Katowice":(50.2649,19.0238),"Szczecin":(53.4285,14.5528),
"Białystok":(53.1325,23.1688),"Police":(53.5524,14.5721),"Wrocław":(51.1079,17.0385),
"Olsztyn":(53.7784,20.4801),"Rzeszów":(50.0413,21.9990),"Poznań":(52.4064,16.9252),
"Konin":(52.2230,18.2512),"Zielona Góra":(51.9356,15.5062)}
# 18 hospitals (city, donors)
H=[("Kraków",27),("Kielce",25),("Gdańsk",24),("Warszawa",23),("Katowice",23),("Szczecin",17),
("Białystok",16),("Warszawa",14),("Police",14),("Wrocław",13),("Wrocław",13),("Gdańsk",11),
("Olsztyn",11),("Rzeszów",10),("Wrocław",10),("Poznań",10),("Konin",10),("Zielona Góra",10)]

def near(la,lo):
    return min(range(len(AF)),key=lambda i:hav(la,lo,AF[i]["lat"],AF[i]["lon"]))
cair={c:near(la,lo) for c,(la,lo) in OSR.items()}

def worst_for_source(la,lo,tri):
    i=near(la,lo); heli=hav(la,lo,AF[i]["lat"],AF[i]["lon"])/VH
    pos=min(hav(AF[i]["lat"],AF[i]["lon"],AF[b]["lat"],AF[b]["lon"]) for b in tri)/VS
    w=0
    for org,cs in ORG.items():
        for c in cs:
            ci=cair[c]; leg=hav(AF[i]["lat"],AF[i]["lon"],AF[ci]["lat"],AF[ci]["lon"])/VS
            hc=hav(OSR[c][0],OSR[c][1],AF[ci]["lat"],AF[ci]["lon"])/VH
            T=max(heli,STARTUP+pos)+leg+hc
            if T>w: w=T
    return w

def solve(sources, p=3):
    # sources: lista (nazwa, lat, lon)
    best=9e9; bt=None; wsrc=None
    for tri in combinations(range(len(AF)),p):
        mx=0; who=None
        for name,la,lo in sources:
            t=worst_for_source(la,lo,tri)
            if t>mx: mx=t; who=name
            if mx>=best: break
        if mx<best: best=mx; bt=tri; wsrc=who
    return best*60, tuple(sorted(AF[b]["icao"] for b in bt)), wsrc

# set 1: 16 centroids
S16=[(k,la,lo) for k,(la,lo) in CENT.items()]
# set 2: 18 hospitals
S18=[(f"{c}#{i}",*CITY[c]) for i,(c,_) in enumerate(H)]
# set 3: combined 34
S34=S16+S18

for name,src in [("16 centroids",S16),("18 hospitals",S18),("34 laczony",S34)]:
    v,b,w=solve(src)
    print(f"{name:16}: {v:6.1f} min | bases {b} | binds {w}")
