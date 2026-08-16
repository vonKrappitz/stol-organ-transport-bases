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

# paths; NFZ data handled gracefully when absent
import os as _os2, sys as _sys2
_nfz = _os2.path.join(_DANE_DIR, "nhf_interhospital_transport_2020_2024.xlsx")
_nfzc = _os2.path.join(_DANE_DIR, "nhf_transport_od.csv")
if not _os2.path.exists(_nfz) and not _os2.path.exists(_nfzc):
    print("=" * 68)
    print("Missing NHF data file, see dane/NHF_transport_data.md")
    print("Sa dostepne od NFZ na wniosek - patrz dane/NHF_transport_data.md")
    print("The core results reproduce without them (remaining scripts). Skipping.")
    print("=" * 68)
    _sys2.exit(0)
# end of NFZ handling

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 18_transport_distance_profile.py
# Figure: distribution of NHF inter-voivodeship flows by centroid distance,
# split into the disclosed part and the part imputed from "<5" censoring
# (=2 per cell).
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np, csv, json, math
from collections import defaultdict

def hav(a,b,c,d):
    R=6371.0;p1,p2=math.radians(a),math.radians(c);dp=math.radians(c-a);dl=math.radians(d-b)
    x=math.sin(dp/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2;return 2*R*math.asin(math.sqrt(x))
cent=json.load(open('voivodeship_boundaries.json', encoding="utf-8"))['cent']
rows=list(csv.DictReader(open('nhf_transport_od.csv',encoding='utf-8')))
pasma=[(0,100),(100,200),(200,300),(300,400),(400,600)]
et=["0–100","100–200","200–300","300–400","400+"]
jaw=defaultdict(int); imp=defaultdict(int)
for r in rows:
    wy,pr=r['voivodeship_from'].lower(),r['voivodeship_to'].lower()
    if wy==pr: continue
    d=hav(*cent[wy],*cent[pr])
    for k,(lo,hi) in enumerate(pasma):
        if lo<=d<hi or (k==len(pasma)-1 and d>=lo): p=k; break
    if r['censored_below_5']=='1': imp[p]+=2
    else: jaw[p]+=int(r['services'])
J=[jaw[k] for k in range(5)]; I=[imp[k] for k in range(5)]
x=np.arange(5)
fig,ax=plt.subplots(figsize=(5.06,3.08))
b1=ax.bar(x,J,0.62,color="#5b8c5a",edgecolor="white",label="liczby jawne",zorder=3)
b2=ax.bar(x,I,0.62,bottom=J,color="#c44e52",edgecolor="white",label="imputacja cenzury („<5”=2)",zorder=3)
for k in range(5):
    tot=J[k]+I[k]
    ax.text(k, tot+90, f"{tot}", ha="center", fontsize=8.6, weight="bold", color="#1a1a2e")
    if tot: ax.text(k, tot+320, f"{100*I[k]/tot:.0f}% cenz.", ha="center", fontsize=7.0, color="#8a1010")
ax.set_xticks(x); ax.set_xticklabels(et, fontsize=8.2)
ax.set_xlabel("odległość centroidów województw, km", fontsize=8.6)
ax.set_ylabel("świadczenia transportu, suma 2020–2024", fontsize=8.6)
ax.set_title("Międzywojewódzki transport międzyszpitalny NFZ po odległości\n94% przepływów poniżej 200 km, ogon powyżej 300 km w całości cenzurowany",
             fontsize=9.4, weight="bold", color="#1a1a2e")
ax.legend(fontsize=7.8, frameon=False, loc="upper right")
ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
ax.grid(axis="y", alpha=0.25, zorder=0)
ax.tick_params(labelsize=10)
ax.set_ylim(0, max(np.array(J)+np.array(I))*1.16)
plt.tight_layout()
_FIG = _os.path.join(_REPRO_DIR, "figures"); _os.makedirs(_FIG, exist_ok=True)
plt.savefig(_os.path.join(_FIG, "map_distance_profile.png"), dpi=145, bbox_inches="tight", pad_inches=0.05)
plt.close()
print("OK distance profile | bands:", list(zip(et, J, I)))

# save results in machine-readable form
_bands = []
for _e, _j, _i in zip(et, J, I):
    _bands.append({"band_km": _e, "disclosed": int(_j), "estimated": int(_i), "total": int(_j + _i)})
_sum = sum(x["total"] for x in _bands)
_to200 = sum(x["total"] for x in _bands if x["band_km"] in ("0–100", "100–200"))
_b100_200 = sum(x["total"] for x in _bands if x["band_km"] == "100–200")
_over300 = [x for x in _bands if x["band_km"] not in ("0–100", "100–200", "200–300")]
_prof = {
    "bands": _bands,
    "total_procedures": _sum,
    "share_below_200km_pct": round(100 * _to200 / _sum, 2),
    "share_band_100_200_pct": round(100 * _b100_200 / _sum, 2),
    "disclosed_above_300km": sum(x["disclosed"] for x in _over300),
    "estimated_above_300km": sum(x["estimated"] for x in _over300),
}
with open(_os.path.join(RESULTS, "distance_profile.json"), "w", encoding="utf-8") as _f:
    json.dump(_prof, _f, ensure_ascii=False, indent=2)
print(f"  saved results/distance_profile.json")
