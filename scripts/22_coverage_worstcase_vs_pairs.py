# --- paths: paths relative to the repository (runs from any working directory) ---
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
# --- end of the path block ---

# Two coverage models side by side:
# 1) robust worst-case source coverage (the main model, consistent with minimax)
# 2) pair-demand coverage under the proxy
# Their difference is the price of the boundary guarantee.
import csv, json, math
from itertools import combinations
import os as _os
_here=_os.path.dirname(_os.path.abspath(__file__))
exec(open(_os.path.join(_here,"05_compare_methods.py")).read().split("names=[")[0])

BAZY_MM=[i for i,a in enumerate(AF) if a["icao"] in ("EPBK","EPBY","EPML")]
T=135

def cover_wc(tri,T):        # worst case per source (the main model)
    c=0
    for si,s in enumerate(src):
        pos=min(D[si][b] for b in tri)/VS
        if (max(s["heli"],ST+pos)+s["dworst"])*60<=T: c+=s["w"]
    return c/W
def cover_pairs(tri,T):     # pairs under the proxy
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
print(f"at the minimax bases EPBK/EPBY/EPML:")
print(f"  worst case (boundary guarantee): {cover_wc(BAZY_MM,T)*100:.0f}%")
print(f"  pairs (proxy traffic):           {cover_pairs(BAZY_MM,T)*100:.0f}%")
bw,bbw=best(cover_wc); bp,bbp=best(cover_pairs)
print(f"optimum worst-case: {bw*100:.0f}% bases {bbw}")
print(f"optimum pairs:      {bp*100:.0f}% bases {bbp}")
print(f"\nPRICE OF THE BOUNDARY GUARANTEE: proxy traffic coverage {bp*100:.0f}% against guaranteed worst case {bw*100:.0f}%")
print("The difference is the cost of requiring every source to reach its HARDEST eligible target.")

# Table S5 of the supplementary material: the triple is reoptimized at each threshold.
print("\n=== coverage by threshold, triple reoptimized at each threshold ===")
print(f"{'threshold':>9} | {'robust worst case':>17} | {'proxy pairs':>11}")
_c={"threshold_135":{"minimax_bases":{"robust_pct":round(cover_wc(BAZY_MM,T)*100,1),"pairs_pct":round(cover_pairs(BAZY_MM,T)*100,1)},
    "optimum":{"robust_pct":round(bw*100,1),"robust_bases":list(bbw),"pairs_pct":round(bp*100,1),"pairs_bases":list(bbp)}},"by_threshold":{}}
for _T in (120,135,150,180):
    _bw,_=best(cover_wc,_T); _bp,_=best(cover_pairs,_T)
    _c["by_threshold"][str(_T)]={"robust_pct":round(_bw*100,1),"pairs_pct":round(_bp*100,1)}
    print(f"{_T:>5} min | {_bw*100:>16.0f}% | {_bp*100:>10.0f}%")
with open(_os.path.join(RESULTS,"coverage_thresholds.json"),"w",encoding="utf-8") as _f:
    json.dump(_c,_f,ensure_ascii=False,indent=2)
print("  saved results/coverage_thresholds.json")
