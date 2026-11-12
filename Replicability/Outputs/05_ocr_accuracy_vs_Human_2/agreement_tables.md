OCR agreement against Human 2. Accuracy uses populated reference values; missing OCR entries count as errors. Kappa uses both-populated categorical pairs. Different matched subsets prevent a strictly paired model ranking.


Aggregate results


| OCR | Cards | Visits | Reference cells | Correct | Different | Missing OCR | Accuracy | Disagreement |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 4o-mini | 289 | 846 | 17220 | 8923 | 6907 | 1390 | 51.82% | 48.18% |
| 4.1-mini | 333 | 2399 | 39299 | 31012 | 7865 | 422 | 78.91% | 21.09% |
| 5.6-terra | 347 | 2526 | 41221 | 36538 | 4179 | 504 | 88.64% | 11.36% |
| Nemotron | 315 | 2265 | 37018 | 16602 | 18954 | 1462 | 44.85% | 55.15% |
| Qwen | 343 | 2462 | 40253 | 31677 | 8278 | 298 | 78.69% | 21.31% |

Categorical results: accuracy / kappa


| Indicator | 4o-mini | 4.1-mini | 5.6-terra | Nemotron | Qwen |
| --- | --- | --- | --- | --- | --- |
| Wasting/malnutrition | 51.66% / -0.012 | 84.13% / 0.096 | 99.52% / 0.933 | 10.88% / -0.001 | 98.32% / 0.440 |
| Breastfeeding | 37.10% / 0.000 | 48.50% / 0.154 | 89.66% / 0.851 | 2.32% / 0.005 | 50.23% / 0.146 |
| Mother status | 58.44% / -0.002 | 96.99% / 0.391 | 98.00% / 0.537 | 3.56% / -0.002 | 98.07% / 0.173 |
| Clinical monitoring | 88.99% / 0.104 | 97.11% / 0.590 | 99.32% / 0.960 | 10.01% / -0.002 | 99.21% / 0.817 |
| HIV testing | 25.94% / 0.016 | 33.52% / 0.245 | 96.85% / 0.951 | 0.66% / -0.001 | 39.37% / 0.228 |
| HIV infection | 39.35% / 0.182 | 86.09% / 0.730 | 92.02% / 0.846 | 3.06% / 0.007 | 94.16% / 0.876 |
| Follow-up | 78.71% / 0.034 | 92.62% / 0.662 | 97.77% / 0.916 | 0.31% / 0.000 | 94.83% / 0.692 |

Dates: absolute errors in days; tolerance percentages use valid pairs


| Field | OCR | Exact accuracy | Valid pairs | Mean error | Median error | ±1 day | ±7 days | ±14 days |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Birth date | 4o-mini | 59.60% | 232 | 6466.099 | 0.000 | 64.66% | 69.40% | 72.41% |
| Birth date | 4.1-mini | 79.04% | 281 | 7835.715 | 0.000 | 82.21% | 84.70% | 86.83% |
| Birth date | 5.6-terra | 80.86% | 295 | 4970.339 | 0.000 | 83.39% | 88.14% | 90.17% |
| Birth date | Nemotron | 78.75% | 258 | 5770.143 | 0.000 | 83.33% | 85.66% | 86.82% |
| Birth date | Qwen | 81.42% | 286 | 5140.063 | 0.000 | 84.97% | 88.11% | 89.16% |
| Visit date | 4o-mini | 61.82% | 813 | 97.076 | 0.000 | 64.82% | 66.91% | 68.14% |
| Visit date | 4.1-mini | 73.24% | 2302 | 209.233 | 0.000 | 76.98% | 82.23% | 84.06% |
| Visit date | 5.6-terra | 75.81% | 2436 | 180.323 | 0.000 | 80.01% | 86.12% | 88.01% |
| Visit date | Nemotron | 65.34% | 2109 | 246.849 | 0.000 | 70.70% | 74.82% | 76.62% |
| Visit date | Qwen | 73.27% | 2362 | 189.309 | 0.000 | 77.52% | 82.73% | 84.76% |
| Next appointment | 4o-mini | 26.10% | 691 | 574.142 | 59.000 | 30.10% | 33.86% | 37.34% |
| Next appointment | 4.1-mini | 66.80% | 2098 | 376.345 | 0.000 | 72.55% | 78.31% | 79.84% |
| Next appointment | 5.6-terra | 70.31% | 2184 | 310.647 | 0.000 | 76.88% | 83.29% | 85.03% |
| Next appointment | Nemotron | 59.73% | 1902 | 465.460 | 0.000 | 67.03% | 71.29% | 73.34% |
| Next appointment | Qwen | 63.67% | 2154 | 332.183 | 0.000 | 68.57% | 72.79% | 75.12% |

Numerical results: errors in the indicated units; tolerances use valid pairs


| Field | OCR | Exact accuracy | Valid pairs | Mean error | Median error | Tolerance | Within tolerance |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Weight (kg) | 4o-mini | 47.70% | 625 | 1.739 | 0.000 | ±0.1 | 60.80% |
| Weight (kg) | 4.1-mini | 81.34% | 1942 | 3.844 | 0.000 | ±0.1 | 89.55% |
| Weight (kg) | 5.6-terra | 88.08% | 2147 | 5.906 | 0.000 | ±0.1 | 92.18% |
| Weight (kg) | Nemotron | 77.20% | 1797 | 11.599 | 0.000 | ±0.1 | 87.09% |
| Weight (kg) | Qwen | 80.68% | 1958 | 4.983 | 0.000 | ±0.1 | 90.45% |
| Height (cm) | 4o-mini | 52.67% | 372 | 6.634 | 0.000 | ±1 | 66.13% |
| Height (cm) | 4.1-mini | 86.22% | 1108 | 9.203 | 0.000 | ±1 | 90.97% |
| Height (cm) | 5.6-terra | 87.29% | 1137 | 8.979 | 0.000 | ±1 | 91.47% |
| Height (cm) | Nemotron | 84.42% | 996 | 13.693 | 0.000 | ±1 | 91.47% |
| Height (cm) | Qwen | 88.67% | 1114 | 9.203 | 0.000 | ±1 | 93.27% |
| Birth weight (kg) | 4o-mini | 71.11% | 189 | 92.249 | 0.000 | ±0.1 | 86.24% |
| Birth weight (kg) | 4.1-mini | 82.82% | 235 | 72.285 | 0.000 | ±0.1 | 94.04% |
| Birth weight (kg) | 5.6-terra | 82.25% | 238 | 54.607 | 0.000 | ±0.1 | 95.38% |
| Birth weight (kg) | Nemotron | 77.42% | 215 | 99.328 | 0.000 | ±0.1 | 91.16% |
| Birth weight (kg) | Qwen | 79.40% | 226 | 86.228 | 0.000 | ±0.1 | 94.69% |
| Age (months) | 4o-mini | 58.63% | 842 | 2.052 | 0.000 | ±1 | 70.78% |
| Age (months) | 4.1-mini | 98.96% | 2399 | 0.015 | 0.000 | ±1 | 99.79% |
| Age (months) | 5.6-terra | 99.68% | 2525 | 0.005 | 0.000 | ±1 | 99.84% |
| Age (months) | Nemotron | 97.66% | 2264 | 0.053 | 0.000 | ±1 | 99.03% |
| Age (months) | Qwen | 99.39% | 2462 | 0.009 | 0.000 | ±1 | 99.80% |
| CPT (recorded units) | 4o-mini | 29.04% | 336 | 38.012 | 0.000 | — | — |
| CPT (recorded units) | 4.1-mini | 79.90% | 1892 | 12.613 | 0.000 | — | — |
| CPT (recorded units) | 5.6-terra | 86.20% | 2062 | 10.992 | 0.000 | — | — |
| CPT (recorded units) | Nemotron | 51.45% | 1205 | 33.776 | 0.000 | — | — |
| CPT (recorded units) | Qwen | 84.70% | 2017 | 10.888 | 0.000 | — | — |

District accuracy


| District | 4o-mini | 4.1-mini | 5.6-terra | Nemotron | Qwen |
| --- | --- | --- | --- | --- | --- |
| D1 | 52.45% | 78.41% | 88.72% | 44.36% | 77.63% |
| D2 | 51.49% | 78.64% | 88.46% | 44.02% | 78.28% |
| D3 | 50.91% | 78.88% | 88.23% | 45.86% | 79.60% |
| D4 | 52.97% | 79.98% | 89.31% | 44.94% | 79.25% |

Facility accuracy


| Facility | 4o-mini | 4.1-mini | 5.6-terra | Nemotron | Qwen |
| --- | --- | --- | --- | --- | --- |
| F1 | 53.16% | 79.19% | 89.12% | 45.51% | 79.15% |
| F2 | 53.43% | 80.03% | 90.21% | 43.67% | 78.13% |
| F3 | 50.21% | 73.88% | 87.14% | 44.13% | 75.16% |
| F6 | 50.23% | 76.78% | 87.13% | 44.16% | 78.62% |
| F7 | 53.96% | 80.35% | 87.62% | 41.54% | 76.07% |
| F8 | 49.40% | 77.36% | 87.44% | 45.60% | 79.78% |
| F9 | 50.42% | 77.86% | 88.00% | 45.63% | 79.10% |
| F10 | 53.86% | 80.51% | 87.84% | 43.85% | 78.88% |
| F11 | 51.86% | 80.11% | 88.08% | 46.07% | 78.87% |
| F12 | 53.18% | 79.43% | 89.83% | 41.61% | 76.52% |
| F13 | 47.45% | 77.51% | 88.40% | 45.91% | 79.48% |
| F14 | 52.85% | 81.79% | 89.42% | 46.44% | 79.95% |
| F15 | 50.91% | 80.87% | 90.32% | 45.69% | 80.48% |
| F16 | 54.43% | 78.57% | 89.45% | 45.03% | 78.07% |

Unmatched cards and visits do not enter cell accuracy. Age and visit date help pair visits; see age_date_sensitivity.csv for independent pairing checks. Extreme and invalid values are retained in exact agreement; error magnitudes exclude invalid pairs. All detailed district/facility indicator results are supplied in the CSV reports.
