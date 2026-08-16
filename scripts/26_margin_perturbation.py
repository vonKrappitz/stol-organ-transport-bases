# -*- coding: utf-8 -*-
# Copyright 2026 Maciej M. Kasperek. Licensed under the Apache License, Version 2.0.
"""
26_margin_perturbation.py

MARGIN PERTURBATION TEST.

The source margins are constructed, not observed directly. This script
perturbs every margin by a random factor U[0.8, 1.2] and re-runs the
full Frechet-class optimization (three criteria) 200 times.

Question: does the invariance result and the optimal triple survive
margin error, or is it an artifact of the constructed margins?
"""
# paths relative to the repository root
import os as _os
try:
    _SKRYPT_DIR = _os.path.dirname(_os.path.abspath(__file__))
except NameError:
    _SKRYPT_DIR = _os.path.dirname(_os.path.abspath(_os.sys.argv[0])) or _os.getcwd()
_REPO_DIR = _os.path.dirname(_SKRYPT_DIR)
_DANE_DIR = _os.path.join(_REPO_DIR, "data")
RESULTS = _os.path.join(_REPO_DIR, "results")
_os.makedirs(RESULTS, exist_ok=True)
_os.chdir(_DANE_DIR)
# end of path block

import csv, re, json, math
from itertools import combinations
import numpy as np
from scipy.optimize import linprog

# ---------- data: identical to 05_compare_methods.py ----------
keep = {"small_airport", "medium_airport", "large_airport"}
ap = {}
with open("airports.csv", newline='', encoding="utf-8") as f:
    for r in csv.DictReader(f):
        if r["iso_country"] != "PL" or r["type"] not in keep: continue
        ap[r["ident"]] = {"muni": r["municipality"] or r["name"],
                          "icao": r["icao_code"] or r["ident"],
                          "lat": float(r["latitude_deg"]), "lon": float(r["longitude_deg"])}

_TROJKA = ["EPBY", "EPML", "EPSY"]
_CERT13 = ["EPWA", "EPGD", "EPKT", "EPKK", "EPLL", "EPPO", "EPRZ", "EPSC", "EPMO", "EPWR", "EPZG", "EPLB", "EPRA"]
_ad4k = [r["icao"] for r in csv.DictReader(open("airfield_audit_thresholds.csv", encoding="utf-8")) if r["prog_kons"] == "1"]
AUDYT33 = sorted(set(_TROJKA + _CERT13 + _ad4k))
AF = [{"icao": d["icao"], "muni": d["muni"], "lat": d["lat"], "lon": d["lon"]}
      for a, d in ap.items() if d["icao"] in AUDYT33]
for _ic in set(AUDYT33) - {a["icao"] for a in AF}:
    for a, d in ap.items():
        if d["icao"] == _ic:
            AF.append({"icao": _ic, "muni": d["muni"], "lat": d["lat"], "lon": d["lon"]})
assert len(AF) == 33, len(AF)

g = json.load(open("voivodeship_boundaries.json", encoding="utf-8")); CENT = g["cent"]; OSR = g["osr"]
WD = {"dolnośląskie": (2879271, 10.0, 10.7, 7.95, 38, 53), "kujawsko-pomorskie": (1996003, 9.0, 9.2, 12.43, 27, 35),
      "lubelskie": (2011047, 5.0, 5.75, 7.88, 23, 22), "lubuskie": (975023, 12.0, 17.94, 14.25, 9, 21),
      "łódzkie": (2362519, 4.0, 5.36, 7.55, 15, 22), "małopolskie": (3429632, 7.0, 10.56, 11.08, 46, 54),
      "mazowieckie": (5510527, 9.0, 8.67, 10.16, 85, 101), "opolskie": (936725, 10.0, 11.30, 11.64, 11, 13),
      "podkarpackie": (2071676, 4.0, 2.84, 4.80, 13, 16), "podlaskie": (1138216, 7.0, 4.28, 15.71, 16, 27),
      "pomorskie": (2359573, 20.0, 23.87, 21.62, 67, 55), "śląskie": (4320130, 13.0, 13.64, 15.83, 73, 83),
      "świętokrzyskie": (1168499, 4.0, 5.75, 5.92, 23, 30), "warmińsko-mazurskie": (1357910, 19.0, 14.89, 10.95, 23, 27),
      "wielkopolskie": (3487973, 15.0, 11.17, 15.16, 57, 67), "zachodniopomorskie": (1631784, 13.0, 8.32, 12.77, 40, 41)}
def wgt(k):
    p, a, b, c, d, e = WD[k]; return (a * p / 1e6 + b * p / 1e6 + c * p / 1e6 + d + e) / 5
def hav(a, b, c, d):
    R = 6371.0; p1, p2 = math.radians(a), math.radians(c)
    dp = math.radians(c - a); dl = math.radians(d - b)
    x = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(x))
VH, VS, ST = 240.0, 330.0, 5 / 60
VOL = {"heart": {"Gdańsk": 16, "Kraków": 14, "Poznań": 8, "Warszawa": 67, "Wrocław": 49, "Zabrze": 48},
       "lungs": {"Gdańsk": 48, "Kraków": 2, "Poznań": 7, "Szczecin": 4, "Warszawa": 26, "Zabrze": 60},
       "liver": {"Bydgoszcz": 39, "Gdańsk": 75, "Katowice": 50, "Szczecin": 78, "Warszawa": 365, "Wrocław": 7}}
def near(la, lo):
    bi, bd = 0, 9e9
    for i, a in enumerate(AF):
        x = hav(la, lo, a["lat"], a["lon"])
        if x < bd: bd = x; bi = i
    return bi, bd
cair = {c: near(la, lo) for c, (la, lo) in OSR.items()}

WOJ = list(CENT.keys())
sair = {k: near(la, lo) for k, (la, lo) in CENT.items()}

# ---------- margins ----------
# d_i : donor count of the voivodeship (mean 2020-2024)
D = np.array([wgt(k) for k in WOJ])
# r_k^o : transplant volume of centre k for organ o
ORG = list(VOL.keys())
# donors are split across organs proportionally to the organ share,
# so that row and column sums close in every Frechet set
Rtot = {o: sum(VOL[o].values()) for o in ORG}
TOT = sum(Rtot.values())

print("=" * 78)
print("MARGINS (observed)")
print("=" * 78)
print(f"  sources: {len(WOJ)} voivodeships, donors in total {D.sum():.1f}/year")
for o in ORG:
    print(f"  {o:8}: {len(VOL[o])} centres, volume {Rtot[o]}")
print(f"  total volume {TOT}")

# ---------- times ----------
# A_i(x) = max(feeder_i, ST + positioning_i(x))   [depends on x, not on k,o]
# B_ik   = flight(a(i)->c(k)) + feeder_k            [depends on (i,k), not on x]
feeder_src = np.array([sair[k][1] / VH for k in WOJ])
Dist_base = np.array([[hav(AF[b]["lat"], AF[b]["lon"], AF[sair[k][0]]["lat"], AF[sair[k][0]]["lon"])
                       for b in range(len(AF))] for k in WOJ])

B = {}
for o in ORG:
    ks = list(VOL[o].keys())
    M = np.zeros((len(WOJ), len(ks)))
    for ii, w in enumerate(WOJ):
        ai = sair[w][0]
        for kk, c in enumerate(ks):
            ci, cd = cair[c]
            M[ii, kk] = hav(AF[ai]["lat"], AF[ai]["lon"], AF[ci]["lat"], AF[ci]["lon"]) / VS + cd / VH
    B[o] = M

def A_of(tri):
    pos = Dist_base[:, list(tri)].min(axis=1) / VS
    return np.maximum(feeder_src, ST + pos)

# ---------- Frechet set: bounds over the coupling ----------
def frechet_extremum(Bo, d_o, r_o, sense):
    """max lub min sum_ik q_ik B_ik po politopie transportowym."""
    n, m = Bo.shape
    c = Bo.reshape(-1)
    if sense == "max": c = -c
    Aeq = []
    beq = []
    for i in range(n):
        row = np.zeros(n * m); row[i * m:(i + 1) * m] = 1
        Aeq.append(row); beq.append(d_o[i])
    for j in range(m):
        row = np.zeros(n * m); row[j::m] = 1
        Aeq.append(row); beq.append(r_o[j])
    res = linprog(c, A_eq=np.array(Aeq), b_eq=np.array(beq), bounds=(0, None), method="highs")
    assert res.success, res.message
    return (-res.fun if sense == "max" else res.fun)


# =====================================================================
# MARGIN PERTURBATION
# =====================================================================
import numpy as _np

LOSOWAN = 200
_rng = _np.random.default_rng(20260804)

def trojki_dla(D_p, VOL_p):
    Rtot_p = {o: sum(VOL_p[o].values()) for o in ORG}
    TOT_p = sum(Rtot_p.values())
    Bmx, Bmn, Bin = {}, {}, {}
    for o in ORG:
        ks = list(VOL_p[o].keys())
        d_o = D_p * (Rtot_p[o] / D_p.sum())
        r_o = _np.array([VOL_p[o][c] for c in ks], dtype=float)
        Bmx[o] = frechet_extremum(B[o], d_o, r_o, "max")
        Bmn[o] = frechet_extremum(B[o], d_o, r_o, "min")
        q_ind = _np.outer(d_o, r_o) / r_o.sum()
        Bin[o] = float((q_ind * B[o]).sum())
    sBmx, sBmn, sBin = sum(Bmx.values()), sum(Bmn.values()), sum(Bin.values())
    Dt = D_p.sum()
    najl = {"dro": (9e9, None), "ind": (9e9, None), "opt": (9e9, None)}
    for tri in combinations(range(len(AF)), 3):
        A = A_of(tri)
        core = float((D_p * A).sum()) * (TOT_p / Dt)
        for kl, sB in (("dro", sBmx), ("ind", sBin), ("opt", sBmn)):
            v = (core + sB) / TOT_p
            if v < najl[kl][0]: najl[kl] = (v, tri)
    return {k: v[1] for k, v in najl.items()}

baza = trojki_dla(D, VOL)
assert baza["dro"] == baza["ind"] == baza["opt"], baza
print()
print("=" * 78)
print(f"MARGIN PERTURBATION: {LOSOWAN} draws, each margin times U[0.8, 1.2]")
print("=" * 78)
print(f"  triple without perturbation: {', '.join(sorted(AF[b]['muni'] for b in baza['dro']))}")

zgodne = 0
ta_sama = 0
for _ in range(LOSOWAN):
    D_p = D * _rng.uniform(0.8, 1.2, size=D.shape)
    VOL_p = {o: {c: v * float(_rng.uniform(0.8, 1.2)) for c, v in VOL[o].items()} for o in ORG}
    t = trojki_dla(D_p, VOL_p)
    if t["dro"] == t["ind"] == t["opt"]:
        zgodne += 1
        if t["dro"] == baza["dro"]: ta_sama += 1

print(f"  invariance held (three criteria agree): {zgodne}/{LOSOWAN}")
print(f"  same triple as without perturbation:                {ta_sama}/{LOSOWAN}")

import json as _json
with open(_os.path.join(RESULTS, "margin_perturbation.json"), "w", encoding="utf-8") as f:
    _json.dump({"draws": LOSOWAN, "range": [0.8, 1.2],
                "invariance_held": zgodne,
                "same_triple": ta_sama,
                "base_triple": sorted(AF[b]["muni"] for b in baza["dro"])}, f, ensure_ascii=False, indent=1)
print(f"\n  saved {_os.path.join(RESULTS, 'margin_perturbation.json')}")
