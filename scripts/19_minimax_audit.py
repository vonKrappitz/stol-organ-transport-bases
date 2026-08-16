# Copyright 2026 Maciej M. Kasperek. Licensed under the Apache License, Version 2.0.
# paths relative to the repository root
import os as _os
try:
    _SKRYPT_DIR = _os.path.dirname(_os.path.abspath(__file__))
except NameError:
    _SKRYPT_DIR = _os.path.dirname(_os.path.abspath(_os.sys.argv[0])) or _os.getcwd()
_REPRO_DIR  = _os.path.dirname(_SKRYPT_DIR)          # reprodukcja_VI/
_DANE_DIR   = _os.path.join(_REPRO_DIR, "data")
RESULTS      = _os.path.join(_REPRO_DIR, "results")     # figury i CSV tu
_os.makedirs(RESULTS, exist_ok=True)
_os.chdir(_DANE_DIR)                                  # gole sciezki czytaja z dane/
# end of path block

# -*- coding: utf-8 -*-
# minimax p-center on the audited set (snapshot 2026-07-18)
import csv, json, math
from itertools import combinations

TROJKA=["EPBY","EPML","EPSY"]
CERT13=["EPWA","EPGD","EPKT","EPKK","EPLL","EPPO","EPRZ","EPSC","EPMO","EPWR","EPZG","EPLB","EPRA"]
CERT_H24=["EPWA","EPGD","EPKT","EPKK","EPRZ","EPMO","EPWR"]  # bez EPPO (okna wojskowe)
ad4b=[]; ad4k=[]
for r in csv.DictReader(open("airfield_audit_thresholds.csv", encoding="utf-8")):
    if r["prog_baza"]=="1": ad4b.append(r["icao"])
    if r["prog_kons"]=="1": ad4k.append(r["icao"])
MIL=[r["icao"] for r in csv.DictReader(open("airfield_audit_military.csv", encoding="utf-8")) if r["prog_baza"]=="1"]

coords={}
for r in csv.DictReader(open("airports.csv",encoding="utf-8")):
    ic=r["icao_code"] or r["ident"]
    if ic.startswith("EP"): coords[ic]={"muni":r["municipality"] or r["name"],
        "lat":float(r["latitude_deg"]),"lon":float(r["longitude_deg"])}

def zbior(icaos):
    out=[]; brak=[]
    for ic in icaos:
        if ic in coords: out.append({"icao":ic,**coords[ic]})
        else: brak.append(ic)
    if brak: print("  ! missing coordinates:",brak)
    return out

g=json.load(open("voivodeship_boundaries.json", encoding="utf-8")); CENT=g["cent"]; OSR=g["osr"]
WD={"dolnośląskie":(2879271,10.0,10.7,7.95,38,53),"kujawsko-pomorskie":(1996003,9.0,9.2,12.43,27,35),
"lubelskie":(2011047,5.0,5.75,7.88,23,22),"lubuskie":(975023,12.0,17.94,14.25,9,21),
"łódzkie":(2362519,4.0,5.36,7.55,15,22),"małopolskie":(3429632,7.0,10.56,11.08,46,54),
"mazowieckie":(5510527,9.0,8.67,10.16,85,101),"opolskie":(936725,10.0,11.30,11.64,11,13),
"podkarpackie":(2071676,4.0,2.84,4.80,13,16),"podlaskie":(1138216,7.0,4.28,15.71,16,27),
"pomorskie":(2359573,20.0,23.87,21.62,67,55),"śląskie":(4320130,13.0,13.64,15.83,73,83),
"świętokrzyskie":(1168499,4.0,5.75,5.92,23,30),"warmińsko-mazurskie":(1357910,19.0,14.89,10.95,23,27),
"wielkopolskie":(3487973,15.0,11.17,15.16,57,67),"zachodniopomorskie":(1631784,13.0,8.32,12.77,40,41)}
def hav(a,b,c,d):
    R=6371.0;p1,p2=math.radians(a),math.radians(c)
    dp=math.radians(c-a);dl=math.radians(d-b)
    x=math.sin(dp/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*R*math.asin(math.sqrt(x))
VH,VS=240.0,330.0; STARTUP=5/60
ORG={"heart":["Gdańsk","Kraków","Poznań","Warszawa","Wrocław","Zabrze"],
"lungs":["Gdańsk","Kraków","Poznań","Szczecin","Warszawa","Zabrze"],
"liver":["Bydgoszcz","Gdańsk","Katowice","Szczecin","Warszawa","Wrocław"]}

def run(nazwa,AF,ps=(2,3,4)):
    print(f"\n########## SCENARIO: {nazwa} | airfields: {len(AF)} ##########")
    def nearest(la,lo):
        bi,bd=None,9e9
        for i,a in enumerate(AF):
            d=hav(la,lo,a["lat"],a["lon"])
            if d<bd: bd,bi=d,i
        return bi,bd
    cair={c:nearest(la,lo) for c,(la,lo) in OSR.items()}
    src=[]
    for k,(la,lo) in CENT.items():
        i,d=nearest(la,lo)
        worst=0;wl=None
        for g_,cl in ORG.items():
            for c in cl:
                ci,cd=cair[c]
                t=hav(AF[i]["lat"],AF[i]["lon"],AF[ci]["lat"],AF[ci]["lon"])/VS+cd/VH
                if t>worst: worst,wl=t,(g_,c)
        src.append({"woj":k,"ai":i,"heli":d/VH,"dest":worst,"dlbl":wl})
    D=[[hav(AF[b]["lat"],AF[b]["lon"],AF[s["ai"]]["lat"],AF[s["ai"]]["lon"]) for b in range(len(AF))] for s in src]
    wyn={}
    for p in ps:
        best=9e9;bt=None
        for tri in combinations(range(len(AF)),p):
            mx=0
            for si,s in enumerate(src):
                pos=min(D[si][b] for b in tri)/VS
                T=max(s["heli"],STARTUP+pos)+s["dest"]
                if T>mx: mx=T
                if mx>=best: break
            if mx<best: best,bt=mx,tri
        bz=", ".join(f"{AF[b]['icao']}({AF[b]['muni'][:12]})" for b in bt)
        wi=max(range(len(src)),key=lambda si:max(src[si]["heli"],STARTUP+min(D[si][b] for b in bt)/VS)+src[si]["dest"])
        print(f"  p={p}: {best*60:6.1f} min | bases: {bz} | binds: {src[wi]['woj']} ({src[wi]['dlbl'][0]} {src[wi]['dlbl'][1]})")
        wyn[p]=(best*60,bz)
    return wyn

S={}
S["S1 civil base set (triple+13cert+AD4 base)"]=zbior(sorted(set(TROJKA+CERT13+ad4b)))
S["S2 conservative (triple+13cert+AD4 cons)"]=zbior(sorted(set(TROJKA+CERT13+ad4k)))
# S1b: base set without the conditional airfield at Pila. It is a former
# military field that the audit flags for point verification (surface data
# from an external base, no Jet A-1, no night in the eAIP). The supplementary
# material reports this variant, so the script must compute it.
S["S1b base set without conditional EPPI"]=zbior(sorted(set(TROJKA+CERT13+ad4b)-{"EPPI"}))
S["S3 night H24 (7 cert H24)"]=zbior(CERT_H24)
S["S4 civil+MIL (S1+14 military)"]=zbior(sorted(set(TROJKA+CERT13+ad4b+MIL)))
wyniki={n:run(n,af) for n,af in S.items()}
print("\n===== SUMMARY p=3 (reference: 143.0 min on the old set of 51) =====")
for n,w in wyniki.items():
    print(f"  {n:48} {w[3][0]:6.1f} min")

# save results in machine-readable form
_a = {}
for _n, _w in wyniki.items():
    _a[_n] = {"airfields": len(S[_n]),
              "p": {str(_p): {"worst_min": round(_v, 1), "bases": _bz}
                    for _p, (_v, _bz) in _w.items()}}
with open(_os.path.join(RESULTS, "minimax_audit.json"), "w", encoding="utf-8") as _f:
    json.dump(_a, _f, ensure_ascii=False, indent=2)
print(f"  saved results/minimax_audit.json ({len(_a)} scenarios)")
