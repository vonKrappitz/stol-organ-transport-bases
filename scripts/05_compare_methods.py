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

import csv, re, json, math
from itertools import combinations
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

# audited set (snapshot 2026-07-18): main conservative set of 33
import csv as _csv
_TROJKA=["EPBY","EPML","EPSY"]
_CERT13=["EPWA","EPGD","EPKT","EPKK","EPLL","EPPO","EPRZ","EPSC","EPMO","EPWR","EPZG","EPLB","EPRA"]
_ad4k=[r["icao"] for r in _csv.DictReader(open("airfield_audit_thresholds.csv", encoding="utf-8")) if r["prog_kons"]=="1"]
AUDYT33=sorted(set(_TROJKA+_CERT13+_ad4k))
AF=[{"icao":d["icao"],"muni":d["muni"],"lat":d["lat"],"lon":d["lon"]} for a,d in ap.items() if d["icao"] in AUDYT33]
_braki=set(AUDYT33)-{a["icao"] for a in AF}
for _ic in _braki:  # np. EPBK bez pasa twardego w OurAirports, wspolrzedne z airports.csv
    for a,d in ap.items():
        if d["icao"]==_ic: AF.append({"icao":_ic,"muni":d["muni"],"lat":d["lat"],"lon":d["lon"]})
assert len(AF)==len(AUDYT33),(len(AF),sorted(_braki))
g=json.load(open("voivodeship_boundaries.json", encoding="utf-8")); CENT=g["cent"]; OSR=g["osr"]
WD={"dolnośląskie":(2879271,10.0,10.7,7.95,38,53),"kujawsko-pomorskie":(1996003,9.0,9.2,12.43,27,35),
"lubelskie":(2011047,5.0,5.75,7.88,23,22),"lubuskie":(975023,12.0,17.94,14.25,9,21),
"łódzkie":(2362519,4.0,5.36,7.55,15,22),"małopolskie":(3429632,7.0,10.56,11.08,46,54),
"mazowieckie":(5510527,9.0,8.67,10.16,85,101),"opolskie":(936725,10.0,11.30,11.64,11,13),
"podkarpackie":(2071676,4.0,2.84,4.80,13,16),"podlaskie":(1138216,7.0,4.28,15.71,16,27),
"pomorskie":(2359573,20.0,23.87,21.62,67,55),"śląskie":(4320130,13.0,13.64,15.83,73,83),
"świętokrzyskie":(1168499,4.0,5.75,5.92,23,30),"warmińsko-mazurskie":(1357910,19.0,14.89,10.95,23,27),
"wielkopolskie":(3487973,15.0,11.17,15.16,57,67),"zachodniopomorskie":(1631784,13.0,8.32,12.77,40,41)}
def wgt(k):
    p,a,b,c,d,e=WD[k]; return (a*p/1e6+b*p/1e6+c*p/1e6+d+e)/5
def hav(a,b,c,d):
    R=6371.0;p1,p2=math.radians(a),math.radians(c);dp=math.radians(c-a);dl=math.radians(d-b)
    x=math.sin(dp/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2;return 2*R*math.asin(math.sqrt(x))
VH,VS,ST=240.0,330.0,5/60
VOL={"heart":{"Gdańsk":16,"Kraków":14,"Poznań":8,"Warszawa":67,"Wrocław":49,"Zabrze":48},
"lungs":{"Gdańsk":48,"Kraków":2,"Poznań":7,"Szczecin":4,"Warszawa":26,"Zabrze":60},
"liver":{"Bydgoszcz":39,"Gdańsk":75,"Katowice":50,"Szczecin":78,"Warszawa":365,"Wrocław":7}}
def near(la,lo):
    bi,bd=0,9e9
    for i,a in enumerate(AF):
        x=hav(la,lo,a["lat"],a["lon"])
        if x<bd:bd=x;bi=i
    return bi,bd
cair={c:near(la,lo) for c,(la,lo) in OSR.items()}
TOTV=sum(sum(v.values()) for v in VOL.values())
src=[]
for k,(la,lo) in CENT.items():
    i,d=near(la,lo)
    dworst=0; dsum=0
    for gr,cl in VOL.items():
        for c,v in cl.items():
            ci,cd=cair[c]
            term=hav(AF[i]["lat"],AF[i]["lon"],AF[ci]["lat"],AF[ci]["lon"])/VS+cd/VH
            tr=hav(AF[i]["lat"],AF[i]["lon"],AF[ci]["lat"],AF[ci]["lon"])/VS
            if term>dworst:dworst=term
            dsum+=v*term
    src.append({"woj":k,"ai":i,"heli":d/VH,"dworst":dworst,"davg":dsum/TOTV,"w":wgt(k)})
D=[[hav(AF[b]["lat"],AF[b]["lon"],AF[s["ai"]]["lat"],AF[s["ai"]]["lon"]) for b in range(len(AF))] for s in src]
W=sum(s["w"] for s in src)
def metrics(tri):
    worst=0; wavg=0
    for si,s in enumerate(src):
        pos=min(D[si][b] for b in tri)/VS
        arr=max(s["heli"],ST+pos)
        worst=max(worst,arr+s["dworst"])
        wavg+=s["w"]*(arr+s["davg"])
    return worst, wavg/W
def search(obj,p=3):
    best=9e9;bt=None
    for tri in combinations(range(len(AF)),p):
        v=obj(tri)
        if v<best:best=v;bt=tri
    return bt
# objectives
o_minimax=lambda t: metrics(t)[0]
o_pmedW  =lambda t: metrics(t)[1]
def o_pmedU(t):
    s=0
    for si,sc in enumerate(src):
        pos=min(D[si][b] for b in t)/VS; s+=max(sc["heli"],ST+pos)+sc["davg"]
    return s
def o_stol(t):  # STOL only: positioning + worst transport, no helicopter
    mx=0
    for si,sc in enumerate(src):
        pos=min(D[si][b] for b in t)/VS
        mx=max(mx,pos+ (sc["dworst"]-sc.get("_h",0)))  # dworst zawiera heli_C; przybliz transport=dworst (heli_C maly)
    return mx
def cover(tri,T):  # udzial wazony popytem z najgorszym <= T (min)
    c=0
    for si,s in enumerate(src):
        pos=min(D[si][b] for b in tri)/VS
        if (max(s["heli"],ST+pos)+s["dworst"])*60<=T: c+=s["w"]
    return c/W
def o_cover(t): return -cover(t,135)
names=[("Minimax (worst case)",o_minimax),("Donor-weighted p-median",o_pmedW),
       ("Geographic p-median",o_pmedU),("Worst-case coverage 135 min",o_cover)]
print(f"{'Method':26} | {'Bases':38} | {'worst':>6} | {'w.mean':>6} | {'cov135':>7}")
print("-"*100)
res={}
for nm,ob in names:
    tri=search(ob); wo,wa=metrics(tri); cv=cover(tri,135)
    res[nm]=tri
    bz=", ".join(AF[b]["icao"] for b in tri)
    bzc=", ".join(AF[b]["muni"][:10] for b in tri)
    print(f"{nm:26} | {bz:11} {'('+bzc+')':26} | {wo*60:5.0f}m | {wa*60:5.0f}m | {cv*100:5.0f}%")
print("\nBinding voivodeship for the worst case (minimax bases):")
tri=res["Minimax (worst case)"]
b=max(src,key=lambda s:max(s["heli"],ST+min(D[src.index(s)][x] for x in tri)/VS)+s["dworst"])
print(" ",b["woj"],f"{(max(b['heli'],ST+min(D[src.index(b)][x] for x in tri)/VS)+b['dworst'])*60:.0f} min")

# save results in machine-readable form
_out = {}
for _nm, _tri in res.items():
    _wo, _wa = metrics(_tri)
    _cv = cover(_tri, 135)
    _out[_nm] = {
        "bases_icao": [AF[b]["icao"] for b in _tri],
        "bases_cities": [AF[b]["muni"] for b in _tri],
        "worst_min": round(_wo * 60, 1),
        "weighted_mean_min": round(_wa * 60, 1),
        "coverage_135_pct": round(_cv * 100, 1),
    }
with open(_os.path.join(RESULTS, "compare_methods.json"), "w", encoding="utf-8") as _f:
    json.dump(_out, _f, ensure_ascii=False, indent=2)
print(f"\n  saved results/compare_methods.json ({len(_out)} methods)")
