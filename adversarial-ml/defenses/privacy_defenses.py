"""Privacy defenses: L2 regularisation and a small DP-SGD softmax regression (numpy)."""
import numpy as np


class DPLogReg:
    """Softmax regression trained with DP-SGD: per-sample gradient clipping + Gaussian noise.
    We report the noise multiplier (sigma). A formal (epsilon, delta) needs a privacy accountant."""

    def __init__(self, noise_multiplier=1.0, clip=1.0, epochs=40, lr=0.8, batch=64, seed=0):
        self.sigma, self.clip, self.epochs, self.lr, self.batch = noise_multiplier, clip, epochs, lr, batch
        self.rng = np.random.default_rng(seed)

    @staticmethod
    def _softmax(z):
        z = z - z.max(1, keepdims=True)
        e = np.exp(z)
        return e / e.sum(1, keepdims=True)

    def fit(self, X, y):
        self.classes_ = np.unique(y)
        n, d = X.shape
        k = len(self.classes_)
        Y = np.eye(k)[np.searchsorted(self.classes_, y)]
        self.W, self.b = np.zeros((d, k)), np.zeros(k)
        for _ in range(self.epochs):
            order = self.rng.permutation(n)
            for s in range(0, n, self.batch):
                idx = order[s:s + self.batch]
                P = self._softmax(X[idx] @ self.W + self.b)
                R = P - Y[idx]
                G = np.concatenate([(X[idx][:, :, None] * R[:, None, :]).reshape(len(idx), -1), R], axis=1)
                G *= np.minimum(1.0, self.clip / (np.linalg.norm(G, axis=1, keepdims=True) + 1e-12))
                g = G.sum(0) + self.rng.normal(0, self.sigma * self.clip, G.shape[1])
                g /= len(idx)
                self.W -= self.lr * g[:d * k].reshape(d, k)
                self.b -= self.lr * g[d * k:]
        return self

    def predict_proba(self, X):
        return self._softmax(X @ self.W + self.b)

    def predict(self, X):
        return self.classes_[self.predict_proba(X).argmax(1)]
