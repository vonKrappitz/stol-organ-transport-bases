# -*- coding: utf-8 -*-
"""
28_optimal_set.py

Structure of the set of optimal triples.
The first part repeats the data block of script 23.
"""
# --- paths relative to the repository ---
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
# --- end of the path block ---

import csv, re, json, math
from itertools import combinations
import numpy as np
from scipy.optimize import linprog

# ---------- data: as in 05_compare_methods ----------
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
_ad4k = [r["icao"] for r in csv.DictReader(open("airfield_audit_thresholds.csv")) if r["prog_kons"] == "1"]
AUDYT33 = sorted(set(_TROJKA + _CERT13 + _ad4k))
AF = [{"icao": d["icao"], "muni": d["muni"], "lat": d["lat"], "lon": d["lon"]}
      for a, d in ap.items() if d["icao"] in AUDYT33]
for _ic in set(AUDYT33) - {a["icao"] for a in AF}:
    for a, d in ap.items():
        if d["icao"] == _ic:
            AF.append({"icao": _ic, "muni": d["muni"], "lat": d["lat"], "lon": d["lon"]})
assert len(AF) == 33, len(AF)

g = json.load(open("voivodeship_boundaries.json")); CENT = g["cent"]; OSR = g["osr"]
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
# d_i : donors of the voivodeship (mean 2020-2024)
D = np.array([wgt(k) for k in WOJ])
# r_k^o : transplant volume of centre k for organ o
ORG = list(VOL.keys())
# donors are split between organs in proportion to the organ's share, so that
# row and column sums balance in every Frechet set
Rtot = {o: sum(VOL[o].values()) for o in ORG}
TOT = sum(Rtot.values())

print("=" * 78)
print("MARGINS")
print("=" * 78)
print(f"  sources: {len(WOJ)} voivodeships, donors in total {D.sum():.1f}/year")
for o in ORG:
    print(f"  {o:8}: {len(VOL[o])} centres, volume {Rtot[o]}")
print(f"  total volume {TOT}")

# ---------- times ----------
# A_i(x) = max(feeder_i, ST + positioning_i(x))   [depends on x, not on k,o]
# B_ik   = flight(a(i)->c(k)) + feeder_k           [depends on (i,k), not on x]
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
    """Maximum or minimum of sum_ik q_ik B_ik over the transport polytope."""
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
# STRUCTURE OF THE SET OF OPTIMAL SOLUTIONS
# =====================================================================
# The minimax is degenerate here: several triples reach the same value. A
# decision-maker should know which position is forced and which positions are
# free, because that changes the recommendation.
#
# Triples are compared within a tolerance. Three south-eastern airfields lie
# within 20 m of the same distance to Lublin airport, so their triples differ
# by a fraction of a second, which is below the precision of the coordinates.
# An exact comparison would keep only one of the three.
TOL = 0.05  # minutes, half of the 0.1 min precision of the reported times
from collections import Counter as _Counter

def najgorszy(tri):
    mx = 0.0
    for si, w in enumerate(WOJ):
        poz = min(Dist_base[si][b] for b in tri) / VS
        A = max(feeder_src[si], ST + poz)
        for o in ORG:
            for kj in range(B[o].shape[1]):
                T = A + B[o][si][kj]
                if T > mx: mx = T
    return mx

wart = []
for tri in combinations(range(len(AF)), 3):
    wart.append((round(najgorszy(tri) * 60, 6), tri))
opt = min(v for v, _ in wart)
exact = [t for v, t in wart if v == opt]
rem = [t for v, t in wart if v <= opt + TOL]
spread_s = (max(v for v, _ in wart if v <= opt + TOL) - opt) * 60
nxt = min(v for v, _ in wart if v > opt + TOL)
bl5 = [t for v, t in wart if v < opt + 5]
bl10 = [t for v, t in wart if v < opt + 10]

lic = _Counter(b for t in rem for b in t)

def reszta(b):
    """Pairs that complete airfield b to an optimal triple."""
    return frozenset(tuple(x for x in t if x != b) for t in rem if b in t)

# forced position: the airfield present in every exactly tied triple, together
# with the airfields that complete the very same pairs within the tolerance
_lex = _Counter(b for t in exact for b in t)
_n0 = [b for b, n in _lex.items() if n == len(exact)]
grupa = sorted(b for b in lic if _n0 and reszta(b) == reszta(_n0[0]))
assert all(sum(b in grupa for b in t) == 1 for t in rem) or not grupa

print()
print("=" * 78)
print("STRUCTURE OF THE SET OF OPTIMAL SOLUTIONS")
print("=" * 78)
print(f"  optimum:                         {opt:6.1f} min")
print(f"  tolerance:                       {TOL:6.2f} min")
print(f"  triples tied exactly:            {len(exact)}")
print(f"  triples within the tolerance:    {len(rem)}  (spread {spread_s:.2f} s)")
print(f"  next value above the set:        {nxt:6.1f} min (+{(nxt - opt) * 60:.1f} s)")
print(f"  triples within  5 min:           {len(bl5)}")
print(f"  triples within 10 min:           {len(bl10)}")
print(f"  worst triple:                    {max(v for v, _ in wart):6.1f} min")
print()
print("  share of airfields in optimal triples:")
for b, n in lic.most_common():
    gw = "   <<< FORCED POSITION" if b in grupa else ""
    print(f"    {AF[b]['icao']:6} {AF[b]['muni'][:20]:<22} {n}/{len(rem)}{gw}")
wymuszona = [AF[b]["icao"] for b in grupa]
print()
print(f"  FORCED POSITION (exactly one of these in every optimal triple): {wymuszona}")
print(f"  remaining entries spread over {len(lic) - len(grupa)} airfields")
print()
print("  Reading. The robust recommendation is not 'these three airfields' but")
print("  'one base from the forced group is necessary, the other positions are")
print("  free and can follow criteria outside this model, such as cost or readiness'.")

import json as _json
with open(_os.path.join(RESULTS, "optimal_set.json"), "w", encoding="utf-8") as f:
    _json.dump({"optimum_min": round(opt, 1), "tolerancja_min": TOL,
                "trojek_optymalnych": len(rem), "trojek_remis_dokladny": len(exact),
                "rozstep_s": round(spread_s, 2),
                "nastepna_wartosc_min": round(nxt, 1), "odstep_nastepnej_s": round((nxt - opt) * 60, 1),
                "w_promieniu_5min": len(bl5), "w_promieniu_10min": len(bl10),
                "worst_triple_min": round(max(v for v, _ in wart), 1), "spread_min": round(max(v for v, _ in wart) - opt, 1),
                "pozycja_wymuszona": wymuszona,
                "share": {AF[b]["icao"]: n for b, n in lic.most_common()}},
               f, ensure_ascii=False, indent=1)
print(f"\n  saved {_os.path.join(RESULTS, 'optimal_set.json')}")
