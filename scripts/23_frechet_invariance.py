# -*- coding: utf-8 -*-
# Copyright 2026 Maciej M. Kasperek. Licensed under the Apache License, Version 2.0.
"""
23_frechet_invariance.py

Base location with PARTIALLY IDENTIFIED source-destination matrix.

Margins are observed (donor counts per voivodeship, transplant volumes
per centre and organ), but the coupling between them is not observed.
Instead of choosing one coupling (product = independence), we take the
ENTIRE Frechet class of all matrices consistent with the margins and compute:

  - upper bound  max_{q in Q} E_q[T(x)]   (worst coupling)
  - lower bound  min_{q in Q} E_q[T(x)]   (best coupling)
  - value for the independence coupling (current proxy of the paper)

and solve the robust model  min_x max_{q in Q} E_q[T(x)].

Verifies the INVARIANCE THEOREM: in a chain where the base affects only
the positioning leg, argmin is the same for every coupling.
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

print()
print("=" * 78)
print("BOUNDS OVER THE FRECHET CLASS, component B (independent of base location)")
print("=" * 78)
Bmax = {}; Bmin = {}; Bind = {}
for o in ORG:
    ks = list(VOL[o].keys())
    d_o = D * (Rtot[o] / D.sum())          # donors assigned to organ
    r_o = np.array([VOL[o][c] for c in ks], dtype=float)
    assert abs(d_o.sum() - r_o.sum()) < 1e-6, (d_o.sum(), r_o.sum())
    Bmax[o] = frechet_extremum(B[o], d_o, r_o, "max")
    Bmin[o] = frechet_extremum(B[o], d_o, r_o, "min")
    q_ind = np.outer(d_o, r_o) / r_o.sum()   # independence coupling = current proxy
    Bind[o] = float((q_ind * B[o]).sum())
    print(f"  {o:8}: min {Bmin[o]*60/Rtot[o]:6.1f} | independence {Bind[o]*60/Rtot[o]:6.1f} | max {Bmax[o]*60/Rtot[o]:6.1f}  [min/mission]")

# ---------- exhaustive search over triples ----------
print()
print("=" * 78)
print("EXHAUSTIVE SEARCH 5456 TRIPLES, three criteria")
print("=" * 78)
sumBmax = sum(Bmax.values()); sumBmin = sum(Bmin.values()); sumBind = sum(Bind.values())
Dtot = D.sum()

best = {"rob": (9e9, None), "ind": (9e9, None), "opt": (9e9, None)}
for tri in combinations(range(len(AF)), 3):
    A = A_of(tri)
    core = float((D * A).sum()) * (TOT / Dtot)      # Sum_o Sum_i d_i^o A_i
    v_rob = (core + sumBmax) / TOT
    v_ind = (core + sumBind) / TOT
    v_opt = (core + sumBmin) / TOT
    if v_rob < best["rob"][0]: best["rob"] = (v_rob, tri)
    if v_ind < best["ind"][0]: best["ind"] = (v_ind, tri)
    if v_opt < best["opt"][0]: best["opt"] = (v_opt, tri)

def nm(tri): return ", ".join(sorted(AF[b]["muni"] for b in tri))
for key, label in [("rob", "min-max (robust)"), ("ind", "independence (current proxy)"), ("opt", "min-min (optimistic)")]:
    v, tri = best[key]
    print(f"  {label:28}: {v*60:6.1f} min | bases {nm(tri)}")

print()
print("=" * 78)
print("TEST OF THE INVARIANCE THEOREM")
print("=" * 78)
# The theorem speaks of the SET of minimizers, not of a single triple. With
# a degenerate optimum, comparison of single choices may pass or fail depending
# on tie-breaking, so we compare entire sets.
EPS = 1e-9
_v = {"rob": [], "ind": [], "opt": []}
for _tri in combinations(range(len(AF)), 3):
    _A = A_of(_tri)
    _c = float((D * _A).sum()) * (TOT / Dtot)
    _v["rob"].append(((_c + sumBmax) / TOT, _tri))
    _v["ind"].append(((_c + sumBind) / TOT, _tri))
    _v["opt"].append(((_c + sumBmin) / TOT, _tri))
ARG = {}
for _k, _l in _v.items():
    _m = min(x for x, _ in _l)
    ARG[_k] = {t for x, t in _l if x - _m < EPS}
for _k in ("rob", "ind", "opt"):
    print(f"  argmin set for criterion {_k:4}: {len(ARG[_k])} triples")
same = ARG["rob"] == ARG["ind"] == ARG["opt"]
print(f"  argmin SETS identical for three criteria: {same}")
if same and len(ARG["rob"]) == 1:
    print("  optimum unique, so result does not depend on tie-breaking")
same = same and best["rob"][1] == best["ind"][1] == best["opt"][1]
if same:
    tri = best["rob"][1]
    A = A_of(tri); core = float((D * A).sum()) * (TOT / Dtot)
    lo = (core + sumBmin) / TOT * 60
    ind = (core + sumBind) / TOT * 60
    hi = (core + sumBmax) / TOT * 60
    print(f"  PARTIAL IDENTIFICATION INTERVAL of the mean mission time:")
    print(f"    [{lo:.1f} , {hi:.1f}] min,  width {hi-lo:.1f} min")
    print(f"    independence coupling (current proxy): {ind:.1f} min")
    print(f"    proxy position in interval: {(ind-lo)/(hi-lo)*100:.0f}% of width")

# save
import json as _j
out = {"bases_robust": [AF[b]["icao"] for b in best["rob"][1]],
       "bases_independence": [AF[b]["icao"] for b in best["ind"][1]],
       "bases_optimistic": [AF[b]["icao"] for b in best["opt"][1]],
       "min_min_min": best["opt"][0] * 60, "min_max_min": best["rob"][0] * 60,
       "independence_min": best["ind"][0] * 60,
       "invariance": bool(same)}
with open(_os.path.join(RESULTS, "frechet_invariance.json"), "w", encoding="utf-8") as f:
    _j.dump(out, f, ensure_ascii=False, indent=1)
print(f"\n  saved results/frechet_invariance.json")
