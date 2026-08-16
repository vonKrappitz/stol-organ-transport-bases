# STOL Organ Transport Bases — Reproduction Package

Code, input data, and results reproducing every number and every figure in the manuscript *"Facility Location under a Partially Identified Demand Coupling: Aircraft Bases for Time-Critical Organ Transport in Poland"*.

**Author:** Maciej M. Kasperek (ORCID 0009-0008-7419-0851)
**Contact:** maciej_kasperek@protonmail.ch

**Polish version:** [README_PL.md](README_PL.md)

## Main result

With three bases the worst-case mission time is **143.5 min** (main model, 33 airfields after an infrastructure audit), bases: **Bialystok-Krywlany (EPBK), Bydgoszcz (EPBY), Mielec (EPML)**. The optimum is invariant across the whole Frechet class of demand couplings — the location decision holds even though the donor-recipient matrix is not recorded.

## Repository structure

```
.
├── README.md                # this file
├── README_PL.md             # Polish version
├── LICENSE                  # Apache 2.0 (code)
├── LICENSE-DATA.md          # licences for data and figures
├── CITATION.cff             # citation metadata
├── requirements.txt         # Python dependencies
├── run_all.sh               # reproduce everything with one command
├── data/                    # input data
├── scripts/                 # 29 Python scripts (01-29)
├── results/                 # numerical results (JSON/CSV)
└── figures/                 # figures (PNG)
```

## Reproduce from scratch

```bash
pip install -r requirements.txt      # Python 3.10+
bash run_all.sh                      # runs every script, then checks the outputs
```

Scripts read from `data/`, write numbers to `results/` and figures to
`figures/`. They use paths relative to the repository root, so they run from
any working directory. **No network access is needed** — all inputs are in
`data/` (exception: the optional geocoding script 03, see below).

## What each script does

| Script | Computes | Output |
|---|---|---|
| 01_filter_airfields.py | Airfield set after runway/infrastructure audit | data/stol_candidates_final.csv |
| 02_demand_weights.py | Source weights from donor margins | (console) |
| 03_geocoding.py | Voivodeship centroids (optional, cached) | data/voivodeship_boundaries.json |
| 04_minimax.py | Minimax (p-center) optimum, 5456 triples | (console) |
| 05_compare_methods.py | Four location models side by side | results/compare_methods.json |
| 06_maps_main.py | Maps: minimax placement, four methods | figures/*.png |
| 07_maps_reach_circles.py | Helicopter reach, positioning zones | figures/*.png |
| 08_map_donor_hospitals.py | Donor hospital map | figures/map_donor_hospitals.png |
| 09_aircraft_classes.py | Four aircraft classes, day variant | (console) |
| 10_mission_loss_distribution.py | Mission time loss distribution | results/mission_loss_distribution.json |
| 11_cost_per_mission.py | Operating cost per mission | results/cost_per_mission.json |
| 12_feeder_configurations.py | HEMS/GEMS feeder configurations | (console) |
| 13_plot_feeder.py | Feeder configuration chart | figures/map_feeder_configurations.png |
| 14_map_merged_coverage.py | Merged coverage map | figures/*.png |
| 15_sensitivity.py | Six sensitivity dimensions | results/sensitivity.json |
| 16_transport_flows.py | Inter-voivodeship flows from payer data | data/nhf_transport_od.csv |
| 17_transport_correlation.py | Flow-distance correlations | results/correlations.json |
| 18_transport_distance_profile.py | Distance profile of transports | results/distance_profile.json |
| 19_minimax_audit.py | Minimax across audited airfield sets | results/minimax_audit.json |
| 20_free_airfield_choice.py | Free base choice (no audit constraint) | results/free_airfield_choice.json |
| 21_source_sets.py | Robustness across three source sets | (console) |
| 22_coverage_worstcase_vs_pairs.py | Worst-case vs pair coverage | (console) |
| 23_frechet_invariance.py | Frechet class bounds, invariance test | results/frechet_invariance.json |
| 24_invariance_boundary.py | Where invariance breaks | results/invariance_boundary.json |
| 25_night_by_aircraft_class.py | Night variant, seven H24 airports | results/night_by_aircraft_class.json |
| 26_margin_perturbation.py | Margin perturbation, 200 draws | results/margin_perturbation.json |
| 27_lower_bound.py | Geography-only lower bound | results/lower_bound.json |
| 28_optimal_set.py | Structure of the optimal set (14 triples) | results/optimal_set.json |
| 29_graphical_abstract.py | Graphical abstract in journal ratio | figures/graphical_abstract.png |

## Key results

| Result | Value | Script |
|---|---|---|
| Worst-case time | **143.5 min** | 04, 28 |
| Optimal bases | **EPBK, EPBY, EPML** | 28 |
| Optimal triples | **14** | 28 |
| Frechet invariance | **True** | 23 |
| Frechet interval | **[45.0, 89.1] min** | 23 |
| Boundary test | **0.06 min** difference | 24 |
| Lower bound | **125.2 min** (12.7% gap) | 27 |
| Margin perturbation | invariance held **200/200** | 26 |

## Data sources

- **Poltransplant:** organ procurement statistics 2020-2024
- **National Health Fund (NFZ):** inter-hospital transport records, released
  17 July 2026 under reference NFZ-DAMJiOS.0143.264.2026 (letter in `data/`)
- **eAIP Poland:** airfield infrastructure (AIRAC snapshot 07-26)
- **Statistics Poland (GUS):** population by voivodeship

## Licences

- **Code:** Apache License 2.0 (`LICENSE`)
- **Data and figures:** CC BY 4.0, details in `LICENSE-DATA.md`
- **NFZ data:** public information, reference NFZ-DAMJiOS.0143.264.2026

## Citation

See `CITATION.cff`. If you use this package or the method, please cite the
manuscript and give ORCID 0009-0008-7419-0851.
