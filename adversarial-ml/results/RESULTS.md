### Evasion (PGD, white-box)

| eps | Baseline | Adversarial training | Squeezing (non-adaptive) |
|---|---|---|---|
| 0 | 96.7% | 92.0% | 95.0% |
| 0.05 | 87.0% | 89.6% | 89.1% |
| 0.1 | 64.1% | 79.6% | 79.4% |
| 0.15 | 33.5% | 62.4% | 52.8% |
| 0.2 | 6.9% | 38.0% | 2.4% |
| 0.3 | 1.9% | 5.7% | 1.9% |

### Backdoor poisoning (target class 7)

| Poisoned | Clean acc | Attack success | Clean acc (filtered) | Attack success (filtered) | Filter precision | Filter recall |
|---|---|---|---|---|---|---|
| 0% | 96.7% | 0.0% | 95.6% | 0.4% | - | - |
| 1% | 96.7% | 79.6% | 95.4% | 0.2% | 30.2% | 100.0% |
| 2% | 96.7% | 88.7% | 95.7% | 18.7% | 39.6% | 84.0% |
| 5% | 95.9% | 97.5% | 95.9% | 73.5% | 51.7% | 47.6% |
| 10% | 96.3% | 99.0% | 95.2% | 91.4% | 41.1% | 18.3% |

### Membership inference

| Model | Test acc | MIA AUC | MIA advantage |
|---|---|---|---|
| Overfit MLP (no defense) | 92.0% | 0.587 | 0.275 |
| MLP + L2 regularisation | 92.8% | 0.574 | 0.210 |
| DP-SGD (sigma=1) | 81.5% | 0.569 | 0.135 |
| DP-SGD (sigma=4) | 41.1% | 0.547 | 0.120 |
