"""Shared helpers: data, seeds, plotting style."""
import numpy as np
from sklearn.datasets import load_digits
from sklearn.model_selection import train_test_split

SEED = 42
TARGET_CLASS = 7  # backdoor target


def load_data():
    """8x8 digits scaled to [0, 1]. Small, fast and needs no download."""
    d = load_digits()
    X, y = d.data / 16.0, d.target
    return train_test_split(X, y, test_size=0.3, random_state=SEED, stratify=y)


def set_dark_style():
    import matplotlib.pyplot as plt
    plt.rcParams.update({
        "figure.facecolor": "#070C1E", "axes.facecolor": "#0B1230",
        "axes.edgecolor": "#2B4A8A", "axes.labelcolor": "#E8EEFF",
        "text.color": "#E8EEFF", "xtick.color": "#A5B4D4", "ytick.color": "#A5B4D4",
        "grid.color": "#1E3A5F", "axes.grid": True, "grid.alpha": 0.5,
        "legend.facecolor": "#0B1230", "legend.edgecolor": "#2B4A8A",
        "font.size": 11, "savefig.facecolor": "#070C1E",
    })

CYAN, PINK, PURPLE, GREEN = "#00E5FF", "#FF2E93", "#8B5CF6", "#4ADE80"
