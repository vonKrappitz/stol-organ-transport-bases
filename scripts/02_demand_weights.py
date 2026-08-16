# Copyright 2026 Maciej M. Kasperek. Licensed under the Apache License, Version 2.0.
# Donor counts from the Poltransplant report on procurement and transplantation, Table 5
# pop = residents at the end of 2023. For 2020-2022 the source gives donors per million,
# so the count is reconstructed as pmp*pop/1e6. For 2023 and 2024 the count is given directly.
W = {
"dolnośląskie":   (2879271, 10.0, 10.7, 7.95, 38, 53),
"kuj-pomorskie":  (1996003,  9.0,  9.2,12.43, 27, 35),
"lubelskie":      (2011047,  5.0, 5.75, 7.88, 23, 22),
"lubuskie":       ( 975023, 12.0,17.94,14.25,  9, 21),
"łódzkie":        (2362519,  4.0, 5.36, 7.55, 15, 22),
"małopolskie":    (3429632,  7.0,10.56,11.08, 46, 54),
"mazowieckie":    (5510527,  9.0, 8.67,10.16, 85,101),
"opolskie":       ( 936725, 10.0,11.30,11.64, 11, 13),
"podkarpackie":   (2071676,  4.0, 2.84, 4.80, 13, 16),
"podlaskie":      (1138216,  7.0, 4.28,15.71, 16, 27),
"pomorskie":      (2359573, 20.0,23.87,21.62, 67, 55),
"śląskie":        (4320130, 13.0,13.64,15.83, 73, 83),
"świętokrzyskie": (1168499,  4.0, 5.75, 5.92, 23, 30),
"warm-mazurskie": (1357910, 19.0,14.89,10.95, 23, 27),
"wielkopolskie":  (3487973, 15.0,11.17,15.16, 57, 67),
"zachpomorskie":  (1631784, 13.0, 8.32,12.77, 40, 41),
}
print(f"{'voivodeship':16} {'2020':>5} {'2021':>5} {'2022':>5} {'2023':>5} {'2024':>5} {'mean':>6}")
tot={}
mean_sum=0; c24_sum=0
for w,(pop,p20,p21,p22,c23,c24) in W.items():
    c20=p20*pop/1e6; c21=p21*pop/1e6; c22=p22*pop/1e6
    m=(c20+c21+c22+c23+c24)/5
    tot[w]=m; mean_sum+=m; c24_sum+=c24
    print(f"{w:16} {c20:5.1f} {c21:5.1f} {c22:5.1f} {c23:5d} {c24:5d} {m:8.1f}")
print("-"*54)
print(f"{'sum':16} {'':5} {'':5} {'':5} {'':5} {c24_sum:5d} {mean_sum:8.1f}")
print("\nShare of demand (source weight, mean 2020-2024):")
for w,m in sorted(tot.items(),key=lambda x:-x[1]):
    print(f"  {w:16} {m:6.1f}  ({100*m/mean_sum:4.1f}%)")
