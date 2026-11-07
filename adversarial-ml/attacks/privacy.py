"""Membership inference: loss-threshold attack (Yeom et al.). Members have lower loss."""
import numpy as np
from sklearn.metrics import roc_auc_score


def per_sample_loss(model, X, y, eps=1e-12):
    p = model.predict_proba(X)
    cols = {c: i for i, c in enumerate(model.classes_)}
    idx = np.array([cols[c] for c in y])
    return -np.log(np.clip(p[np.arange(len(y)), idx], eps, 1.0))


def membership_inference(model, X_in, y_in, X_out, y_out):
    """Returns AUC and attacker advantage (max TPR - FPR). 0.5 AUC / 0 advantage = no leakage."""
    loss = np.concatenate([per_sample_loss(model, X_in, y_in), per_sample_loss(model, X_out, y_out)])
    is_member = np.concatenate([np.ones(len(X_in)), np.zeros(len(X_out))])
    score = -loss
    auc = roc_auc_score(is_member, score)
    thr = np.sort(np.unique(score))
    adv = max(((score[is_member == 1] >= t).mean() - (score[is_member == 0] >= t).mean()) for t in thr)
    return float(auc), float(adv)
