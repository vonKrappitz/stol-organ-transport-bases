# --- paths: paths relative to the repository (runs from any working directory) ---
import os as _os
try:
    _SKRYPT_DIR = _os.path.dirname(_os.path.abspath(__file__))
except NameError:
    _SKRYPT_DIR = _os.path.dirname(_os.path.abspath(_os.sys.argv[0])) or _os.getcwd()
_REPRO_DIR  = _os.path.dirname(_SKRYPT_DIR)          # repository root
_DANE_DIR   = _os.path.join(_REPRO_DIR, "data")
RESULTS      = _os.path.join(_REPRO_DIR, "results")     # output folder
_os.makedirs(RESULTS, exist_ok=True)
_os.chdir(_DANE_DIR)                                  # bare paths read from data/
# --- end of the path block ---

# --- the script skips itself when the National Health Fund data are missing ---
import os as _os2, sys as _sys2
_nfz = _os2.path.join(_DANE_DIR, "nhf_interhospital_transport_2020_2024.xlsx")
_nfzc = _os2.path.join(_DANE_DIR, "nhf_transport_od.csv")
if not _os2.path.exists(_nfz) and not _os2.path.exists(_nfzc):
    print("=" * 68)
    print("National Health Fund data file not found in data/.")
    print("See data/NHF_transport_data.md for the file name and provenance")
    print("The core results reproduce without them from the other scripts. Skipping.")
    print("=" * 68)
    _sys2.exit(0)
# --- end of the data check ---

# Correlation of the proxy (source donors x target transplants) with the
# observed matrix of inter-hospital transport (data/nhf_transport_od.csv).
# Three carriers: (a) pairs with any disclosed count, (b) pairs present with censored cells as 2,
# (c) all 240 ordered pairs with zeros for the absent ones.
import csv, json, math
from collections import defaultdict
from scipy.stats import spearmanr, kendalltau

# --- proxy, as in scripts 02 and 05 ---
WD={"dolnośląskie":(2879271,10.0,10.7,7.95,38,53),"kujawsko-pomorskie":(1996003,9.0,9.2,12.43,27,35),
"lubelskie":(2011047,5.0,5.75,7.88,23,22),"lubuskie":(975023,12.0,17.94,14.25,9,21),
"łódzkie":(2362519,4.0,5.36,7.55,15,22),"małopolskie":(3429632,7.0,10.56,11.08,46,54),
"mazowieckie":(5510527,9.0,8.67,10.16,85,101),"opolskie":(936725,10.0,11.30,11.64,11,13),
"podkarpackie":(2071676,4.0,2.84,4.80,13,16),"podlaskie":(1138216,7.0,4.28,15.71,16,27),
"pomorskie":(2359573,20.0,23.87,21.62,67,55),"śląskie":(4320130,13.0,13.64,15.83,73,83),
"świętokrzyskie":(1168499,4.0,5.75,5.92,23,30),"warmińsko-mazurskie":(1357910,19.0,14.89,10.95,23,27),
"wielkopolskie":(3487973,15.0,11.17,15.16,57,67),"zachodniopomorskie":(1631784,13.0,8.32,12.77,40,41)}
def dawcy(k):
    p,a,b,c,d,e=WD[k]; return (a*p/1e6+b*p/1e6+c*p/1e6+d+e)/5
VOL={"heart":{"Gdańsk":16,"Kraków":14,"Poznań":8,"Warszawa":67,"Wrocław":49,"Zabrze":48},
"lungs":{"Gdańsk":48,"Kraków":2,"Poznań":7,"Szczecin":4,"Warszawa":26,"Zabrze":60},
"liver":{"Bydgoszcz":39,"Gdańsk":75,"Katowice":50,"Szczecin":78,"Warszawa":365,"Wrocław":7}}
M2W={"Gdańsk":"pomorskie","Kraków":"małopolskie","Poznań":"wielkopolskie","Warszawa":"mazowieckie",
"Wrocław":"dolnośląskie","Zabrze":"śląskie","Katowice":"śląskie","Szczecin":"zachodniopomorskie",
"Bydgoszcz":"kujawsko-pomorskie"}
przesz=defaultdict(float)
for gr in VOL.values():
    for c,v in gr.items(): przesz[M2W[c]] += v
WOJ=sorted(WD)
def proxy(i,j): return dawcy(i)*przesz.get(j,0.0)

# --- observed transport ---
rows=list(csv.DictReader(open('nhf_transport_od.csv',encoding='utf-8')))
obs_num=defaultdict(int); obs_c2=defaultdict(int); ma_jawna=set()
for r in rows:
    wy,pr=r['voivodeship_from'].lower(),r['voivodeship_to'].lower()
    if wy==pr: continue
    k=(wy,pr)
    if r['censored_below_5']=='1': obs_c2[k]+=2
    else:
        obs_num[k]+=int(r['services']); obs_c2[k]+=int(r['services']); ma_jawna.add(k)

def korr(pairs, obs):
    xs=[proxy(*k) for k in pairs]; ys=[obs.get(k,0) for k in pairs]
    rs,ps=spearmanr(xs,ys); rt,pt=kendalltau(xs,ys)
    return len(pairs), rs, ps, rt, pt

warianty=[
 ("(a) pary z liczba jawna",        sorted(ma_jawna),                                  obs_num),
 ("(b) pary wystepujace, cenz=2",   sorted(obs_c2),                                    obs_c2),
 ("(c) wszystkie 240 par, zera",    [(i,j) for i in WOJ for j in WOJ if i!=j],         obs_c2),
]
print(f"{'carrier':34} {'n':>4} {'Spearman':>9} {'p':>9} {'Kendall':>8} {'p':>9}")
# The variant names are keys of the result file and stay as they are. The
# printout uses their English reading.
_EN={"(a) pary z liczba jawna":"(a) pairs with a disclosed count","(b) pary wystepujace, cenz=2":"(b) pairs that occur, censored=2","(c) wszystkie 240 par, zera":"(c) all 240 pairs, zeros"}
for nazwa,pairs,obs in warianty:
    n,rs,ps,rt,pt=korr(pairs,obs)
    print(f"{_EN[nazwa]:34} {n:>4} {rs:>9.4f} {ps:>9.2g} {rt:>8.4f} {pt:>9.2g}")

# also: does the observation correlate with distance alone (decay with distance)
cent=json.load(open('voivodeship_boundaries.json'))['cent']
def hav(a,b,c,d):
    R=6371.0;p1,p2=math.radians(a),math.radians(c);dp=math.radians(c-a);dl=math.radians(d-b)
    x=math.sin(dp/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2;return 2*R*math.asin(math.sqrt(x))
pairs=sorted(obs_c2)
ds=[hav(*cent[i],*cent[j]) for i,j in pairs]; ys=[obs_c2[k] for k in pairs]
rs,ps=spearmanr(ds,ys)
print(f"\nobservation against centroid distance (pairs present): Spearman {rs:.4f} (p={ps:.2g})")
# and the proxy against distance, for contrast
xs=[proxy(*k) for k in pairs]
rs2,ps2=spearmanr(ds,xs)
print(f"proxy against distance (same pairs): Spearman {rs2:.4f} (p={ps2:.2g})")

# --- machine-readable results ---
# The block below computes nothing new. It repeats korr() and spearmanr on the
# same pairs as the loop above.
_k = {"warianty": {}, "wobec_odleglosci": {}}
for _nazwa, _pairs, _obs in warianty:
    _n, _rs, _ps, _rt, _pt = korr(_pairs, _obs)
    _k["warianty"][_nazwa] = {"n": _n, "spearman": round(_rs, 4), "p_spearman": _ps,
                              "kendall": round(_rt, 4), "p_kendall": _pt}
_k["wobec_odleglosci"] = {
    "obserwacja_vs_odleglosc": {"spearman": round(rs, 4), "p": ps, "n": len(pairs)},
    "proxy_vs_odleglosc": {"spearman": round(rs2, 4), "p": ps2, "n": len(pairs)},
}
with open(_os.path.join(RESULTS, "correlations.json"), "w", encoding="utf-8") as _f:
    json.dump(_k, _f, ensure_ascii=False, indent=2)
print(f"  saved results/correlations.json")
