"""Evasion attacks (FGSM, PGD) using the Adversarial Robustness Toolbox (ART)."""
import numpy as np
from art.estimators.classification import SklearnClassifier
from art.attacks.evasion import FastGradientMethod, ProjectedGradientDescent


def wrap(model):
    return SklearnClassifier(model=model, clip_values=(0.0, 1.0))


def fgsm(model, X, eps):
    return FastGradientMethod(wrap(model), eps=eps).generate(x=X)


def pgd(model, X, eps, steps=20):
    atk = ProjectedGradientDescent(wrap(model), eps=eps, eps_step=eps / 4,
                                   max_iter=steps, verbose=False)
    return atk.generate(x=X)


def accuracy_under_attack(model, X, y, eps, attack="pgd"):
    if eps == 0:
        return float((model.predict(X) == y).mean())
    Xa = pgd(model, X, eps) if attack == "pgd" else fgsm(model, X, eps)
    return float((model.predict(Xa) == y).mean())
