# -*- coding: utf-8 -*-
# Copyright 2026 Maciej M. Kasperek. Licensed under the Apache License, Version 2.0.
"""
27_lower_bound.py

LOWER BOUND ON THE WORST-CASE MISSION TIME, independent of base placement.

Computes the minimum over all feasible source-destination pairs of the
time that no network of bases, of any cardinality, can go below.
Shows that three bases leave only a small gap to this bound, i.e. most
of the worst-case time is a property of geography, not of the network.
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
# LOWER BOUND ON THE WORST TIME
# =====================================================================
naj = 0.0
opis = None
for si, w in enumerate(WOJ):
    for o in ORG:
        for kj, c in enumerate(VOL[o].keys()):
            T = max(feeder_src[si], ST) + B[o][si][kj]
            if T > naj:
                naj, opis = float(T), (w, c, o)

print()
print("=" * 78)
print("LOWER BOUND ON THE WORST TIME, independent of base placement")
print("=" * 78)
print(f"  lower bound:  {naj*60:6.1f} min")
print(f"  binds:        {opis[0]} -> {opis[1]} ({opis[2]})")
print(f"  optimum p=3:   143.5 min")
print(f"  gap:          {143.5 - naj*60:6.1f} min, i.e. {100*(143.5-naj*60)/143.5:.1f} percent of the result")
print()
print("  Interpretation. No network of bases, of any cardinality, can go below")
print("  this bound. Three bases leave a gap of a dozen-odd minutes to it,")
print("  so the dominant part of the worst-case time is a property of geography.")

import json as _json
with open(_os.path.join(RESULTS, "lower_bound.json"), "w", encoding="utf-8") as f:
    _json.dump({"lower_bound_min": round(naj*60, 1), "binds": list(opis),
                "optimum_p3_min": 143.5, "gap_min": round(143.5 - naj*60, 1)},
               f, ensure_ascii=False, indent=1)
print(f"\n  saved {_os.path.join(RESULTS, 'lower_bound.json')}")
