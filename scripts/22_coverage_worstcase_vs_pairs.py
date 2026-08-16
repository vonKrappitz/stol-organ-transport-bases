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
import csv, json, math
from itertools import combinations
import os as _os
_here=_os.path.dirname(_os.path.abspath(__file__))
exec(open(_os.path.join(_here,"05_compare_methods.py"), encoding="utf-8").read().split("names=[")[0])

BAZY_MM=[i for i,a in enumerate(AF) if a["icao"] in ("EPBK","EPBY","EPML")]
T=135

def cover_wc(tri,T):        # worst-case zagregowane (obecny model main)
    c=0
    for si,s in enumerate(src):
        pos=min(D[si][b] for b in tri)/VS
        if (max(s["heli"],ST+pos)+s["dworst"])*60<=T: c+=s["w"]
    return c/W
def cover_pairs(tri,T):     # pary pod proxy grawitacyjnym
    num=den=0.0
    for si,s in enumerate(src):
        pos=min(D[si][b] for b in tri)/VS; arr=max(s["heli"],ST+pos); i=s["ai"]
        for gr,cl in VOL.items():
            for c,v in cl.items():
                ci,cd=cair[c]; term=hav(AF[i]["lat"],AF[i]["lon"],AF[ci]["lat"],AF[ci]["lon"])/VS+cd/VH
                den+=v
                if (arr+term)*60<=T: num+=v
    return num/den
def best(fn,T=135):
    bb=-1;bt=None
    for tri in combinations(range(len(AF)),3):
        c=fn(tri,T)
        if c>bb:bb=c;bt=tri
    return bb,tuple(sorted(AF[b]["icao"] for b in bt))

print("=== coverage threshold 135 min ===")
print(f"on minimax baseline EPBK/EPBY/EPML:")
print(f"  worst-case (boundary guarantee): {cover_wc(BAZY_MM,T)*100:.0f}%")
print(f"  pairs (gravity proxy traffic):   {cover_pairs(BAZY_MM,T)*100:.0f}%")
bw,bbw=best(cover_wc); bp,bbp=best(cover_pairs)
print(f"optimum worst-case: {bw*100:.0f}% bases {bbw}")
print(f"optimum pairs:      {bp*100:.0f}% bases {bbp}")
print(f"\nPRICE OF THE BOUNDARY GUARANTEE: proxy-traffic coverage {bp*100:.0f}% vs guaranteed worst-case {bw*100:.0f}%")
print("The difference is the cost of requiring every source to reach its HARDEST admissible destination.")
