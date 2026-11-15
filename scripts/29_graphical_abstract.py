#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# --- paths relative to the repository (runs from any working directory) ---
import os as _os
try:
    _SCRIPT_DIR = _os.path.dirname(_os.path.abspath(__file__))
except NameError:
    _SCRIPT_DIR = _os.getcwd()
_REPO_DIR = _os.path.dirname(_SCRIPT_DIR)
_DANE_DIR = _os.path.join(_REPO_DIR, "data")
FIGURES = _os.path.join(_REPO_DIR, "figures")
_os.makedirs(FIGURES, exist_ok=True)
_os.chdir(_DANE_DIR)
# --- end of the path block ---

"""29_graphical_abstract.py

Graphical abstract in the wide format that journals ask for.

The guidelines ask for 531 by 1328 points, an image about 2.5 times wider than
tall. The minimax map is nearly square, so this script sets the map beside the
three numbers that carry the result.
"""
import csv
import json
import math

import matplotlib
matplotlib.use("Agg")
import matplotlib.patheffects as _pe
import matplotlib.pyplot as plt

_OBW = [_pe.withStroke(linewidth=2.2, foreground="white")]
try:
    from shapely.geometry import shape
    _MA_SHAPELY = True
except ImportError:
    _MA_SHAPELY = False

    def shape(g):
        return g


R = 6371.0
BAZY = {"EPBK": ("Białystok", 53.1014, 23.1706),
        "EPBY": ("Bydgoszcz", 53.0968, 17.9777),
        "EPML": ("Mielec", 50.3223, 21.4621)}

g = json.load(open("voivodeship_boundaries.json"))
OSR = g["osr"]

fig, (axm, axt) = plt.subplots(
    1, 2, figsize=(13.0, 5.2), gridspec_kw={"width_ratios": [1.0, 1.55]})

# --- left panel: map ---
try:
    gj = json.load(open("wojewodztwa.geojson"))
    for f in gj["features"]:
        geom = f["geometry"]
        czesci = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
        for cz in czesci:
            xy = cz[0] if isinstance(cz[0][0], (list, tuple)) else cz
            axm.plot([p[0] for p in xy], [p[1] for p in xy], lw=0.5, color="#b9bec7", zorder=1)
except Exception as e:
    print(f"  WARNING boundaries: {e}")

for c, (la, lo) in OSR.items():
    axm.scatter(lo, la, s=52, marker="*", color="#d62728", edgecolor="white", lw=0.5, zorder=5)
for ic, (nazwa, la, lo) in BAZY.items():
    axm.scatter(lo, la, s=150, marker="^", color="#1f77b4", edgecolor="white", lw=0.9, zorder=6)
    axm.annotate(nazwa, (lo, la), (0, -15), textcoords="offset points", fontsize=8.5,
                 color="#0d3b66", weight="bold", ha="center", zorder=7, path_effects=_OBW)
axm.set_axis_off()
axm.set_aspect(1 / math.cos(math.radians(52)))
axm.margins(0.03)

# --- right panel: the result in three numbers ---
axt.set_axis_off()
axt.set_xlim(0, 1)
axt.set_ylim(0, 1)
axt.text(0.0, 0.93, "Where the matrix is missing,\nthe siting decision still holds",
         fontsize=17, weight="bold", color="#1a1a2e", va="top", linespacing=1.25)
WIERSZE = [("143.5 min", "worst mission, three bases"),
           ("125.2 min", "unimprovable geometric bound"),
           ("45.0 to 89.1", "mean mission, min, identified only to an interval,\nat the bases that minimize it (Warsaw, Katowice, Poznań)")]
# The bases and the three numbers are typed in. This check keeps them equal
# to the results of scripts 19, 27 and 23.
_res=_os.path.join(_REPO_DIR,"results")
if all(_os.path.exists(_os.path.join(_res,_p)) for _p in ('minimax_audit.json', 'lower_bound.json', 'frechet_invariance.json')):
    _a=[v["p"]["3"] for v in json.load(open(_os.path.join(_res,'minimax_audit.json'),encoding="utf-8")).values() if v["airfields"]==33][0]
    assert abs(_a["worst_min"]-143.5)<0.05 and all(_ic in _a["bases"] for _ic in BAZY), _a
    assert abs(json.load(open(_os.path.join(_res,'lower_bound.json'),encoding="utf-8"))["ograniczenie_min"]-125.2)<0.05
    _fr=json.load(open(_os.path.join(_res,'frechet_invariance.json'),encoding="utf-8"))
    assert round(_fr["min_min_min"],1)==45.0 and round(_fr["min_max_min"],1)==89.1, _fr
    # The interval belongs to the bases that minimize the mean, not to the minimax bases on the map.
    assert sorted(_fr["bazy_dro"])==["EPBC","EPKM","EPPO"], _fr["bazy_dro"]
y = 0.56
for duza, opis in WIERSZE:
    axt.text(0.0, y, duza, fontsize=21, weight="bold", color="#1f77b4", va="center")
    axt.text(0.34, y, opis, fontsize=11.5, color="#3a3f4a", va="center")
    y -= 0.19
axt.text(0.0, 0.02, "Location is invariant across the whole Fréchet class of couplings.",
         fontsize=11.5, style="italic", color="#5a5f6a", va="bottom")

plt.tight_layout()
sciezka = _os.path.join(FIGURES, "graphical_abstract.png")
plt.savefig(sciezka, dpi=350, bbox_inches="tight", pad_inches=0.06)
plt.close()

from PIL import Image
im = Image.open(sciezka)
# The cropped image can come out narrower than the required proportion, depending on the
# text width in the local fonts. White margins are added left and right until it holds.
if im.width / im.height < 1328 / 531:
    _w = int(math.ceil(im.height * 2.52))
    _tlo = Image.new("RGB", (_w, im.height), "white")
    _tlo.paste(im.convert("RGB"), ((_w - im.width) // 2, 0))
    _tlo.save(sciezka, dpi=(350, 350))
    im = Image.open(sciezka)
print(f"OK graphical abstract {im.size}, aspect ratio {im.width/im.height:.2f}")
print(f"   required aspect ratio >= {1328/531:.2f}, minimum width 1328 px")
print(f"   {'MEETS IT' if im.width/im.height >= 1328/531 and im.width >= 1328 else 'DOES NOT MEET IT'}")
