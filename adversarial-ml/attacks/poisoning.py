"""Backdoor data poisoning: a 2x2 white patch in the corner flips the label to TARGET_CLASS."""
import numpy as np
from common import TARGET_CLASS


def add_trigger(X):
    X = X.copy().reshape(-1, 8, 8)
    X[:, 6:8, 6:8] = 1.0
    return X.reshape(-1, 64)


def poison(X, y, frac, seed=0):
    """Return poisoned copy of (X, y) and the indices that were tampered with."""
    rng = np.random.default_rng(seed)
    n = int(round(frac * len(X)))
    idx = rng.choice(np.where(y != TARGET_CLASS)[0], size=n, replace=False)
    Xp, yp = X.copy(), y.copy()
    Xp[idx] = add_trigger(X[idx])
    yp[idx] = TARGET_CLASS
    return Xp, yp, idx


def attack_success_rate(model, X_test, y_test):
    """Share of triggered non-target test samples classified as the target class."""
    mask = y_test != TARGET_CLASS
    return float((model.predict(add_trigger(X_test[mask])) == TARGET_CLASS).mean())
