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

# --- save the result to a file so it is reproducible, not copied by hand ---
import io as _io, sys as _sys
_bufor = _io.StringIO()
class _Tee:
    def __init__(self, *s): self.s = s
    def write(self, x):
        for t in self.s: t.write(x)
    def flush(self):
        for t in self.s: t.flush()
_stdout_org = _sys.stdout
_sys.stdout = _Tee(_stdout_org, _bufor)
import atexit as _atexit
def _zapisz():
    _sys.stdout = _stdout_org
    with open(_os.path.join(RESULTS, "sensitivity_result.txt"), "w", encoding="utf-8") as f:
        f.write(_bufor.getvalue())
    print(f"  saved {_os.path.join(RESULTS, 'sensitivity_result.txt')}")
_atexit.register(_zapisz)
# end of save block


import csv, re, json, math
from itertools import combinations

# ---------- load airfields and runways (as in 04_minimax.py) ----------
keep={"small_airport","medium_airport","large_airport"}
ap={}
with open("airports.csv",newline='',encoding="utf-8") as f:
    for r in csv.DictReader(f):
        if r["iso_country"]!="PL" or r["type"] not in keep: continue
        ap[r["ident"]]={"muni":r["municipality"] or r["name"],"icao":r["icao_code"] or r["ident"],
            "lat":float(r["latitude_deg"]),"lon":float(r["longitude_deg"]),"rwys":[]}
HARD=re.compile(r"asph|ashp|aspha|\basp\b|conc|\bcon\b|cement|bitum|tarmac|\btar\b|paved|\bpav|\bpem\b|sealed|\bseal\b|composite|\bcop\b|\bhard\b|macadam|\bpcn\b",re.I)
SOFT=re.compile(r"grass|\bgrs\b|turf|\bgvl\b|gravel|dirt|sand|soil|earth|clay|snow|\bice\b|water|\bsod\b|\bgre\b|unpaved|natural",re.I)
def hard(s):
    if not s: return False
    if SOFT.search(s) and not HARD.search(s): return False
    return bool(HARD.search(s))
with open("runways.csv",newline='',encoding="utf-8") as f:
    for r in csv.DictReader(f):
        a=r["airport_ident"]
        if a not in ap or r["closed"]=="1": continue
        try: ln=int(r["length_ft"])
        except: continue
        ap[a]["rwys"].append((ln,r["surface"]))

import csv as _csv
_TROJKA=["EPBY","EPML","EPSY"]
_CERT13=["EPWA","EPGD","EPKT","EPKK","EPLL","EPPO","EPRZ","EPSC","EPMO","EPWR","EPZG","EPLB","EPRA"]
_ad4rows={r["icao"]:r for r in _csv.DictReader(open("airfield_audit_thresholds.csv", encoding="utf-8"))}
AUDYT33=sorted(set(_TROJKA+_CERT13+[ic for ic,r in _ad4rows.items() if r["prog_kons"]=="1"]))
AUDYT40=sorted(set(_TROJKA+_CERT13+[ic for ic,r in _ad4rows.items() if r["prog_baza"]=="1"]))
def build_AF(thr_m):
    # audit thresholds: thr_m<=758 -> base set of 40; otherwise main set of 33
    chc=AUDYT40 if thr_m<=758 else AUDYT33
    AF=[]; seen=set()
    for a,d in ap.items():
        if d["icao"] in chc and d["icao"] not in seen:
            AF.append({"icao":d["icao"],"muni":d["muni"],"lat":d["lat"],"lon":d["lon"]}); seen.add(d["icao"])
    for ic in set(chc)-seen:
        for a,d in ap.items():
            if d["icao"]==ic:
                AF.append({"icao":ic,"muni":d["muni"],"lat":d["lat"],"lon":d["lon"]}); break
    return AF

g=json.load(open("voivodeship_boundaries.json", encoding="utf-8")); CENT=g["cent"]; OSR=g["osr"]

def hav(lat1,lon1,lat2,lon2):
    R=6371.0; p1,p2=math.radians(lat1),math.radians(lat2)
    dp=math.radians(lat2-lat1); dl=math.radians(lon2-lon1)
    a=math.sin(dp/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*R*math.asin(math.sqrt(a))

ORG={"heart":["Gdańsk","Kraków","Poznań","Warszawa","Wrocław","Zabrze"],
"lungs":["Gdańsk","Kraków","Poznań","Szczecin","Warszawa","Zabrze"],
"liver":["Bydgoszcz","Gdańsk","Katowice","Szczecin","Warszawa","Wrocław"]}

def nearest(AF,lat,lon):
    best=None;bd=9e9
    for i,a in enumerate(AF):
        d=hav(lat,lon,a["lat"],a["lon"])
        if d<bd: bd=d;best=i
    return best,bd

def solve(VH=240.0,VS=330.0,STARTUP=5/60,thr_m=875.0,src_mode="centroids",p=3):
    AF=build_AF(thr_m)
    # destinations -> nearest airfield + helicopter feeder leg
    cair={}
    for c,(la,lo) in OSR.items():
        i,d=nearest(AF,la,lo); cair[c]=(i,d)
    # zbuduj zrodla wedlug trybu
    src=[]
    if src_mode=="centroids":
        pts=[(k,la,lo) for k,(la,lo) in CENT.items()]
    elif src_mode=="osrodki":
        pts=[(k,la,lo) for k,(la,lo) in OSR.items()]
    elif src_mode=="airports":
        pts=[(a["icao"],a["lat"],a["lon"]) for a in AF]
    for k,la,lo in pts:
        if src_mode=="airports":
            # the source lies on an airfield: helicopter feeder leg = 0, source airfield = that airfield
            ai,helikm=nearest(AF,la,lo)  # zwroci to samo lotnisko, d~0
        else:
            ai,helikm=nearest(AF,la,lo)
        worst=0
        for g_,cl in ORG.items():
            for c in cl:
                ci,cd=cair[c]
                t=hav(AF[ai]["lat"],AF[ai]["lon"],AF[ci]["lat"],AF[ci]["lon"])/VS + cd/VH
                if t>worst: worst=t
        src.append({"k":k,"ai":ai,"heli":helikm/VH,"dest":worst})
    D=[[hav(AF[b]["lat"],AF[b]["lon"],AF[s["ai"]]["lat"],AF[s["ai"]]["lon"]) for b in range(len(AF))] for s in src]
    best=9e9; bestT=None
    for tri in combinations(range(len(AF)),p):
        mx=0
        for si,s in enumerate(src):
            pos=min(D[si][b] for b in tri)/VS
            T=max(s["heli"],STARTUP+pos)+s["dest"]
            if T>mx: mx=T
            if mx>=best: break
        if mx<best: best=mx; bestT=tri
    bases=tuple(sorted(AF[b]["icao"] for b in bestT))
    return best*60, bases, len(AF)

# ---------- WALIDACJA: baza ----------
v,b,n=solve()
print(f"BASELINE VALIDATION: {v:.1f} min, bases {b}, |AF|={n}")
print(f"  expected: 143.5 min, ('EPBK','EPBY','EPML'), 33")
assert abs(v-143.5)<0.1 and b==('EPBK','EPBY','EPML') and n==33, "BAZA SIE NIE ZGADZA"
print("  MATCHES\n")
BASE=('EPBK','EPBY','EPML')


def line(label, val, bases, extra=""):
    same = "= baseline" if tuple(bases)==BASE else "CHANGED"
    print(f"  {label:28} {val:6.1f} min  {same:7} {','.join(bases)}  {extra}")

print("\n########## A. SENSITIVITY TO SPEEDS (baseline VH=240, VS=330) ##########")
print("  setting                   result     status  bases")
keep=0; tot=0
for VH in (204,240,276):
    for VS in (280,330,380):
        v,b,n=solve(VH=VH,VS=VS)
        tot+=1; keep+= (tuple(b)==BASE)
        line(f"VH={VH} VS={VS}", v, b)
print(f"  --> base triple unchanged in {keep}/{tot} speed combinations")

print("\n########## B. SENSITIVITY TO RUNWAY THRESHOLD (baseline 750 m) ##########")
print("  setting                   result     status  bases")
kb=0; tb=0
for thr in (700,750,800,900,1000):
    v,b,n=solve(thr_m=thr)
    tb+=1; kb+=(tuple(b)==BASE)
    line(f"threshold={thr} m  (|AF|={n})", v, b)
print(f"  --> base triple unchanged in {kb}/{tb} thresholds")

print("\n########## C. SENSITIVITY TO THE SOURCE SET ##########")
print("  setting                   result     status  bases")
modes=[("centroids","16 voivodeship centroids (baseline)"),
       ("osrodki","9 centre cities as sources"),
       ("airports","33 airfields, fully demand-free")]
for m,desc in modes:
    v,b,n=solve(src_mode=m)
    line(desc, v, b)

print("\n########## STABILITY SUMMARY ##########")
allres=[]
for VH in (204,240,276):
    for VS in (280,330,380):
        allres.append(solve(VH=VH,VS=VS)[1])
for thr in (700,750,800,900,1000):
    allres.append(solve(thr_m=thr)[1])
same=sum(1 for b in allres if tuple(b)==BASE)
print(f"  Speed and threshold perturbations in total: {len(allres)}")
print(f"  Triple Bialystok, Bydgoszcz, Mielec retained: {same}/{len(allres)}")
# zakres wartosci na bazowych zrodlach przy bazowym progu, po predkosciach
vals=[solve(VH=VH,VS=VS)[0] for VH in (204,240,276) for VS in (280,330,380)]
print(f"  Worst time across the speed grid: {min(vals):.0f} do {max(vals):.0f} min")

# save results in machine-readable form
_w = {"baseline": {}, "runway_threshold_m": {}, "speed": {}, "sources": {}}
_v, _b, _n = solve()
_w["baseline"] = {"worst_min": round(_v, 1), "bases": list(_b), "airfields": _n}
for _thr in (700, 750, 800, 875, 900, 1000):
    _v, _b, _n = solve(thr_m=_thr)
    _w["runway_threshold_m"][str(_thr)] = {"worst_min": round(_v, 1), "bases": list(_b), "airfields": _n}
for _vh, _vs in ((200, 330), (240, 330), (280, 330), (240, 280), (240, 380)):
    _v, _b, _n = solve(VH=float(_vh), VS=float(_vs))
    _w["speed"][f"VH{_vh}_VS{_vs}"] = {"worst_min": round(_v, 1), "bases": list(_b)}
for _sm in ("centroids", "osrodki", "airports"):
    try:
        _v, _b, _n = solve(src_mode=_sm)
        _w["sources"][_sm] = {"worst_min": round(_v, 1), "bases": list(_b)}
    except Exception as _e:
        _w["sources"][_sm] = {"error": str(_e)}   # jawnie, nie po cichu
with open(_os.path.join(RESULTS, "sensitivity.json"), "w", encoding="utf-8") as _f:
    json.dump(_w, _f, ensure_ascii=False, indent=2)
print(f"  saved results/sensitivity.json")
