# Aircraft base location for time-critical organ transport in Poland

Code and data that reproduce every number and every figure of the study
*Facility Location under a Partially Identified Demand Coupling: Aircraft Bases
for Time-Critical Organ Transport in Poland.*

The study places three short take-off and landing aircraft bases by exhaustive
enumeration of all 5 456 airfield triples drawn from a two-level infrastructure
audit. It shows that the location minimizing the mean mission time is the same
for every demand coupling consistent with the margins, a Fréchet class, and
reports the interval to which the mean mission time is identified.

Everything here runs from the raw inputs. No figure is assembled by hand.

**Author:** Maciej M. Kasperek, ORCID
[0009-0008-7419-0851](https://orcid.org/0009-0008-7419-0851),
maciej_kasperek@protonmail.ch

---

## Quick start

```bash
pip install -r requirements.txt      # Python 3.10 or later
bash run_all.sh
```

The run takes about two minutes and needs no network. Figures land in
`figures/`, numerical results in `results/`.

`run_all.sh` skips a script only when a library it imports unconditionally is
missing, and says so. Scripts 03 and 14 need `shapely`. Script 03 is also
skipped when its output is already in `data/`. The run ends with a check that
every announced result file exists, and returns a non-zero code when a script
fails or a file is missing.

---

## What is here

```
data/       inputs: airfield and runway registers, the infrastructure audit,
            voivodeship boundaries, donor-hospital cities, the payer dataset
scripts/    29 numbered scripts, run in order by run_all.sh
figures/    10 figures at 350 dpi and the donor-hospital list
results/    20 JSON files, one CSV and one text file with the computed numbers
```

### The scripts

| Script | What it does |
|---|---|
| 01 | pre-audit filter of airfields at 750 m and 700 m, which feeds script 04 |
| 02 | builds donor weights per voivodeship |
| 03 | geocodes the nine centres and writes the boundary file |
| 04 | minimax placement on the pre-audit set of 51 airfields, an earlier run kept for the record |
| 05 | compares the four location methods, with a variant without the landing site at Piła |
| 06 to 08 | main maps, reach circles, donor hospitals |
| 09 | aircraft classes and flight regimes, and the worst heart mission with overheads |
| 10 | distribution of the time loss of the STOL |
| 11 | direct operating cost per mission |
| 12 and 13 | feeder configurations, with the worst heart mission in each, and their plot |
| 14 | merged helicopter coverage map |
| 15 | sensitivity analysis |
| 16 to 18 | inter-hospital transport flows, correlation, distance profile |
| 19 | minimax across the audited airfield sets, the source of the figures in the paper, with the main set also run without Piła |
| 20 | free choice of the transfer airfield |
| 21 | source sets of 16, 18 and 34 points, with the hospital set also run without Piła |
| 22 | worst-case coverage against pair coverage |
| 23 | invariance over the Fréchet class, identified interval |
| 24 | boundary of the invariance proposition |
| 25 | night network by aircraft class |
| 26 | perturbation of the margins |
| 27 | lower bound on the worst case |
| 28 | structure of the optimal set within a tolerance of 0.05 min, with the forced position |
| 29 | graphical abstract |

Script 04 runs on the set of 51 airfields that preceded the infrastructure
audit, so its output differs from the paper. The paper's minimax figures, 150,
143.5 and 134 min for two, three and four bases on the audited set of 33
airfields, come from script 19.

Script 03 downloads voivodeship boundaries and geocodes through Nominatim. Its
output is already in `data/`, so `run_all.sh` skips it and the whole run works
offline.

Script 23 also writes the identified interval for the minimax triple, computed
by a linear program on the full time matrix. It is stored under the key
`minimax_triple` in `results/frechet_invariance.json`.

---

## Which figure comes from which script

| Figure | Script |
|---|---|
| map_distance_profile.png | 18 |
| map_minimax_placement.png | 06 |
| map_four_methods.png | 06 |
| map_donor_hospitals.png | 08 |
| map_helicopter_reach.png | 07 |
| map_merged_coverage.png | 14 |
| map_zero_positioning_zones.png | 07 |
| map_mission_loss.png | 10 |
| map_feeder_configurations.png | 13 |
| graphical_abstract.png | 29 |

---

## Data

**Airfields and runways.** `airports.csv` and `runways.csv` come from
[OurAirports](https://ourairports.com/data/), which places its data in the
public domain.

**Infrastructure audit.** The four `airfield_audit_*.csv` files are our own
work, built from AIP Poland, the register of the Polish Civil Aviation
Authority, and operator data. The runway thresholds follow the performance of
the Cessna 208B Grand Caravan EX.

The files are the airfield cards of the audit in table form. `thresholds`
holds the 67 airfields outside the certified group, `certified` 13 certified
airports, `military` the 15 military airfields *(14 meeting the threshold)*. Bydgoszcz, Mielec and
Olsztyn-Mazury were audited one by one. Their cards are in `individual`, which
has English column names, and the scripts enter these three by their codes.
Column names in the other three files are in Polish.

| File | Column | Meaning |
|---|---|---|
| thresholds | `nazwa` | airfield name |
| thresholds | `tw_max` | longest hard runway, metres, 0 when none |
| thresholds | `tr_max` | longest grass runway, metres, 0 when none |
| thresholds | `swiatla_OA` | runway lighting according to OurAirports, 1 or 0 |
| thresholds | `noc_eAIP` | night operations according to the aeronautical publication, 1 or 0 |
| thresholds | `jeta1` | Jet A-1 fuel on site, 1 or 0 |
| thresholds, military | `prog_baza` | meets the base threshold, 758 m hard or 890 m grass |
| thresholds, military | `prog_kons` | meets the conservative threshold, 875 m hard or 1050 m grass |
| certified | `pas_glowny_m` | length of the main runway, metres |
| certified | `szerokosc_m` | runway width, metres |
| certified | `nawierzchnia` | surface |
| certified | `godziny_admin_UTC_zima` | operating hours in UTC, winter, with summer in brackets |
| certified | `H24` | open around the clock, `tak` yes, `nie` no, `warunkowo` conditional |
| certified | `uwagi` | notes |
| certified | `zrodlo_1`, `zrodlo_2` | sources |
| military | `max_dim` | longest runway, metres |
| military | `dims` | runways as pairs of length and width, metres |
| military | `twarda` | hard surface, 1 or 0 |
| military | `godziny` | operating hours in UTC, with summer in brackets |
| military | `noc` | night operations, 1 or 0 |
| military | `ils` | instrument landing system, 1 or 0 |
| military | `paliwo_jet` | jet fuel on site, 1 or 0 |

**Voivodeship boundaries and coordinates.** `wojewodztwa.geojson` holds the
boundaries from the polska-geojson project, under the MIT Licence.
`voivodeship_boundaries.json` holds the 16 voivodeship centroids computed from
them and the coordinates of the nine transplant centres. Both are stored here
so that the run needs no network.

**Inter-hospital transport.** `nhf_interhospital_transport_2020_2024.xlsx` is
the dataset released by the National Health Fund of Poland on 17 July 2026
under case NFZ-DAMJiOS.0143.264.2026, in answer to a request for public
information. It is aggregated to voivodeship pairs, holds no personal data, and
is included unaltered with the release letter beside it.
`data/NHF_transport_data.md` records its provenance.

---

## Keys of the result files

Some keys and column names in the result files are in Polish. The table gives their meaning.

| File | Key | Meaning |
|---|---|---|
| correlations.json | `warianty` | variants of the rank correlation between the proxy and the observed flows |
| correlations.json | `(a) pary z liczba jawna` | pairs with a disclosed count |
| correlations.json | `(b) pary wystepujace, cenz=2` | pairs that occur, censored cells counted as two |
| correlations.json | `(c) wszystkie 240 par, zera` | all 240 pairs, absent pairs as zeros |
| correlations.json | `wobec_odleglosci` | rank correlations with the centroid distance, on the pairs that occur |
| correlations.json | `obserwacja_vs_odleglosc` | observed flows against distance |
| correlations.json | `proxy_vs_odleglosc` | proxy against distance |
| distance_profile.json | `pasma` | distance bands |
| distance_profile.json | `pasmo_km` | limits of the band, km |
| distance_profile.json | `ujawnione` | services in cells with a disclosed count |
| distance_profile.json | `doszacowane` | services imputed at two per censored cell |
| distance_profile.json | `razem` | disclosed plus imputed |
| distance_profile.json | `suma_swiadczen` | all services, disclosed plus imputed |
| distance_profile.json | `udzial_ponizej_200km_proc` | share of services below 200 km, per cent |
| distance_profile.json | `udzial_pasma_100_200_proc` | share of the 100 to 200 km band, per cent |
| distance_profile.json | `ujawnionych_powyzej_300km` | disclosed services above 300 km |
| distance_profile.json | `doszacowanych_powyzej_300km` | imputed services above 300 km |
| feeder_configurations.json | `najgorszy_min` | worst-case time of the configuration, minutes |
| feeder_configurations.json | `typowy_min` | demand-weighted typical time, minutes |
| feeder_configurations.json | `wiaze` | source and centre of the binding mission |
| feeder_configurations.json | `dowoz_zrodla_km` | source feeder distance of the binding mission, kilometres |
| feeder_configurations.json | `serce_najgorszy_min` | worst heart mission for the same bases, minutes |
| feeder_configurations.json | `serce_wiaze` | source and centre of the worst heart mission |
| feeder_configurations.json | `serce_od_zacisku_do_przylotu_min` | cross-clamp to arrival for the worst heart mission, lower and upper estimate, minutes |
| frechet_invariance.json | `bazy_dro` | optimal bases under the worst-case coupling |
| frechet_invariance.json | `bazy_niezaleznosc` | optimal bases under the independent coupling |
| frechet_invariance.json | `bazy_optymistyczne` | optimal bases under the best-case coupling |
| frechet_invariance.json | `niezaleznosc_min` | weighted mean time under the independent coupling, minutes |
| free_airfield_choice.json | `stary` | nearest-runway rule |
| free_airfield_choice.json | `nowy` | free choice among the airfields within helicopter reach |
| invariance_boundary.json | `bazy_max` | optimal bases under the worst-case coupling |
| invariance_boundary.json | `bazy_ind` | optimal bases under the independent coupling |
| invariance_boundary.json | `bazy_min` | optimal bases under the best-case coupling |
| lower_bound.json | `ograniczenie_min` | lower bound on the worst-case time, minutes |
| lower_bound.json | `luka_min` | gap between the optimum for three bases and the bound, minutes |
| margin_perturbation.json | `losowan` | number of draws |
| margin_perturbation.json | `zakres` | range of the multiplier applied to each margin |
| margin_perturbation.json | `niezmienniczosc_utrzymana` | draws in which the three criteria chose the same triple |
| margin_perturbation.json | `ta_sama_trojka` | draws that returned the triple found without perturbation |
| margin_perturbation.json | `trojka_bazowa` | triple found without perturbation |
| night_by_aircraft_class.json | `typowy_min` | demand-weighted typical time, minutes |
| optimal_set.json | `optimum_min` | optimal worst-case time for three bases, minutes |
| optimal_set.json | `tolerancja_min` | tolerance of the comparison of triples, minutes |
| optimal_set.json | `trojek_optymalnych` | number of triples within the tolerance of the optimum |
| optimal_set.json | `trojek_remis_dokladny` | number of triples tied exactly at the optimum |
| optimal_set.json | `rozstep_s` | spread of the optimal triples, seconds |
| optimal_set.json | `nastepna_wartosc_min` | next worst-case time above the optimal set, minutes |
| optimal_set.json | `odstep_nastepnej_s` | distance of that next value from the optimum, seconds |
| optimal_set.json | `w_promieniu_5min` | triples within 5 min of the optimum |
| optimal_set.json | `w_promieniu_10min` | triples within 10 min of the optimum |
| optimal_set.json | `pozycja_wymuszona` | interchangeable airfields, exactly one of them in every optimal triple |
| sensitivity.json | `osrodki` | the nine centre cities taken as sources |
| stol_candidates_final.csv | `nazwa` | town of the airfield |
| stol_candidates_final.csv | `dlugosc_m` | longest hard runway, metres |
| stol_candidates_final.csv | `wojskowe` | military airfield, yes or no |
| stol_candidates_final.csv | `tryb` | `optimum` for a runway of at least 750 m, `awaryjny` for 700 to 750 m |

---

## Validation

The four-layer validator that checks the manuscript, the supplementary
material, the cover letter and the highlights against these result files lives
with the submission package. This repository holds only the code and the data.

---

## Licence

Code is under the **Apache License 2.0**, see `LICENSE`.

Data and figures produced here are under **CC BY 4.0**, see `LICENSE-DATA.md`.
Third-party inputs keep their own terms, which that file records.

---

## Citing

If this code or data is useful to you, cite the paper. `CITATION.cff` carries
the machine-readable metadata and will be updated with the publication DOI
once the article appears.
