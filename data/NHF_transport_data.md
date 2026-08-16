# Inter-hospital transport data of the National Health Fund of Poland

`nhf_interhospital_transport_2020_2024.xlsx` is the dataset as received from the
Fund, unaltered, including the methodology sheet the Fund prepared.

## Provenance

- Source: National Health Fund of Poland, Head Office, Department of Analyses,
  Quality Monitoring and Optimisation of Services
- Released: 17 July 2026
- Case reference: NFZ-DAMJiOS.0143.264.2026, 2026.383310.NAJU
- Basis: request for public information
- Release letter: `nhf_release_letter_2026-07-17.pdf`

The dataset is aggregated to voivodeship pairs and holds no personal data and no
individual medical records. The Fund was notified that it would be placed in a
public research repository under the re-use of public sector information regime,
and raised no objection.

Any use should credit the source, the release date, and the case reference.

## Contents

Counts of inter-hospital transport services for 2020 to 2024, by voivodeship of
departure and voivodeship of arrival, for two service codes:

- 5.09.03.0000170, transfer of a patient to another provider for further
  treatment using medical transport,
- 5.09.05.0000004, provision of air transport to another provider.

680 rows. Cells below five services are censored and recorded as `<5`. Censoring
covers 51 per cent of cells, and the whole band above 300 km is censored
entirely. That censoring is the empirical ground for the paper's claim that the
demand matrix cannot be estimated from these data.

The `Metodyka` sheet carries the payer-side definition of a pair: a patient for
whom one of the two codes was reported was admitted the same day to a
hospitalisation at another centre. The voivodeship of departure and of arrival
are the regional branches of the respective centres.

## Use in the reproduction

`16_transport_flows.py` turns the sheet into `nhf_transport_od.csv`, which is a
derived file and is not versioned. Scripts 17 and 18 compute the rank
correlation and the distance profile from it.

If the file is absent, scripts 16 to 18 skip themselves and print a notice. The
rest of the study reproduces without them.
