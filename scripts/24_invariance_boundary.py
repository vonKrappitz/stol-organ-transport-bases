# -*- coding: utf-8 -*-
# Copyright 2026 Maciej M. Kasperek. Licensed under the Apache License, Version 2.0.
"""
24_invariance_boundary.py

BOUNDARY TEST OF THE INVARIANCE THEOREM.

In the main variant, the transfer airfield is always the nearest to the source,
so time decomposes as T_ik(x) = A_i(x) + B_ik and location is invariant
with respect to the coupling (script 23).

Here we check the FREE CHOICE variant of the transfer airfield among all
within range of one helicopter mission. Then the airfield choice depends
SIMULTANEOUSLY on the base triple and on the destination, so the decomposition
breaks. Question: does invariance fail with it, or only its proof?
"""
# paths relative to the repository root
import os as _os
try:
    _SCRIPT_DIR = _os.path.dirname(_os.path.abspath(__file__))
except NameError:
    _SCRIPT_DIR = _os.path.dirname(_os.path.abspath("24_invariance_boundary.py"))
_REPO_DIR = _os.path.dirname(_SCRIPT_DIR)
_DATA_DIR = _os.path.join(_REPO_DIR, "data")
RESULTS = _os.path.join(_REPO_DIR, "results")
_os.makedirs(RESULTS, exist_ok=True)
_os.chdir(_DATA_DIR)
# end of path block

import csv, re, json, math, time
from itertools import combinations
import numpy as np
from scipy.optimize import linprog

keep = {"small_airport", "medium_airport", "large_airport"}
ap = {}
with open("airports.csv", newline='', encoding="utf-8") as f:
    for r in csv.DictReader(f):
        if r["iso_country"] != "PL" or r["type"] not in keep: continue
        ap[r["ident"]] = {"muni": r["municipality"] or r["name"], "icao": r["icao_code"] or r["ident"],
                          "lat": float(r["latitude_deg"]), "lon": float(r["longitude_deg"])}
_TROJKA = ["EPBY", "EPML", "EPSY"]
_CERT13 = ["EPWA", "EPGD", "EPKT", "EPKK", "EPLL", "EPPO", "EPRZ", "EPSC", "EPMO", "EPWR", "EPZG", "EPLB", "EPRA"]
_ad4k = [r["icao"] for r in csv.DictReader(open("airfield_audit_thresholds.csv", encoding="utf-8")) if r["prog_kons"] == "1"]
AUDYT33 = sorted(set(_TROJKA + _CERT13 + _ad4k))
AF = [{"icao": d["icao"], "muni": d["muni"], "lat": d["lat"], "lon": d["lon"]} for a, d in ap.items() if d["icao"] in AUDYT33]
for _ic in set(AUDYT33) - {a["icao"] for a in AF}:
    for a, d in ap.items():
        if d["icao"] == _ic: AF.append({"icao": _ic, "muni": d["muni"], "lat": d["lat"], "lon": d["lon"]})
assert len(AF) == 33
g = json.load(open("voivodeship_boundaries.json", encoding="utf-8")); CENT = g["cent"]; OSR = g["osr"]
WD = {"dolnośląskie": (2879271,10.0,10.7,7.95,38,53), "kujawsko-pomorskie": (1996003,9.0,9.2,12.43,27,35),
"lubelskie": (2011047,5.0,5.75,7.88,23,22), "lubuskie": (975023,12.0,17.94,14.25,9,21),
"łódzkie": (2362519,4.0,5.36,7.55,15,22), "małopolskie": (3429632,7.0,10.56,11.08,46,54),
"mazowieckie": (5510527,9.0,8.67,10.16,85,101), "opolskie": (936725,10.0,11.30,11.64,11,13),
"podkarpackie": (2071676,4.0,2.84,4.80,13,16), "podlaskie": (1138216,7.0,4.28,15.71,16,27),
"pomorskie": (2359573,20.0,23.87,21.62,67,55), "śląskie": (4320130,13.0,13.64,15.83,73,83),
"świętokrzyskie": (1168499,4.0,5.75,5.92,23,30), "warmińsko-mazurskie": (1357910,19.0,14.89,10.95,23,27),
"wielkopolskie": (3487973,15.0,11.17,15.16,57,67), "zachodniopomorskie": (1631784,13.0,8.32,12.77,40,41)}
def wgt(k):
    p,a,b,c,d,e = WD[k]; return (a*p/1e6 + b*p/1e6 + c*p/1e6 + d + e)/5
def hav(a,b,c,d):
    R=6371.0; p1,p2=math.radians(a),math.radians(c); dp=math.radians(c-a); dl=math.radians(d-b)
    x=math.sin(dp/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2; return 2*R*math.asin(math.sqrt(x))
VH, VS, ST = 240.0, 330.0, 5/60
HELI_RANGE = 100.0
VOL = {"heart": {"Gdańsk":16,"Kraków":14,"Poznań":8,"Warszawa":67,"Wrocław":49,"Zabrze":48},
       "lungs": {"Gdańsk":48,"Kraków":2,"Poznań":7,"Szczecin":4,"Warszawa":26,"Zabrze":60},
       "liver": {"Bydgoszcz":39,"Gdańsk":75,"Katowice":50,"Szczecin":78,"Warszawa":365,"Wrocław":7}}
def near(la,lo):
    bi,bd=0,9e9
    for i,a in enumerate(AF):
        x=hav(la,lo,a["lat"],a["lon"])
        if x<bd: bd=x; bi=i
    return bi,bd
cair={c:near(la,lo) for c,(la,lo) in OSR.items()}
WOJ=list(CENT.keys()); ORG=list(VOL.keys())
D=np.array([wgt(k) for k in WOJ])
Rtot={o:sum(VOL[o].values()) for o in ORG}; TOT=sum(Rtot.values())

# helicopter range: airfields within HELI_RANGE of the source
reach={}; feed={}
for ii,w in enumerate(WOJ):
    la,lo=CENT[w]; R=[];F=[]
    for a in range(len(AF)):
        d=hav(la,lo,AF[a]["lat"],AF[a]["lon"])
        if d<=HELI_RANGE: R.append(a); F.append(d/VH)
    reach[ii]=np.array(R,dtype=int); feed[ii]=np.array(F)
SL={}
for o in ORG:
    ks=list(VOL[o].keys()); M=np.zeros((len(AF),len(ks)))
    for a in range(len(AF)):
        for kk,c in enumerate(ks):
            ci,cd=cair[c]
            M[a,kk]=hav(AF[a]["lat"],AF[a]["lon"],AF[ci]["lat"],AF[ci]["lon"])/VS + cd/VH
    SL[o]=M
DB=np.array([[hav(AF[b]["lat"],AF[b]["lon"],AF[a]["lat"],AF[a]["lon"]) for a in range(len(AF))] for b in range(len(AF))])

def T_free(tri):
    """matrix czasow przy free wyborze airfields przesiadki"""
    pos=DB[list(tri),:].min(axis=0)/VS
    out={}
    for o in ORG:
        M=np.zeros((len(WOJ),len(VOL[o])))
        for ii in range(len(WOJ)):
            R=reach[ii]
            lhs=np.maximum(feed[ii], ST+pos[R])
            M[ii]=(lhs[:,None]+SL[o][R,:]).min(axis=0)
        out[o]=M
    return out

MARG={}
for o in ORG:
    ks=list(VOL[o].keys())
    MARG[o]=(D*(Rtot[o]/D.sum()), np.array([VOL[o][c] for c in ks],float))

def frechet(T,d_o,r_o,sense):
    n,m=T.shape; c=T.reshape(-1).copy()
    if sense=="max": c=-c
    Aeq=np.zeros((n+m,n*m))
    for i in range(n): Aeq[i,i*m:(i+1)*m]=1
    for j in range(m): Aeq[n+j,j::m]=1
    beq=np.concatenate([d_o,r_o])
    res=linprog(c,A_eq=Aeq,b_eq=beq,bounds=(0,None),method="highs")
    assert res.success
    return -res.fun if sense=="max" else res.fun

print("="*78)
print("BOUNDARY TEST: variant FREE choice of transfer airfield")
print("="*78)
print(f"  airfields within reach of sources: min {min(len(v) for v in reach.values())}, "
      f"mediana {int(np.median([len(v) for v in reach.values()]))}, maks {max(len(v) for v in reach.values())}")

best={"max":(9e9,None),"ind":(9e9,None),"min":(9e9,None)}
t0=time.time()
for n,tri in enumerate(combinations(range(len(AF)),3)):
    T=T_free(tri)
    v={"max":0.0,"ind":0.0,"min":0.0}
    for o in ORG:
        d_o,r_o=MARG[o]
        v["max"]+=frechet(T[o],d_o,r_o,"max")
        v["min"]+=frechet(T[o],d_o,r_o,"min")
        q_ind=np.outer(d_o,r_o)/r_o.sum()
        v["ind"]+=float((q_ind*T[o]).sum())
    for k in v:
        val=v[k]/TOT
        if val<best[k][0]: best[k]=(val,tri)
print(f"  compute time: {time.time()-t0:.0f} s")

def nm(t): return ", ".join(sorted(AF[b]["muni"] for b in t))
print()
for k,lab in [("max","min-max (robust)"),("ind","independence (proxy)"),("min","min-min (optimistic)")]:
    v,tri=best[k]; print(f"  {lab:26}: {v*60:6.1f} min | bases {nm(tri)}")

same = best["max"][1]==best["ind"][1]==best["min"][1]
print()
print("="*78)
print(f"  INVARIANCE IN THE FREE CHOICE VARIANT: {same}")
print("="*78)
if not same:
    print("  Triples DIFFER -> the theorem has boundaries, the chain structure")
    print("  condition is ESSENTIAL, not merely convenient for the proof.")
    # how much worse is the robust triple on the proxy criterion?
    tri_ind=best["ind"][1]; tri_max=best["max"][1]
    T=T_free(tri_ind); v_ind_at_ind=0.0
    for o in ORG:
        d_o,r_o=MARG[o]; q=np.outer(d_o,r_o)/r_o.sum(); v_ind_at_ind+=float((q*T[o]).sum())
    T=T_free(tri_max); v_ind_at_max=0.0
    for o in ORG:
        d_o,r_o=MARG[o]; q=np.outer(d_o,r_o)/r_o.sum(); v_ind_at_max+=float((q*T[o]).sum())
    print(f"  cost of robustness: robust triple on proxy criterion {v_ind_at_max/TOT*60:.1f} min")
    print(f"                    proxy triple on proxy criterion {v_ind_at_ind/TOT*60:.1f} min")
    print(f"                    difference {abs(v_ind_at_max-v_ind_at_ind)/TOT*60:.2f} min")
else:
    print("  Triples ARE THE SAME -> invariance extends further than its proof,")
    print("  which is itself a result worth reporting.")

out={"variant":"free choice airfields","invariance":bool(same),
     "bases_max":[AF[b]["icao"] for b in best["max"][1]],
     "bases_ind":[AF[b]["icao"] for b in best["ind"][1]],
     "bases_min":[AF[b]["icao"] for b in best["min"][1]],
     "min_max_min":best["max"][0]*60,"ind_min":best["ind"][0]*60,"min_min_min":best["min"][0]*60}
with open(_os.path.join(RESULTS,"invariance_boundary.json"),"w",encoding="utf-8") as f:
    json.dump(out,f,ensure_ascii=False,indent=1)
print("\n  written results/invariance_boundary.json")
