"""Adversarial training done properly: the attack runs INSIDE the training loop.

Every minibatch is perturbed with a few PGD steps against the *current* weights, then the
weights are updated on those adversarial examples (Madry et al. min-max training).
For softmax regression the input gradient has a closed form: grad_x loss = W (p - y).
The result is exported to a scikit-learn LogisticRegression so the same ART attacks can be
run against it unchanged."""
import numpy as np
from sklearn.linear_model import LogisticRegression


def _softmax(z):
    z = z - z.max(1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(1, keepdims=True)


def _pgd_batch(W, b, X, Y, eps, steps, rng):
    Xa = np.clip(X + rng.uniform(-eps, eps, X.shape), 0, 1)
    for _ in range(steps):
        grad = (_softmax(Xa @ W + b) - Y) @ W.T          # d loss / d x
        Xa = np.clip(Xa + (eps / 4) * np.sign(grad), X - eps, X + eps)
        Xa = np.clip(Xa, 0, 1)
    return Xa


def adversarial_training(X, y, eps=0.1, epochs=80, lr=0.3, batch=64, steps=5, l2=1e-4, seed=0):
    rng = np.random.default_rng(seed)
    classes = np.unique(y)
    Y = np.eye(len(classes))[np.searchsorted(classes, y)]
    n, d = X.shape
    W, b = np.zeros((d, len(classes))), np.zeros(len(classes))
    for _ in range(epochs):
        order = rng.permutation(n)
        for s in range(0, n, batch):
            idx = order[s:s + batch]
            Xa = _pgd_batch(W, b, X[idx], Y[idx], eps, steps, rng)
            R = _softmax(Xa @ W + b) - Y[idx]
            W -= lr * (Xa.T @ R / len(idx) + l2 * W)
            b -= lr * R.mean(0)
    # export to sklearn so ART can attack it exactly like the baseline
    m = LogisticRegression()
    m.classes_, m.coef_, m.intercept_ = classes, W.T.copy(), b.copy()
    m.n_features_in_ = d
    m.n_iter_ = np.array([epochs])
    return m
