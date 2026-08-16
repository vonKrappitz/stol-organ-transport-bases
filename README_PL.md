# Bazy samolotow STOL dla transportu narzadow — pakiet reprodukcyjny

Kod, dane wejsciowe i wyniki odtwarzajace kazda liczbe i kazda figure
z manuskryptu *"Facility Location under a Partially Identified Demand
Coupling: Aircraft Bases for Time-Critical Organ Transport in Poland"*.

**Autor:** Maciej M. Kasperek (ORCID 0009-0008-7419-0851)
**Kontakt:** maciej_kasperek@protonmail.ch

**Wersja angielska:** [README.md](README.md)

## Glowny wynik

Przy trzech bazach najgorszy czas misji wynosi **143,5 min** (model glowny,
33 lotniska po audycie infrastruktury), bazy: **Bialystok-Krywlany (EPBK),
Bydgoszcz (EPBY), Mielec (EPML)**. Optimum jest niezmiennicze wzgledem calej
klasy Frecheta sprzezen popytu — decyzja o lokalizacji zachodzi mimo ze
macierz dawca-biorca nie jest rejestrowana.

## Struktura repozytorium

```
.
├── README.md                # wersja angielska (glowna)
├── README_PL.md             # ten plik
├── LICENSE                  # Apache 2.0 (kod)
├── LICENSE-DATA.md          # licencje danych i figur
├── CITATION.cff             # metadane cytowania
├── requirements.txt         # zaleznosci Python
├── run_all.sh               # odtworzenie wszystkiego jednym poleceniem
├── data/                    # dane wejsciowe
├── scripts/                 # 29 skryptow Python (01-29)
├── results/                 # wyniki liczbowe (JSON/CSV)
└── figures/                 # figury (PNG)
```

## Odtworzenie od zera

```bash
pip install -r requirements.txt      # Python 3.10+
bash run_all.sh                      # uruchamia wszystkie skrypty i sprawdza wyniki
```

Skrypty czytaja z `data/`, zapisuja liczby do `results/`, a figury do
`figures/`. Uzywaja sciezek wzglednych do katalogu glownego repozytorium,
wiec dzialaja z dowolnego katalogu uruchomienia. **Siec nie jest wymagana** —
wszystkie dane wejsciowe sa w `data/` (wyjatek: opcjonalny skrypt 03
geokodowania, patrz nizej).

Po zakonczeniu `run_all.sh` sam sprawdza, czy wszystkie 14 plikow wynikowych
JSON istnieje i nie jest puste. Jesli czegos brakuje, wypisze `MISSING`
i zakonczy sie kodem bledu.

## Co robi kazdy skrypt

| Skrypt | Co liczy | Wynik |
|---|---|---|
| 01_filter_airfields.py | Zbior lotnisk po audycie pasa/infrastruktury | data/stol_candidates_final.csv |
| 02_demand_weights.py | Wagi zrodel z marginesow dawczych | (konsola) |
| 03_geocoding.py | Centroidy wojewodztw (opcjonalny, jest cache) | data/voivodeship_boundaries.json |
| 04_minimax.py | Optimum minimax (p-center), 5456 trojek | (konsola) |
| 05_compare_methods.py | Cztery modele lokalizacji obok siebie | results/compare_methods.json |
| 06_maps_main.py | Mapy: rozmieszczenie minimax, cztery metody | figures/*.png |
| 07_maps_reach_circles.py | Zasieg helikoptera, strefy pozycjonowania | figures/*.png |
| 08_map_donor_hospitals.py | Mapa szpitali dawczych | figures/map_donor_hospitals.png |
| 09_aircraft_classes.py | Cztery klasy samolotow, wariant dzienny | (konsola) |
| 10_mission_loss_distribution.py | Rozklad strat czasu misji | results/mission_loss_distribution.json |
| 11_cost_per_mission.py | Koszt operacyjny na misje | results/cost_per_mission.json |
| 12_feeder_configurations.py | Konfiguracje dowozu HEMS/GEMS | (konsola) |
| 13_plot_feeder.py | Wykres konfiguracji dowozu | figures/map_feeder_configurations.png |
| 14_map_merged_coverage.py | Zbiorcza mapa pokrycia | figures/*.png |
| 15_sensitivity.py | Szesc wymiarow wrazliwosci | results/sensitivity.json |
| 16_transport_flows.py | Przeplywy miedzywojewodzkie z danych platnika | data/nhf_transport_od.csv |
| 17_transport_correlation.py | Korelacje przeplyw-odleglosc | results/correlations.json |
| 18_transport_distance_profile.py | Profil odleglosci transportow | results/distance_profile.json |
| 19_minimax_audit.py | Minimax na zaudytowanych zbiorach lotnisk | results/minimax_audit.json |
| 20_free_airfield_choice.py | Swobodny wybor baz (bez ograniczenia audytu) | results/free_airfield_choice.json |
| 21_source_sets.py | Odpornosc na trzy zbiory zrodel | (konsola) |
| 22_coverage_worstcase_vs_pairs.py | Pokrycie worst-case vs pary | (konsola) |
| 23_frechet_invariance.py | Kresy klasy Frecheta, test niezmienniczosci | results/frechet_invariance.json |
| 24_invariance_boundary.py | Gdzie niezmienniczosc zanika | results/invariance_boundary.json |
| 25_night_by_aircraft_class.py | Wariant nocny, siedem lotnisk H24 | results/night_by_aircraft_class.json |
| 26_margin_perturbation.py | Perturbacja marginesow, 200 losowan | results/margin_perturbation.json |
| 27_lower_bound.py | Dolne ograniczenie czysto geograficzne | results/lower_bound.json |
| 28_optimal_set.py | Struktura zbioru optymalnego (14 trojek) | results/optimal_set.json |
| 29_graphical_abstract.py | Abstrakt graficzny w proporcji pisma | figures/graphical_abstract.png |

## Kluczowe wyniki

| Wynik | Wartosc | Skrypt |
|---|---|---|
| Najgorszy czas | **143,5 min** | 04, 28 |
| Bazy optymalne | **EPBK, EPBY, EPML** | 28 |
| Trojki optymalne | **14** | 28 |
| Niezmienniczosc Frecheta | **True** | 23 |
| Przedzial Frecheta | **[45,0; 89,1] min** | 23 |
| Test granicy | roznica **0,06 min** | 24 |
| Ograniczenie dolne | **125,2 min** (luka 12,7%) | 27 |
| Perturbacja marginesow | niezmienniczosc **200/200** | 26 |

## Zrodla danych

- **Poltransplant:** statystyki pobrania narzadow 2020-2024
- **Narodowy Fundusz Zdrowia (NFZ):** rejestr transportow miedzyszpitalnych,
  udostepniony 17 lipca 2026, znak NFZ-DAMJiOS.0143.264.2026 (pismo w `data/`)
- **eAIP Polska:** infrastruktura lotniskowa (migawka AIRAC 07-26)
- **GUS:** ludnosc wedlug wojewodztw

## Licencje

- **Kod:** Apache License 2.0 (`LICENSE`)
- **Dane i figury:** CC BY 4.0, szczegoly w `LICENSE-DATA.md`
- **Dane NFZ:** informacja publiczna, znak NFZ-DAMJiOS.0143.264.2026

## Cytowanie

Patrz `CITATION.cff`. Jesli korzystasz z tego pakietu lub metody, prosze
o cytowanie manuskryptu i podanie ORCID 0009-0008-7419-0851.
