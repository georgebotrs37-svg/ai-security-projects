"""Poisoning defense: kNN label-consistency filter.
A backdoored sample looks like digit A (plus a tiny patch) but is labelled B, so most of its
nearest neighbours disagree with its label. Flag and drop those samples before training."""
import numpy as np
from sklearn.model_selection import cross_val_predict
from sklearn.neighbors import KNeighborsClassifier


def flag_suspicious(X, y, k=10):
    pred = cross_val_predict(KNeighborsClassifier(n_neighbors=k), X, y, cv=5)
    return pred != y


def detection_metrics(flagged, poisoned_idx, n):
    truth = np.zeros(n, bool)
    truth[poisoned_idx] = True
    tp = (flagged & truth).sum()
    precision = tp / max(flagged.sum(), 1)
    recall = tp / max(truth.sum(), 1)
    return float(precision), float(recall)
