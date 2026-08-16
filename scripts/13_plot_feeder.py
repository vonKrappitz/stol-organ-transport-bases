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

import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
cfg=["HEMS-STOL-HEMS","GEMS-STOL-HEMS","HEMS-STOL-GEMS","GEMS-STOL-GEMS"]
worst=[160,190,182,212]; typ=[94,99,104,109]
x=np.arange(len(cfg)); w=0.38
fig,ax=plt.subplots(figsize=(9.2,5.6))
b1=ax.bar(x-w/2,worst,w,color="#c44e52",edgecolor="white",label="worst case",zorder=3)
b2=ax.bar(x+w/2,typ,w,color="#5b8c5a",edgecolor="white",label="typical flight (demand-weighted)",zorder=3)
for b in list(b1)+list(b2): ax.text(b.get_x()+b.get_width()/2,b.get_height()+2.5,f"{int(b.get_height())}",ha="center",fontsize=11,weight="bold",color="#1a1a2e")
ax.axhline(240,ls="--",color="#8a1010",lw=1.3,zorder=2)
ax.text(-0.45,243,"4 h transport-only reference, not full CIT",ha="left",fontsize=9.5,color="#8a1010",weight="bold")
ax.set_xticks(x);ax.set_xticklabels(cfg,fontsize=10.5)
ax.set_ylabel("time, minutes",fontsize=11);ax.set_ylim(0,300)
ax.set_title("Sensitivity to feeder means, four leg configurations\nHEMS helicopter 240 km/h, GEMS ambulance road x1.35 at 75 km/h, middle STOL",fontsize=12,weight="bold",color="#1a1a2e")
ax.legend(fontsize=10,frameon=False,loc="upper center",bbox_to_anchor=(0.5,-0.10),ncol=2)
ax.spines["top"].set_visible(False);ax.spines["right"].set_visible(False);ax.grid(axis="y",alpha=0.25,zorder=0)
ax.tick_params(labelsize=10)
plt.tight_layout();plt.savefig(_os.path.join(RESULTS, "map_feeder_configurations.png"),dpi=350,bbox_inches="tight");plt.close()
print("OK pflt konfiguracji feeder")
