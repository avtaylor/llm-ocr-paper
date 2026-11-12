OCR agreement against Human 1. Accuracy uses populated reference values; missing OCR entries count as errors. Kappa uses both-populated categorical pairs. Different matched subsets prevent a strictly paired model ranking.


Aggregate results


| OCR | Cards | Visits | Reference cells | Correct | Different | Missing OCR | Accuracy | Disagreement |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 4o-mini | 290 | 870 | 17879 | 9277 | 6995 | 1607 | 51.89% | 48.11% |
| 4.1-mini | 340 | 2501 | 41818 | 32532 | 8464 | 822 | 77.79% | 22.21% |
| 5.6-terra | 352 | 2620 | 43617 | 38103 | 4305 | 1209 | 87.36% | 12.64% |
| Nemotron | 318 | 2359 | 39062 | 16799 | 20374 | 1889 | 43.01% | 56.99% |
| Qwen | 345 | 2527 | 42092 | 32800 | 8674 | 618 | 77.92% | 22.08% |

Categorical results: accuracy / kappa


| Indicator | 4o-mini | 4.1-mini | 5.6-terra | Nemotron | Qwen |
| --- | --- | --- | --- | --- | --- |
| Wasting/malnutrition | 54.22% / -0.001 | 82.95% / 0.070 | 96.82% / 0.862 | 10.35% / -0.001 | 98.22% / 0.357 |
| Breastfeeding | 38.56% / 0.007 | 48.11% / 0.142 | 88.59% / 0.843 | 2.01% / 0.004 | 50.32% / 0.148 |
| Mother status | 59.48% / -0.004 | 97.22% / 0.107 | 97.61% / 0.276 | 3.40% / 0.000 | 99.55% / 0.351 |
| Clinical monitoring | 90.00% / 0.115 | 96.96% / 0.529 | 95.44% / 0.907 | 10.01% / -0.002 | 99.24% / 0.805 |
| HIV testing | 25.44% / 0.009 | 32.27% / 0.233 | 95.16% / 0.945 | 0.57% / 0.000 | 38.24% / 0.220 |
| HIV infection | 38.26% / 0.173 | 84.17% / 0.692 | 89.30% / 0.807 | 2.67% / 0.004 | 92.01% / 0.831 |
| Follow-up | 79.21% / 0.020 | 92.72% / 0.661 | 94.29% / 0.920 | 0.30% / 0.000 | 94.51% / 0.683 |

Dates: absolute errors in days; tolerance percentages use valid pairs


| Field | OCR | Exact accuracy | Valid pairs | Mean error | Median error | ±1 day | ±7 days | ±14 days |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Birth date | 4o-mini | 61.67% | 265 | 145.743 | 0.000 | 67.92% | 72.83% | 75.85% |
| Birth date | 4.1-mini | 83.38% | 325 | 22.612 | 0.000 | 87.38% | 89.85% | 90.77% |
| Birth date | 5.6-terra | 86.53% | 339 | 8.227 | 0.000 | 89.97% | 93.51% | 93.81% |
| Birth date | Nemotron | 82.54% | 297 | 67.189 | 0.000 | 87.88% | 89.90% | 90.57% |
| Birth date | Qwen | 83.92% | 330 | 21.845 | 0.000 | 88.18% | 90.91% | 91.82% |
| Visit date | 4o-mini | 64.83% | 848 | 70.160 | 0.000 | 66.98% | 69.10% | 70.17% |
| Visit date | 4.1-mini | 76.25% | 2421 | 41.939 | 0.000 | 79.51% | 84.47% | 86.29% |
| Visit date | 5.6-terra | 79.58% | 2540 | 13.117 | 0.000 | 83.50% | 89.72% | 91.61% |
| Visit date | Nemotron | 66.47% | 2172 | 71.105 | 0.000 | 72.84% | 76.75% | 78.64% |
| Visit date | Qwen | 76.30% | 2435 | 22.344 | 0.000 | 80.33% | 85.38% | 87.35% |
| Next appointment | 4o-mini | 26.29% | 747 | 120.325 | 43.000 | 30.79% | 35.34% | 38.96% |
| Next appointment | 4.1-mini | 67.64% | 2232 | 76.297 | 0.000 | 75.76% | 81.23% | 82.75% |
| Next appointment | 5.6-terra | 71.54% | 2315 | 18.921 | 0.000 | 80.60% | 87.04% | 88.68% |
| Next appointment | Nemotron | 58.21% | 1998 | 209.851 | 0.000 | 67.97% | 72.62% | 74.47% |
| Next appointment | Qwen | 64.50% | 2270 | 38.659 | 0.000 | 71.15% | 75.33% | 77.58% |

Numerical results: errors in the indicated units; tolerances use valid pairs


| Field | OCR | Exact accuracy | Valid pairs | Mean error | Median error | Tolerance | Within tolerance |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Weight (kg) | 4o-mini | 50.19% | 643 | 0.706 | 0.000 | ±0.1 | 64.23% |
| Weight (kg) | 4.1-mini | 81.33% | 2036 | 0.609 | 0.000 | ±0.1 | 91.21% |
| Weight (kg) | 5.6-terra | 88.81% | 2231 | 3.844 | 0.000 | ±0.1 | 94.35% |
| Weight (kg) | Nemotron | 76.93% | 1842 | 7.966 | 0.000 | ±0.1 | 87.95% |
| Weight (kg) | Qwen | 82.36% | 2019 | 0.176 | 0.000 | ±0.1 | 92.92% |
| Height (cm) | 4o-mini | 52.49% | 377 | 6.024 | 0.000 | ±1 | 67.11% |
| Height (cm) | 4.1-mini | 84.84% | 1141 | 1.482 | 0.000 | ±1 | 91.76% |
| Height (cm) | 5.6-terra | 86.39% | 1172 | 0.749 | 0.000 | ±1 | 92.83% |
| Height (cm) | Nemotron | 81.78% | 1003 | 5.710 | 0.000 | ±1 | 91.13% |
| Height (cm) | Qwen | 88.68% | 1138 | 1.269 | 0.000 | ±1 | 94.55% |
| Birth weight (kg) | 4o-mini | 65.35% | 210 | 92.605 | 0.000 | ±0.1 | 81.43% |
| Birth weight (kg) | 4.1-mini | 76.51% | 265 | 115.046 | 0.000 | ±0.1 | 88.68% |
| Birth weight (kg) | 5.6-terra | 78.06% | 266 | 74.757 | 0.000 | ±0.1 | 91.73% |
| Birth weight (kg) | Nemotron | 72.30% | 238 | 135.131 | 0.000 | ±0.1 | 86.97% |
| Birth weight (kg) | Qwen | 73.36% | 258 | 117.439 | 0.000 | ±0.1 | 87.98% |
| Age (months) | 4o-mini | 56.09% | 866 | 2.107 | 0.000 | ±1 | 68.94% |
| Age (months) | 4.1-mini | 98.20% | 2499 | 0.030 | 0.000 | ±1 | 99.52% |
| Age (months) | 5.6-terra | 99.12% | 2618 | 0.018 | 0.000 | ±1 | 99.69% |
| Age (months) | Nemotron | 96.86% | 2355 | 0.072 | 0.000 | ±1 | 98.94% |
| Age (months) | Qwen | 98.54% | 2527 | 0.030 | 0.000 | ±1 | 99.56% |
| CPT (recorded units) | 4o-mini | 28.34% | 359 | 40.827 | 0.000 | — | — |
| CPT (recorded units) | 4.1-mini | 74.85% | 1992 | 11.147 | 0.000 | — | — |
| CPT (recorded units) | 5.6-terra | 81.67% | 2153 | 8.005 | 0.000 | — | — |
| CPT (recorded units) | Nemotron | 48.80% | 1264 | 33.601 | 0.000 | — | — |
| CPT (recorded units) | Qwen | 80.36% | 2100 | 10.067 | 0.000 | — | — |

District accuracy


| District | 4o-mini | 4.1-mini | 5.6-terra | Nemotron | Qwen |
| --- | --- | --- | --- | --- | --- |
| D1 | 52.31% | 77.00% | 86.15% | 42.08% | 76.28% |
| D2 | 50.91% | 77.20% | 87.38% | 42.10% | 77.51% |
| D3 | 51.57% | 78.39% | 87.74% | 44.79% | 79.20% |
| D4 | 52.98% | 78.60% | 88.19% | 42.61% | 78.61% |

Facility accuracy


| Facility | 4o-mini | 4.1-mini | 5.6-terra | Nemotron | Qwen |
| --- | --- | --- | --- | --- | --- |
| F1 | 53.89% | 78.54% | 86.96% | 43.70% | 78.75% |
| F2 | 53.04% | 79.24% | 88.55% | 42.78% | 77.19% |
| F3 | 48.88% | 73.09% | 86.07% | 43.47% | 74.06% |
| F6 | 49.70% | 75.03% | 85.37% | 41.54% | 77.03% |
| F7 | 54.05% | 80.76% | 88.81% | 41.97% | 78.10% |
| F8 | 50.48% | 77.94% | 87.61% | 44.90% | 80.16% |
| F9 | 51.47% | 77.23% | 87.34% | 44.37% | 78.19% |
| F10 | 53.12% | 80.57% | 88.23% | 42.78% | 78.95% |
| F11 | 51.83% | 77.63% | 82.90% | 42.02% | 76.43% |
| F12 | 52.03% | 77.46% | 87.60% | 39.45% | 74.88% |
| F13 | 45.91% | 74.69% | 87.05% | 42.20% | 77.73% |
| F14 | 52.78% | 80.32% | 88.36% | 45.12% | 79.25% |
| F15 | 50.80% | 78.79% | 88.92% | 43.34% | 79.38% |
| F16 | 54.82% | 77.04% | 87.41% | 41.64% | 77.59% |

Unmatched cards and visits do not enter cell accuracy. Age and visit date help pair visits; see age_date_sensitivity.csv for independent pairing checks. Extreme and invalid values are retained in exact agreement; error magnitudes exclude invalid pairs. All detailed district/facility indicator results are supplied in the CSV reports.
