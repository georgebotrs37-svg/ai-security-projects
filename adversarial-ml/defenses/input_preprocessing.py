"""Input preprocessing: bit-depth reduction (feature squeezing).
NOTE: only evaluated against NON-adaptive attacks. An attacker who knows about the
squeezer can bypass it (see README limitations)."""
import numpy as np


def squeeze(X, bits=2):
    levels = 2 ** bits - 1
    return np.round(np.clip(X, 0, 1) * levels) / levels
