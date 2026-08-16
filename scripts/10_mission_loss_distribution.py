# Copyright 2026 Maciej M. Kasperek. Licensed under the Apache License, Version 2.0.
# paths relative to the repository root
import os as _os
try:
    _SCRIPT_DIR = _os.path.dirname(_os.path.abspath(__file__))
except NameError:
    _SCRIPT_DIR = _os.path.dirname(_os.path.abspath(_os.sys.argv[0])) or _os.getcwd()
_REPO_DIR  = _os.path.dirname(_SCRIPT_DIR)          # repository root
_DATA_DIR   = _os.path.join(_REPO_DIR, "data")
RESULTS      = _os.path.join(_REPO_DIR, "figures")     # figures and CSV go here
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
g=json.load(open("voivodeship_boundaries.json", encoding="utf-8")); OSR=g["osr"]; CENT=g["cent"]
WD={"dolnośląskie":(2879271,10.0,10.7,7.95,38,53),"kujawsko-pomorskie":(1996003,9.0,9.2,12.43,27,35),"lubelskie":(2011047,5.0,5.75,7.88,23,22),"lubuskie":(975023,12.0,17.94,14.25,9,21),"łódzkie":(2362519,4.0,5.36,7.55,15,22),"małopolskie":(3429632,7.0,10.56,11.08,46,54),"mazowieckie":(5510527,9.0,8.67,10.16,85,101),"opolskie":(936725,10.0,11.30,11.64,11,13),"podkarpackie":(2071676,4.0,2.84,4.80,13,16),"podlaskie":(1138216,7.0,4.28,15.71,16,27),"pomorskie":(2359573,20.0,23.87,21.62,67,55),"śląskie":(4320130,13.0,13.64,15.83,73,83),"świętokrzyskie":(1168499,4.0,5.75,5.92,23,30),"warmińsko-mazurskie":(1357910,19.0,14.89,10.95,23,27),"wielkopolskie":(3487973,15.0,11.17,15.16,57,67),"zachodniopomorskie":(1631784,13.0,8.32,12.77,40,41)}
def wS(k):
    p,a,b,c,d,e=WD[k];return (a*p/1e6+b*p/1e6+c*p/1e6+d+e)/5
VOL={"heart":{"Gdańsk":16,"Kraków":14,"Poznań":8,"Warszawa":67,"Wrocław":49,"Zabrze":48},"lungs":{"Gdańsk":48,"Kraków":2,"Poznań":7,"Szczecin":4,"Warszawa":26,"Zabrze":60},"liver":{"Bydgoszcz":39,"Gdańsk":75,"Katowice":50,"Szczecin":78,"Warszawa":365,"Wrocław":7}}
def hav(a,b,c,d):
    R=6371.0;p1,p2=math.radians(a),math.radians(c);dp=math.radians(c-a);dl=math.radians(d-b)
    x=math.sin(dp/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2;return 2*R*math.asin(math.sqrt(x))
VH=240.0

import csv as _csv
_TROJKA=["EPBY","EPML","EPSY"]
_CERT13=["EPWA","EPGD","EPKT","EPKK","EPLL","EPPO","EPRZ","EPSC","EPMO","EPWR","EPZG","EPLB","EPRA"]
_ad4rows={r["icao"]:r for r in _csv.DictReader(open("airfield_audit_thresholds.csv", encoding="utf-8"))}
AUDYT33=sorted(set(_TROJKA+_CERT13+[ic for ic,r in _ad4rows.items() if r["prog_kons"]=="1"]))
AUDYT_TWARDE={**{ic:9999 for ic in _CERT13+_TROJKA},"EPBK":1350,**{ic:int(r["tw_max"] or 0) for ic,r in _ad4rows.items() if r["prog_kons"]=="1"}}
def net(minr):
    if minr=="AUDYT33":
        AF=[a for a in ALL if a["icao"] in AUDYT33]
        _braki=set(AUDYT33)-{a["icao"] for a in AF}
        for _ic in _braki:
            for a2,d2 in ap.items():
                if d2["icao"]==_ic: AF.append({"icao":_ic,"muni":d2["muni"],"lat":d2["lat"],"lon":d2["lon"],"len":AUDYT_TWARDE.get(_ic,0)})
    else:
        AF=[a for a in ALL if a["icao"] in AUDYT_TWARDE and AUDYT_TWARDE[a["icao"]]>=minr]
    def near(la,lo):
        b,bd=0,9e9
        for i,a in enumerate(AF):
            x=hav(la,lo,a["lat"],a["lon"])
            if x<bd:bd=x;b=i
        return b,bd
    return AF,near
def setup(minr,VS,rf,term,act):
    AF,near=net(minr)
    cair={c:near(la,lo) for c,(la,lo) in OSR.items()}
    sair={k:near(la,lo) for k,(la,lo) in CENT.items()}
    def flt(km):return (km*rf)/VS+term/60
    # minimax bases
    srcw=[]
    for k,(la,lo) in CENT.items():
        i,d=sair[k];dw=0
        for gr,cl in VOL.items():
            for c in cl: 
                ci,cd=cair[c];t=flt(hav(AF[i]["lat"],AF[i]["lon"],AF[ci]["lat"],AF[ci]["lon"]))+cd/VH
                dw=max(dw,t)
        srcw.append((k,i,d/VH,dw))
    D=[[hav(AF[b]["lat"],AF[b]["lon"],AF[i]["lat"],AF[i]["lon"]) for b in range(len(AF))] for _,i,_,_ in srcw]
    best=9e9;bt=None
    for tri in combinations(range(len(AF)),3):
        mx=0
        for si,(k,i,h,dw) in enumerate(srcw):
            pd=min(D[si][b] for b in tri);pos=flt(pd) if pd>0.1 else 0
            T=max(h,act/60+pos)+dw;mx=max(mx,T)
            if mx>=best:break
        if mx<best:best=mx;bt=tri
    return AF,near,cair,sair,flt,bt,act
def mtime(k,gr,c,S):
    AF,near,cair,sair,flt,bt,act=S
    i,hO=sair[k];ci,hC=cair[c]
    pd=min(hav(AF[b]["lat"],AF[b]["lon"],AF[i]["lat"],AF[i]["lon"]) for b in bt);pos=flt(pd) if pd>0.1 else 0
    return max(hO/VH,act/60+pos)+flt(hav(AF[i]["lat"],AF[i]["lon"],AF[ci]["lat"],AF[ci]["lon"]))+hC/VH, hav(AF[i]["lat"],AF[i]["lon"],AF[ci]["lat"],AF[ci]["lon"])
ST=setup("AUDYT33",330,1.05,5,5)      # STOL VFR
PP=setup(1100,700,1.12,18,10)   # P180 IFR
# enumeration of demand-weighted pairs
rows=[]
for gr,cl in VOL.items():
    for c,v in cl.items():
        for k in CENT:
            w=wS(k)*v
            ts,dist=mtime(k,gr,c,ST); tp,_=mtime(k,gr,c,PP)
            rows.append((w,dist,ts*60,tp*60,(ts-tp)*60))
W=sum(r[0] for r in rows)
def share(pred): return 100*sum(r[0] for r in rows if pred(r))/W
print("distribution mission weighted DEMAND (S_i x volume organ), pary source-centre\n")
print("distance flight (airfield-airfield), share demand:")
for lo,hi in [(0,200),(200,350),(350,500),(500,9999)]:
    lbl=f"{lo}-{hi} km" if hi<9999 else f">{lo} km"
    print(f"  {lbl:12} {share(lambda r,a=lo,b=hi: a<=r[1]<b):5.1f}%")
md=sorted(rows,key=lambda r:r[1]); cum=0
for r in md:
    cum+=r[0]
    if cum>=W/2: print(f"\nDemand-weighted median flight distance: {r[1]:.0f} km"); break
print("\nLoss of the STOL against the P180 (STOL time minus P180), share of demand:")
for lo,hi,lbl in [(-999,0,"STOL faster"),(0,5,"0-5 min"),(5,10,"5-10 min"),(10,20,"10-20 min"),(20,9999,">20 min")]:
    print(f"  {lbl:14} {share(lambda r,a=lo,b=hi: a<=r[4]<b):5.1f}%")
wmean=sum(r[0]*r[4] for r in rows)/W
print(f"\nDemand-weighted mean loss of the STOL: {wmean:.1f} min")
print(f"Share of demand where the STOL loses at most 10 min: {share(lambda r: r[4]<10):.1f}%")
print(f"Share of demand with a flight over 500 km (the diagonal): {share(lambda r: r[1]>500):.1f}%")

# --- plot, demand-weighted ---
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
bins=[("STOL\nfaster",-999,0),("0–5\nmin",0,5),("5–10\nmin",5,10),("10–20\nmin",10,20),(">20\nmin",20,9999)]
vals=[share(lambda r,a=a,b=b: a<=r[4]<b) for _,a,b in bins]
cols=["#2a9d4a","#5cb85c","#9acd6e","#f0ad4e","#d9534f"]
fig,ax=plt.subplots(figsize=(8.6,5.4))
bars=ax.bar([b[0] for b in bins],vals,color=cols,edgecolor="white",width=0.72,zorder=3)
for bar,v in zip(bars,vals): ax.text(bar.get_x()+bar.get_width()/2,v+0.7,f"{v:.0f}%",ha="center",fontsize=12,weight="bold",color="#1a1a2e")
ax.axvspan(-0.5,2.5,color="#2a9d4a",alpha=0.07,zorder=0)
ax.text(2.0,max(vals)*0.86,f"STOL keeps pace\n(loss ≤10 min or faster): {share(lambda r: r[4]<10):.0f}%",ha="center",va="top",fontsize=10.5,color="#1f6b33",weight="bold")
ax.set_ylabel("demand share",fontsize=11);ax.set_ylim(0,max(vals)*1.18)
ax.set_title(f"Loss of STOL VFR against P180 IFR, demand-weighted\nmean loss {wmean:.1f} min, diagonal >500 km is only {share(lambda r: r[1]>500):.1f}% of traffic",fontsize=12.5,weight="bold",color="#1a1a2e")
ax.spines["top"].set_visible(False);ax.spines["right"].set_visible(False);ax.tick_params(labelsize=10.5)
ax.grid(axis="y",alpha=0.25,zorder=0)
plt.tight_layout();plt.savefig(_os.path.join(RESULTS, "map_mission_loss.png"),dpi=350,bbox_inches="tight");plt.close()
print("\nOK pflt rozkladu")

# --- machine-readable results ---
import json as _json
_d = {"mean_loss_min": round(wmean, 1),
      "share_loss_under_10min_pct": round(share(lambda r: r[4] < 10), 1),
      "share_flight_over_500km_pct": round(share(lambda r: r[1] > 500), 1),
      "bands": {b[0].replace("\n", " "): round(v, 1) for b, v in zip(bins, vals)}}
with open(_os.path.join(_os.path.join(_REPO_DIR, "results"), "mission_loss_distribution.json"), "w", encoding="utf-8") as _f:
    _json.dump(_d, _f, ensure_ascii=False, indent=2)
print("  saved results/mission_loss_distribution.json")