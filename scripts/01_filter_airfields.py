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

import csv, re
WOJ={"PL-DS":"dolnośląskie","PL-KP":"kuj-pom","PL-LU":"lubelskie","PL-LB":"lubuskie",
"PL-LD":"łódzkie","PL-MA":"małopolskie","PL-MZ":"mazowieckie","PL-OP":"opolskie",
"PL-PK":"podkarpackie","PL-PD":"podlaskie","PL-PM":"pomorskie","PL-SL":"śląskie",
"PL-SK":"świętokrzyskie","PL-WN":"warm-maz","PL-WP":"wielkopolskie","PL-ZP":"zach-pom"}
keep={"small_airport","medium_airport","large_airport"}
ap={}
with open("airports.csv",newline='',encoding="utf-8") as f:
    for r in csv.DictReader(f):
        if r["iso_country"]!="PL" or r["type"] not in keep: continue
        ap[r["ident"]]={"name":r["name"],"muni":r["municipality"] or r["name"],"woj":WOJ.get(r["iso_region"],r["iso_region"]),
            "icao":r["icao_code"] or r["ident"],"lat":r["latitude_deg"],"lon":r["longitude_deg"],"rwys":[]}
HARD=re.compile(r"asph|ashp|aspha|\basp\b|conc|\bcon\b|cement|bitum|tarmac|\btar\b|paved|\bpav|\bpem\b|sealed|\bseal\b|composite|\bcop\b|\bhard\b|macadam|\bpcn\b",re.I)
SOFT=re.compile(r"grass|\bgrs\b|turf|\bgvl\b|gravel|dirt|sand|soil|earth|clay|snow|\bice\b|water|\bsod\b|\bgre\b|unpaved|natural",re.I)
def is_hard(s):
    if not s: return False
    if SOFT.search(s) and not HARD.search(s): return False
    return bool(HARD.search(s))
with open("runways.csv",newline='',encoding="utf-8") as f:
    for r in csv.DictReader(f):
        aid=r["airport_ident"]
        if aid not in ap or r["closed"]=="1": continue
        try: ln=int(r["length_ft"])
        except: continue
        ap[aid]["rwys"].append({"len_ft":ln,"surf":r["surface"],"lit":r["lighted"]=="1"})
rows=[]
for aid,a in ap.items():
    hard=[w for w in a["rwys"] if is_hard(w["surf"])]
    if not hard: continue
    b=max(hard,key=lambda w:w["len_ft"])
    rows.append({"icao":a["icao"],"muni":a["muni"],"woj":a["woj"],"lat":round(float(a["lat"]),4),
        "lon":round(float(a["lon"]),4),"len_m":round(b["len_ft"]*0.3048),"surf":b["surf"],
        "lit":b["lit"],"mil":bool(re.search(r"military|air base",a["name"],re.I))})
rows.sort(key=lambda x:-x["len_m"])
OPT,EMG=750,700
opt=[x for x in rows if x["len_m"]>=OPT]
emg=[x for x in rows if EMG<=x["len_m"]<OPT]
print(f"OPTIMUM  (>= {OPT} m): {len(opt)} airfields")
print(f"MARGINAL ({EMG}-{OPT} m): {len(emg)} -> "+", ".join(f"{x['icao']} {x['muni']} {x['len_m']}m [{x['surf']}]" for x in emg))
print(f"TOTAL    (>= {EMG} m): {len(opt)+len(emg)}")
print("Military airfields in the optimum set:", sum(1 for x in opt if x['mil']))
woj=sorted(set(x['woj'] for x in opt))
print(f"Voivodeships in the optimum set: {len(woj)}")
with open(_os.path.join(RESULTS, "stol_candidates_final.csv"),"w",newline='',encoding="utf-8") as f:
    w=csv.writer(f); w.writerow(["icao","nazwa","voivodeship","dlugosc_m","surface","lighting","wojskowe","tryb","lat","lon"])
    for x in opt+emg:
        tryb="optimum" if x["len_m"]>=OPT else "awaryjny"
        w.writerow([x["icao"],x["muni"],x["woj"],x["len_m"],x["surf"],"yes" if x["lit"] else "no","yes" if x["mil"] else "no",tryb,x["lat"],x["lon"]])
print("CSV:", _os.path.join(RESULTS, "stol_candidates_final.csv"))
