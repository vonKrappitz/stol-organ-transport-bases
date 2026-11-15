# Licences for data and figures

The code in `scripts/` is licensed under the Apache License 2.0, see `LICENSE`.
Data and figures are covered separately, as set out below.

## Our own work

The infrastructure audit files `airfield_audit_thresholds.csv`,
`airfield_audit_certified.csv`, `airfield_audit_military.csv` and
`airfield_audit_individual.csv`, everything in
`results/`, and every figure in `figures/` are released under the
**Creative Commons Attribution 4.0 International licence (CC BY 4.0)**.

You may share and adapt them, including commercially, provided you give credit
and indicate any changes. Full text: https://creativecommons.org/licenses/by/4.0/

## Third-party inputs

**`airports.csv`, `runways.csv`** come from OurAirports
(https://ourairports.com/data/). OurAirports places its data in the public
domain. They are redistributed here unchanged so that the run is reproducible
offline.

**`voivodeship_boundaries.json`** holds the voivodeship centroids, computed
from the boundary file listed below, and the coordinates of the transplant
centres, geocoded through Nominatim from OpenStreetMap. It is cached here for
the same reason. The centre coordinates are © OpenStreetMap contributors and
are available under the Open Database Licence, see
https://www.openstreetmap.org/copyright.

**`nhf_interhospital_transport_2020_2024.xlsx`** and the accompanying release
letter come from the National Health Fund of Poland, released on 17 July 2026
under case NFZ-DAMJiOS.0143.264.2026 in answer to a request for public
information. They are reproduced here unaltered as public sector information,
re-used under the Polish regime for the re-use of public sector information. The
Fund was notified of this deposit and raised no objection.

Credit the source, the release date, and the case reference. The file metadata
date its creation to 16 July 2026. The files `results/correlations.json`,
`results/distance_profile.json` and `figures/map_distance_profile.png` are our
own processing of this dataset. See `data/NHF_transport_data.md` for the full
provenance and contents.

The derived file `nhf_transport_od.csv` is produced by script 16 and is not
versioned.

**Donor counts and transplant volumes** written into the scripts, and the list
in `figures/donor_hospital_list.md`, come from the Poltransplant report
*Pobieranie i przeszczepianie narządów w Polsce 2024*, Tables 5, 7, 18, 19 and
20, and from the Poltransplant bulletins. Both are cited in the paper.

**Population figures** written into the scripts are those of Statistics Poland
(GUS) for 31 December 2023.

**`hospital_cities.json`** holds the coordinates of the fourteen cities of the
donor hospitals. They are commonly published city-centre coordinates, typed in
by hand.

## Third-party data included here

**`data/wojewodztwa.geojson`**, the voivodeship boundaries, comes from the
polska-geojson project by Piotr Patrzyk, https://github.com/ppatrzyk/polska-geojson,
and is used under the MIT Licence. The full notice is in
`data/BOUNDARIES_LICENCE.md`. It is stored here so that the map scripts run
without network access.
