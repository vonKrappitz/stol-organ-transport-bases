# Copyright 2026 Maciej M. Kasperek. Licensed under the Apache License, Version 2.0.
import json, requests, time
from shapely.geometry import shape
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

# 16 centroids from the voivodeship boundaries (GeoJSON)
urls=["https://raw.githubusercontent.com/ppatrzyk/polska-geojson/master/wojewodztwa/wojewodztwa-medium.geojson",
      "https://raw.githubusercontent.com/ppatrzyk/polska-geojson/master/wojewodztwa/wojewodztwa-max.geojson"]
gj=None
for u in urls:
    try:
        r=requests.get(u,timeout=30); r.raise_for_status(); gj=r.json(); print("geojson OK:",u.split('/')[-1]); break
    except Exception as e: print("fail",u.split('/')[-1],e)
cent={}
if gj:
    for ft in gj["features"]:
        nm=ft["properties"].get("nazwa") or ft["properties"].get("name") or str(ft["properties"])
        c=shape(ft["geometry"]).centroid
        cent[nm.lower()]=(round(c.y,4),round(c.x,4))
    print("\n--- voivodeship centroids ---")
    for k,v in sorted(cent.items()): print(f"  {k:22} {v[0]:.4f},{v[1]:.4f}")

# 9 centres (geocoding)
geoloc=Nominatim(user_agent="lpr_stol_research_kasperek")
gc=RateLimiter(geoloc.geocode,min_delay_seconds=1.1)
centra=["Bydgoszcz","Gdańsk","Katowice","Kraków","Poznań","Szczecin","Warszawa","Wrocław","Zabrze"]
print("\n--- centres ---")
osr={}
for c in centra:
    loc=gc(c+", Polska")
    if loc: osr[c]=(round(loc.latitude,4),round(loc.longitude,4)); print(f"  {c:12} {loc.latitude:.4f},{loc.longitude:.4f}")
    else: print(f"  {c:12} MISSING")

json.dump({"cent":cent,"osr":osr},open("voivodeship_boundaries.json","w", encoding="utf-8"))
print("\nwritten voivodeship_boundaries.json | centroids:",len(cent),"| centres:",len(osr))
