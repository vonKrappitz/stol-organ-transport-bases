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

import csv, re, json, math
from itertools import combinations
keep={"small_airport","medium_airport","large_airport"}
ap={}
with open("airports.csv",newline='',encoding="utf-8") as f:
    for r in csv.DictReader(f):
        if r["iso_country"]!="PL" or r["type"] not in keep: continue
        ap[r["ident"]]={"icao":r["icao_code"] or r["ident"],"muni":r["municipality"] or r["name"],"lat":float(r["latitude_deg"]),"lon":float(r["longitude_deg"]),"rw":[]}
HARD=re.compile(r"asph|ashp|aspha|\basp\b|conc|\bcon\b|cement|bitum|tarmac|\btar\b|paved|\bpav|\bpem\b|sealed|\bseal\b|composite|\bcop\b|\bhard\b|macadam|\bpcn\b",re.I)
SOFT=re.compile(r"grass|\bgrs\b|turf|\bgvl\b|gravel|dirt|sand|soil|earth|clay|snow|\bice\b|water|\bsod\b|\bgre\b|unpaved|natural",re.I)
def hd(s):
    if not s:return False
    if SOFT.search(s) and not HARD.search(s):return False
    return bool(HARD.search(s))
with open("runways.csv",newline='',encoding="utf-8") as f:
    for r in csv.DictReader(f):
        a=r["airport_ident"]
        if a not in ap or r["closed"]=="1":continue
        try:ln=int(r["length_ft"])
        except:continue
        ap[a]["rw"].append((ln,r["surface"]))
ALL=[{"icao":d["icao"],"muni":d["muni"],"lat":d["lat"],"lon":d["lon"],"len":max([l for l,s in d["rw"] if hd(s)])*0.3048} for a,d in ap.items() if [l for l,s in d["rw"] if hd(s)]]

# audited set (snapshot 2026-07-18): main conservative set of 33
import csv as _csv
_TROJKA=["EPBY","EPML","EPSY"]
_CERT13=["EPWA","EPGD","EPKT","EPKK","EPLL","EPPO","EPRZ","EPSC","EPMO","EPWR","EPZG","EPLB","EPRA"]
_ad4k=[r["icao"] for r in _csv.DictReader(open("airfield_audit_thresholds.csv", encoding="utf-8")) if r["prog_kons"]=="1"]
AUDYT33=sorted(set(_TROJKA+_CERT13+_ad4k))

# hard after audit: certified13 + triple + conservative AD4 with a hard runway + EPBK(1350)
_ad4rows={r["icao"]:r for r in _csv.DictReader(open("airfield_audit_thresholds.csv", encoding="utf-8"))}
AUDYT_TWARDE_OK=set(_CERT13+_TROJKA+["EPBK"]+[ic for ic,r in _ad4rows.items() if r["prog_kons"]=="1" and int(r["tw_max"] or 0)>=875])
g=json.load(open("voivodeship_boundaries.json", encoding="utf-8")); OSR=g["osr"]; CENT=g["cent"]
WD={"dolnośląskie":(2879271,10.0,10.7,7.95,38,53),"kujawsko-pomorskie":(1996003,9.0,9.2,12.43,27,35),"lubelskie":(2011047,5.0,5.75,7.88,23,22),"lubuskie":(975023,12.0,17.94,14.25,9,21),"łódzkie":(2362519,4.0,5.36,7.55,15,22),"małopolskie":(3429632,7.0,10.56,11.08,46,54),"mazowieckie":(5510527,9.0,8.67,10.16,85,101),"opolskie":(936725,10.0,11.30,11.64,11,13),"podkarpackie":(2071676,4.0,2.84,4.80,13,16),"podlaskie":(1138216,7.0,4.28,15.71,16,27),"pomorskie":(2359573,20.0,23.87,21.62,67,55),"śląskie":(4320130,13.0,13.64,15.83,73,83),"świętokrzyskie":(1168499,4.0,5.75,5.92,23,30),"warmińsko-mazurskie":(1357910,19.0,14.89,10.95,23,27),"wielkopolskie":(3487973,15.0,11.17,15.16,57,67),"zachodniopomorskie":(1631784,13.0,8.32,12.77,40,41)}
def wgt(k):
    p,a,b,c,d,e=WD[k];return (a*p/1e6+b*p/1e6+c*p/1e6+d+e)/5
VOL={"heart":{"Gdańsk":16,"Kraków":14,"Poznań":8,"Warszawa":67,"Wrocław":49,"Zabrze":48},"lungs":{"Gdańsk":48,"Kraków":2,"Poznań":7,"Szczecin":4,"Warszawa":26,"Zabrze":60},"liver":{"Bydgoszcz":39,"Gdańsk":75,"Katowice":50,"Szczecin":78,"Warszawa":365,"Wrocław":7}}
TOTV=sum(sum(v.values()) for v in VOL.values())
def hav(a,b,c,d):
    R=6371.0;p1,p2=math.radians(a),math.radians(c);dp=math.radians(c-a);dl=math.radians(d-b)
    x=math.sin(dp/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2;return 2*R*math.asin(math.sqrt(x))
VH=240.0

def run(minrwy,VS,rf,term,label,act=5):
    ST=act/60
    if minrwy=="AUDYT33":
        AF=[a for a in ALL if a["icao"] in AUDYT33]
        _braki=set(AUDYT33)-{a["icao"] for a in AF}
        for _ic in _braki:
            for a2,d2 in ap.items():
                if d2["icao"]==_ic:
                    AF.append({"icao":_ic,"muni":d2["muni"],"lat":d2["lat"],"lon":d2["lon"],"len":1350 if _ic=="EPBK" else 0})
    else:
        AF=[a for a in ALL if a["len"]>=minrwy and a["icao"] in AUDYT_TWARDE_OK]
    def near(la,lo):
        bi,bd=0,9e9
        for i,a in enumerate(AF):
            x=hav(la,lo,a["lat"],a["lon"])
            if x<bd:bd=x;bi=i
        return bi,bd
    cair={c:near(la,lo) for c,(la,lo) in OSR.items()}
    def flt(km):  # czas lotu STOL/jet z trasa i narzutem terminalowym
        return (km*rf)/VS + term/60
    src=[]
    for k,(la,lo) in CENT.items():
        i,d=near(la,lo); dworst=0; dsum=0
        for gr,cl in VOL.items():
            for c,v in cl.items():
                ci,cd=cair[c]
                term_=flt(hav(AF[i]["lat"],AF[i]["lon"],AF[ci]["lat"],AF[ci]["lon"]))+cd/VH
                if term_>dworst:dworst=term_
                dsum+=v*term_
        src.append({"woj":k,"ai":i,"feeder":d/VH,"helikm":d,"dworst":dworst,"davg":dsum/TOTV,"w":wgt(k)})
    bads=[s["woj"] for s in src if s["helikm"]>100]+[c for c in OSR if cair[c][1]>100]
    D=[[hav(AF[b]["lat"],AF[b]["lon"],AF[s["ai"]]["lat"],AF[s["ai"]]["lon"]) for b in range(len(AF))] for s in src]
    W=sum(s["w"] for s in src)
    best=9e9;bt=None
    for tri in combinations(range(len(AF)),3):
        mx=0
        for si,s in enumerate(src):
            pd=min(D[si][b] for b in tri)
            pos=flt(pd) if pd>0.1 else 0
            T=max(s["feeder"],ST+pos)+s["dworst"]
            if T>mx:mx=T
            if mx>=best:break
        if mx<best:best=mx;bt=tri
    # demand-weighted mean for the best triple
    wa=0
    for si,s in enumerate(src):
        pd=min(D[si][b] for b in bt); pos=flt(pd) if pd>0.1 else 0
        wa+=s["w"]*(max(s["feeder"],ST+pos)+s["davg"])
    wa/=W
    bz=", ".join(AF[b]["muni"][:11] for b in bt)
    print(f"{label:24} | flt {len(AF):2d} | worst {best*60:3.0f} min | w.mean {wa*60:3.0f} min | coverage {'full' if not bads else 'GAP '+str(bads)} | bases {bz}")
    return best*60,wa*60

print("Parameters: feeder 240 km/h, start-up 5 min. Activation Caravan 5 min, P180 10 min, Learjet 12 min (single- vs twin-pilot, engine count).\n")
print(f"{'aircraft':24} | {'flight':3} | {'worst':9} | {'w.mean':6} | coverage | bases")
print("-"*120)
run("AUDYT33", 330, 1.05, 5,  "STOL Caravan EX VFR", act=5)
run("AUDYT33", 330, 1.12, 18, "STOL Caravan EX IFR", act=5)
run(1100,700, 1.12, 18, "Piaggio P180 IFR", act=10)
run(1536,800, 1.12, 18, "Learjet 45 IFR", act=12)
