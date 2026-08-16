# Licences for data and figures

The code in `scripts/` is licensed under the Apache License 2.0, see `LICENSE`.
Data and figures are covered separately, as set out below.

## Our own work

The infrastructure audit files `airfield_audit_thresholds.csv`,
`airfield_audit_certified.csv` and `airfield_audit_military.csv`, everything in
`results/`, and every figure in `figures/` are released under the
**Creative Commons Attribution 4.0 International licence (CC BY 4.0)**.

You may share and adapt them, including commercially, provided you give credit
and indicate any changes. Full text: https://creativecommons.org/licenses/by/4.0/

## Third-party inputs

**`airports.csv`, `runways.csv`** come from OurAirports
(https://ourairports.com/data/). OurAirports places its data in the public
domain. They are redistributed here unchanged so that the run is reproducible
offline.

**`voivodeship_boundaries.json`** is derived from open administrative boundary
data and is cached here for the same reason.

**`nhf_interhospital_transport_2020_2024.xlsx`** and the accompanying release
letter come from the National Health Fund of Poland, released on 17 July 2026
under case NFZ-DAMJiOS.0143.264.2026 in answer to a request for public
information. They are reproduced here unaltered as public sector information,
re-used under the Polish regime for the re-use of public sector information. The
Fund was notified of this deposit and raised no objection.

Credit the source, the release date, and the case reference. See
`data/NHF_transport_data.md` for the full provenance and contents.

The derived file `nhf_transport_od.csv` is produced by script 16 and is not
versioned.

## Third-party data included here

**`data/wojewodztwa.geojson`**, the voivodeship boundaries, comes from the
polska-geojson project by Piotr Patrzyk, https://github.com/ppatrzyk/polska-geojson,
and is used under the MIT Licence. The full notice is in
`data/BOUNDARIES_LICENCE.md`. It is stored here so that the map scripts run
without network access.
