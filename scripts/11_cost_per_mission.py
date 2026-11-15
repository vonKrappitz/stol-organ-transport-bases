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

import csv, re, json, math
from itertools import combinations
import os as _os
_here=_os.path.dirname(_os.path.abspath(__file__))
exec(open(_os.path.join(_here,"10_mission_loss_distribution.py")).read().split("# --- plot")[0].split("ST=setup")[0])  # reuses the loaders, setup() and helpers of script 10, cut at its text markers
# variable cost (USD/h) and its parts (fuel, maintenance, reserves), price of a used aircraft
COST={"STOL Caravan EX":(400,350,250,1000,2.6e6,setup("AUDYT33",330,1.05,5,5)),
      "Piaggio P180":(800,950,750,2500,2.5e6,setup(1100,700,1.12,18,10)),
      "Learjet 45":(1200,900,700,2800,3.0e6,setup(1536,800,1.12,18,12))}
def misshours(k,gr,c,S):
    AF,near,cair,sair,flt,bt,act=S
    i,_=sair[k];ci,_=cair[c]
    pd=min(hav(AF[b]["lat"],AF[b]["lon"],AF[i]["lat"],AF[i]["lon"]) for b in bt)         # positioning
    rd=min(hav(AF[ci]["lat"],AF[ci]["lon"],AF[b]["lat"],AF[b]["lon"]) for b in bt)        # return to base
    td=hav(AF[i]["lat"],AF[i]["lon"],AF[ci]["lat"],AF[ci]["lon"])                          # transport
    h=flt(td)+flt(rd)+(flt(pd) if pd>0.1 else 0)
    return h
print(f"{'aircraft':18} | {'fuel':6} | {'maint':6} | {'reserve':6} | {'variable/h':9} | {'h/mission':10} | {'cost/mission':11} | used price")
print("-"*118)
res={}
for name,(fu,mt,rs,var,acq,S) in COST.items():
    num=0;den=0
    for gr,cl in VOL.items():
        for c,v in cl.items():
            for k in CENT:
                w=wS(k)*v; num+=w*misshours(k,gr,c,S); den+=w
    h=num/den; cpm=h*var
    res[name]=(h,cpm)
    print(f"{name:18} | ${fu:5} | ${mt:5} | ${rs:5} | ${var:8} | {h:8.2f} h | ${cpm:9,.0f} | ${acq/1e6:.1f}M")
print("\nCost per mission relative to the Caravan:")
base=res["STOL Caravan EX"][1]
for name,(h,cpm) in res.items():
    print(f"  {name:18} x{cpm/base:.2f}")

# --- machine-readable results ---
import json as _json
_base = res["STOL Caravan EX"][1]
_out = {_n: {"hours_per_mission": round(_h, 2), "cost_per_mission_usd": round(_c, 0),
             "ratio_to_caravan": round(_c / _base, 2)} for _n, (_h, _c) in res.items()}
# This script pulls in code from script 10, which points RESULTS at the figures
# folder. The path is therefore built from the repository root.
_RES = _os.path.join(_REPO_DIR, "results"); _os.makedirs(_RES, exist_ok=True)
with open(_os.path.join(_RES, "cost_per_mission.json"), "w", encoding="utf-8") as _f:
    _json.dump(_out, _f, ensure_ascii=False, indent=2)
print("  saved results/cost_per_mission.json")