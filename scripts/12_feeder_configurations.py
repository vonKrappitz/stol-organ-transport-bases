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
keep={"small_airport","medium_airport","large_airport"}
ap={}
for r in csv.DictReader(open("airports.csv",newline='',encoding="utf-8")):
    if r["iso_country"]!="PL" or r["type"] not in keep: continue
    ap[r["ident"]]={"muni":r["municipality"] or r["name"],"lat":float(r["latitude_deg"]),"lon":float(r["longitude_deg"]),"rw":[]}
HARD=re.compile(r"asph|ashp|aspha|\basp\b|conc|\bcon\b|cement|bitum|tarmac|\btar\b|paved|\bpav|\bpem\b|sealed|\bseal\b|composite|\bcop\b|\bhard\b|macadam|\bpcn\b",re.I)
SOFT=re.compile(r"grass|\bgrs\b|turf|\bgvl\b|gravel|dirt|sand|soil|earth|clay|snow|\bice\b|water|\bsod\b|\bgre\b|unpaved|natural",re.I)
def hd(s):
    if not s:return False
    if SOFT.search(s) and not HARD.search(s):return False
    return bool(HARD.search(s))
for r in csv.DictReader(open("runways.csv",newline='',encoding="utf-8")):
    a=r["airport_ident"]
    if a not in ap or r["closed"]=="1":continue
    try:ln=int(r["length_ft"])
    except:continue
    ap[a]["rw"].append((ln,r["surface"]))

import csv as _csv
_TROJKA=["EPBY","EPML","EPSY"]
_CERT13=["EPWA","EPGD","EPKT","EPKK","EPLL","EPPO","EPRZ","EPSC","EPMO","EPWR","EPZG","EPLB","EPRA"]
AUDYT33=sorted(set(_TROJKA+_CERT13+[r["icao"] for r in _csv.DictReader(open("airfield_audit_thresholds.csv")) if r["prog_kons"]=="1"]))
def _audyt_af_dict(ap,hd):
    def _ic(a,d): return d.get("icao") or a
    AF={_ic(a,d):d for a,d in ap.items() if _ic(a,d) in AUDYT33}
    for _m in set(AUDYT33)-set(AF):
        for a,d in ap.items():
            if _ic(a,d)==_m: AF[_m]=d
    return AF
AF=[{"muni":d["muni"],"lat":d["lat"],"lon":d["lon"]} for d in _audyt_af_dict(ap,hd).values()]
g=json.load(open("voivodeship_boundaries.json")); OSR=g["osr"]; CENT=g["cent"]
WD={"dolnośląskie":(2879271,10.0,10.7,7.95,38,53),"kujawsko-pomorskie":(1996003,9.0,9.2,12.43,27,35),"lubelskie":(2011047,5.0,5.75,7.88,23,22),"lubuskie":(975023,12.0,17.94,14.25,9,21),"łódzkie":(2362519,4.0,5.36,7.55,15,22),"małopolskie":(3429632,7.0,10.56,11.08,46,54),"mazowieckie":(5510527,9.0,8.67,10.16,85,101),"opolskie":(936725,10.0,11.30,11.64,11,13),"podkarpackie":(2071676,4.0,2.84,4.80,13,16),"podlaskie":(1138216,7.0,4.28,15.71,16,27),"pomorskie":(2359573,20.0,23.87,21.62,67,55),"śląskie":(4320130,13.0,13.64,15.83,73,83),"świętokrzyskie":(1168499,4.0,5.75,5.92,23,30),"warmińsko-mazurskie":(1357910,19.0,14.89,10.95,23,27),"wielkopolskie":(3487973,15.0,11.17,15.16,57,67),"zachodniopomorskie":(1631784,13.0,8.32,12.77,40,41)}
def wS(k):
    p,a,b,c,d,e=WD[k];return (a*p/1e6+b*p/1e6+c*p/1e6+d+e)/5
VOL={"heart":{"Gdańsk":16,"Kraków":14,"Poznań":8,"Warszawa":67,"Wrocław":49,"Zabrze":48},"lungs":{"Gdańsk":48,"Kraków":2,"Poznań":7,"Szczecin":4,"Warszawa":26,"Zabrze":60},"liver":{"Bydgoszcz":39,"Gdańsk":75,"Katowice":50,"Szczecin":78,"Warszawa":365,"Wrocław":7}}
TOTV=sum(sum(v.values()) for v in VOL.values())
def hav(a,b,c,d):
    R=6371.0;p1,p2=math.radians(a),math.radians(c);dp=math.radians(c-a);dl=math.radians(d-b)
    x=math.sin(dp/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2;return 2*R*math.asin(math.sqrt(x))
def near(la,lo):
    b,bd=0,9e9
    for i,a in enumerate(AF):
        x=hav(la,lo,a["lat"],a["lon"])
        if x<bd:bd=x;b=i
    return b,bd
cair={c:near(la,lo) for c,(la,lo) in OSR.items()}
sair={k:near(la,lo) for k,(la,lo) in CENT.items()}
VS,ROUTE,TERM,ST=330.0,1.05,5/60,5/60
VHELI=240.0; ROAD,VAMB=1.35,75.0   # GEMS: road distance x1.35, ambulance at 75 km/h
def feeder(km,mode): return km/VHELI if mode=="feeder" else km*ROAD/VAMB
def stolleg(km): return km*ROUTE/VS+TERM
# minimax and typical time for a configuration (source mode, destination mode)
def run(om,dm,label):
    D=[[hav(AF[b]["lat"],AF[b]["lon"],AF[sair[k][0]]["lat"],AF[sair[k][0]]["lon"]) for b in range(len(AF))] for k in CENT]
    src=[]
    for si,(k,(la,lo)) in enumerate(CENT.items()):
        i,od=sair[k]; dworst=0;dl=None;dsum=0
        for gr,cl in VOL.items():
            for c,v in cl.items():
                ci,cd=cair[c]; t=stolleg(hav(AF[i]["lat"],AF[i]["lon"],AF[ci]["lat"],AF[ci]["lon"]))+feeder(cd,dm)
                if t>dworst:dworst=t;dl=(gr,c)
                dsum+=v*t
        src.append({"woj":k,"of":feeder(od,om),"odkm":od,"dworst":dworst,"davg":dsum/TOTV,"dl":dl,"w":wS(k)})
    best=9e9;bt=None
    for tri in combinations(range(len(AF)),3):
        mx=0
        for si,s in enumerate(src):
            pos=stolleg(min(D[si][b] for b in tri)) if min(D[si][b] for b in tri)>0.1 else 0
            T=max(s["of"],ST+pos)+s["dworst"]
            if T>mx:mx=T
            if mx>=best:break
        if mx<best:best=mx;bt=tri
    bi=max(range(len(src)),key=lambda si:max(src[si]["of"],ST+ (stolleg(min(D[si][b] for b in bt)) if min(D[si][b] for b in bt)>0.1 else 0))+src[si]["dworst"])
    s=src[bi]
    W=sum(x["w"] for x in src);wa=0
    for si,x in enumerate(src):
        pos=stolleg(min(D[si][b] for b in bt)) if min(D[si][b] for b in bt)>0.1 else 0
        wa+=x["w"]*(max(x["of"],ST+pos)+x["davg"])
    wa/=W
    fit="yes" if best*60<=240 else "NO (>4h)"
    # worst heart mission for the same triple: the overall worst case can bind
    # a centre without a heart programme, so the heart is reported separately
    hs=0;hl=None
    for si,(k,(la,lo)) in enumerate(CENT.items()):
        i,od=sair[k]
        pos=stolleg(min(D[si][b] for b in bt)) if min(D[si][b] for b in bt)>0.1 else 0
        for c in VOL["heart"]:
            ci,cd=cair[c]
            t=max(feeder(od,om),ST+pos)+stolleg(hav(AF[i]["lat"],AF[i]["lon"],AF[ci]["lat"],AF[ci]["lon"]))+feeder(cd,dm)
            if t>hs:hs=t;hl=(k,c)
    print(f"{label:16} | worst {best*60:3.0f} min | typ {wa*60:3.0f} min | binds {s['woj']}->{s['dl'][1]} (source feeder {s['odkm']:.0f}km) | below 4 h {fit} | worst heart {hs*60:3.0f} min ({hl[0]}->{hl[1]})")
    # cross-clamp to arrival for the worst heart mission: two handovers and
    # the assumed donor-side phase, as in script 09
    hz=[round(hs*60+PRZEKAZANIA+f,1) for f in FAZA_DAWCY]
    WYN[label]={"najgorszy_min":round(best*60,1),"typowy_min":round(wa*60,1),
                "wiaze":f"{s['woj']}->{s['dl'][1]}","dowoz_zrodla_km":round(s['odkm'],1),
                "serce_najgorszy_min":round(hs*60,1),"serce_wiaze":f"{hl[0]}->{hl[1]}",
                "serce_od_zacisku_do_przylotu_min":hz}
    return best*60,wa*60
WYN={}
PRZEKAZANIA=30          # two handovers of 15 min
FAZA_DAWCY=(30,60)      # assumed procurement and packing phase, min
print("HEMS helicopter 240 km/h. GEMS ambulance by road x1.35, 75 km/h. STOL 330 km/h.\n")
print(f"{'Configuration':16} | {'worst':9} | {'typical':6} | binding case | below 4 h | worst heart mission")
print("-"*128)
run("feeder","feeder","HEMS-STOL-HEMS")
run("gems","feeder","GEMS-STOL-HEMS")
run("feeder","gems","HEMS-STOL-GEMS")
run("gems","gems","GEMS-STOL-GEMS")
with open(_os.path.join(RESULTS,"feeder_configurations.json"),"w",encoding="utf-8") as f:
    json.dump(WYN,f,ensure_ascii=False,indent=1)
print(f"\nsaved {_os.path.join(RESULTS,'feeder_configurations.json')}")
