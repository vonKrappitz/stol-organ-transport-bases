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
# free choice of the source transfer airfield, including the base.
# comparison: OLD (nearest runway) vs NEW (min over all eligible airfields).
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
if "EPBK" in coords and not any(a["icao"]=="EPBK" for a in AF):
    AF.append({"icao":"EPBK","lat":coords["EPBK"][0],"lon":coords["EPBK"][1]})
N=len(AF)
g=json.load(open("voivodeship_boundaries.json", encoding="utf-8")); CENT=g["cent"]; OSR=g["osr"]
VS,VH,STARTUP=330.0,240.0,5/60
HELI_RANGE=100.0  # km, zasieg jednej mission helicopter (sekcja 2.4)
ORG={"heart":["Gdańsk","Kraków","Poznań","Warszawa","Wrocław","Zabrze"],
"lungs":["Gdańsk","Kraków","Poznań","Szczecin","Warszawa","Zabrze"],
"liver":["Bydgoszcz","Gdańsk","Katowice","Szczecin","Warszawa","Wrocław"]}
def hav(a,b,c,d):
    R=6371.0;p1,p2=math.radians(a),math.radians(c);dp=math.radians(c-a);dl=math.radians(d-b)
    x=math.sin(dp/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2;return 2*R*math.asin(math.sqrt(x))

# destination -> nearest airfield (same for both variants; destination leg by helicopter)
def near_ap(la,lo):
    return min(range(N),key=lambda i:hav(la,lo,AF[i]["lat"],AF[i]["lon"]))
cair={c:near_ap(la,lo) for c,(la,lo) in OSR.items()}

# matrix: feeder od sources do airfields a
HELI=[[hav(la,lo,AF[a]["lat"],AF[a]["lon"])/VH for a in range(N)] for (la,lo) in CENT.values()]
# flight from airfield a to the destination airfield (for the given destination)
def leg(a,ci): return hav(AF[a]["lat"],AF[a]["lon"],AF[cair[ci]]["lat"],AF[cair[ci]]["lon"])/VS
# after the destination: destination feeder
def heli_cel(ci,c): 
    la,lo=OSR[c]; return hav(la,lo,AF[cair[ci]]["lat"],AF[cair[ci]]["lon"])/VH

def solve(mode, p=3):
    keys=list(CENT.keys())
    # for each source: OLD -> airfield = nearest runway; NEW -> any a
    nearest_src=[min(range(N),key=lambda a:HELI[si][a]) for si in range(len(keys))]
    best=9e9; bt=None; wsrc=None
    for tri in combinations(range(N),p):
        mx=0; who=None
        for si,k in enumerate(keys):
            # worst organ for that source
            worst_org=0
            for org,centra in ORG.items():
                for c in centra:
                    ci=c
                    if mode=="stary":
                        a=nearest_src[si]
                        pos=min(hav(AF[a]["lat"],AF[a]["lon"],AF[b]["lat"],AF[b]["lon"]) for b in tri)/VS
                        T=max(HELI[si][a],STARTUP+pos)+leg(a,ci)+heli_cel(ci,c)
                    else: # nowy: min po lotniskach W ZASIEGU feeder od sources
                        T=9e9
                        for a in range(N):
                            if HELI[si][a]*VH > HELI_RANGE: continue  # poza zasiegiem helicopter
                            pos=min(hav(AF[a]["lat"],AF[a]["lon"],AF[b]["lat"],AF[b]["lon"]) for b in tri)/VS
                            t=max(HELI[si][a],STARTUP+pos)+leg(a,ci)+heli_cel(ci,c)
                            if t<T: T=t
                        if T==9e9:  # missing airfields w zasiegu -> uzyj najblizszego (fallback jak stary)
                            a=nearest_src[si]
                            pos=min(hav(AF[a]["lat"],AF[a]["lon"],AF[b]["lat"],AF[b]["lon"]) for b in tri)/VS
                            T=max(HELI[si][a],STARTUP+pos)+leg(a,ci)+heli_cel(ci,c)
                    if T>worst_org: worst_org=T
            if worst_org>mx: mx=worst_org; who=k
            if mx>=best: break
        if mx<best: best=mx; bt=tri; wsrc=who
    bz=tuple(sorted(AF[b]["icao"] for b in bt))
    return best*60, bz, wsrc

_r = {}
for mode in ("stary","nowy"):
    v,b,w=solve(mode)
    print(f"{mode:6}: {v:6.1f} min | bases {b} | binds {w}")
    _r[mode] = {"worst_min": round(v, 1), "bases": list(b), "binding": w}

# --- machine-readable results ---
# The supplementary material reports 133.9 min for free choice of the transfer
# airfield. This block computes nothing new, it collects what solve() returned.
import json as _json
with open(_os.path.join(RESULTS, "free_airfield_choice.json"), "w", encoding="utf-8") as _f:
    _json.dump(_r, _f, ensure_ascii=False, indent=2)
print("  saved results/free_airfield_choice.json")
