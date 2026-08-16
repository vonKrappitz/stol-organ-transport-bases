# Copyright 2026 Maciej M. Kasperek. Licensed under the Apache License, Version 2.0.
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# paths relative to the repository root
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
# end of path block

"""29_graphical_abstract.py

Graphical abstract in the aspect ratio required by the journal.

Rationale. The guidelines require 531 x 1328 points, i.e. a WIDE image
with ratio about 2.5 to 1, legible at 5 x 13 cm. The minimax map is nearly
square and does not meet this, so it served as the abstract against the
checklist. This script composes a map with three numbers that carry the result.
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
        "EPML": ("Mielec", 50.3223, 21.4620)}

g = json.load(open("voivodeship_boundaries.json", encoding="utf-8"))
OSR = g["osr"]

fig, (axm, axt) = plt.subplots(
    1, 2, figsize=(13.0, 5.2), gridspec_kw={"width_ratios": [1.0, 1.55]})

# --- left panel: map ---
try:
    gj = json.load(open("wojewodztwa.geojson", encoding="utf-8"))
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
           ("45.0 to 89.1", "mean identified only to an interval, min")]
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
print(f"OK graphical abstract {im.size}, aspect ratio {im.width/im.height:.2f}")
print(f"   required ratio >= {1328/531:.2f}, minimum 1328 px width")
print(f"   {'MEETS' if im.width/im.height >= 1328/531 and im.width >= 1328 else 'DOES NOT MEET'}")
