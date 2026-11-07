"""Runs all experiments: Attack -> Defend -> Measure. Writes charts + results.json to results/."""
import json, warnings
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier

from common import load_data, set_dark_style, CYAN, PINK, PURPLE, GREEN, SEED, TARGET_CLASS
from attacks.evasion import pgd, fgsm, accuracy_under_attack
from attacks.poisoning import poison, attack_success_rate
from attacks.privacy import membership_inference
from defenses.adversarial_training import adversarial_training
from defenses.input_preprocessing import squeeze
from defenses.poisoning_filter import flag_suspicious, detection_metrics
from defenses.privacy_defenses import DPLogReg

warnings.filterwarnings("ignore")
set_dark_style()
Xtr, Xte, ytr, yte = load_data()
R = {}

# ------------------------------------------------------------------ 1. EVASION
print("[1/3] Evasion + defenses")
base = LogisticRegression(max_iter=3000).fit(Xtr, ytr)
robust = adversarial_training(Xtr, ytr, eps=0.15)
EPS = [0, 0.05, 0.1, 0.15, 0.2, 0.3]
ev = {"eps": EPS, "baseline": [], "adv_training": [], "squeezing_non_adaptive": []}
for e in EPS:
    ev["baseline"].append(accuracy_under_attack(base, Xte, yte, e))
    ev["adv_training"].append(accuracy_under_attack(robust, Xte, yte, e))
    if e == 0:
        ev["squeezing_non_adaptive"].append(float((base.predict(squeeze(Xte)) == yte).mean()))
    else:  # attacker crafts examples against the base model, defender squeezes inputs first
        ev["squeezing_non_adaptive"].append(float((base.predict(squeeze(pgd(base, Xte, e))) == yte).mean()))
R["evasion"] = ev

fig, ax = plt.subplots(figsize=(8, 4.8))
ax.plot(EPS, ev["baseline"], "o-", color=PINK, lw=3, label="Baseline (no defense)")
ax.plot(EPS, ev["adv_training"], "o-", color=CYAN, lw=3, label="Adversarial training")
ax.plot(EPS, ev["squeezing_non_adaptive"], "o--", color=PURPLE, lw=2.5, label="Bit-depth squeezing (non-adaptive attack)")
ax.set_xlabel("Perturbation budget $\\epsilon$ (L-inf, PGD)"); ax.set_ylabel("Test accuracy")
ax.set_title("Accuracy vs robustness: evasion attack (PGD)"); ax.set_ylim(0, 1.02); ax.legend()
fig.tight_layout(); fig.savefig("results/evasion_accuracy_vs_eps.png", dpi=160); plt.close(fig)

# adversarial examples gallery
Xs, ys = Xte[:6], yte[:6]
Xa = fgsm(base, Xs, 0.25)
pc, pa = base.predict(Xs), base.predict(Xa)
fig, axs = plt.subplots(3, 6, figsize=(10, 5.4))
for i in range(6):
    for r, (img, title, col) in enumerate([(Xs[i], f"clean: {pc[i]}", CYAN), (Xa[i] - Xs[i], "perturbation", PURPLE), (Xa[i], f"adversarial: {pa[i]}", PINK if pa[i] != ys[i] else CYAN)]):
        axs[r, i].imshow(img.reshape(8, 8), cmap="magma" if r == 1 else "gray"); axs[r, i].set_title(title, color=col, fontsize=10)
        axs[r, i].axis("off")
fig.suptitle("FGSM ($\\epsilon$=0.25): small pixel changes, wrong predictions", y=0.99)
fig.tight_layout(); fig.savefig("results/adversarial_examples.png", dpi=160); plt.close(fig)

# ------------------------------------------------------------------ 2. POISONING
print("[2/3] Backdoor poisoning + defense")
FR = [0.0, 0.01, 0.02, 0.05, 0.10]
po = {"fraction": FR, "clean_acc": [], "asr": [], "filtered_clean_acc": [], "filtered_asr": [], "precision": [], "recall": []}
for f in FR:
    Xp, yp, idx = poison(Xtr, ytr, f, seed=SEED)
    m = LogisticRegression(max_iter=3000).fit(Xp, yp)
    po["clean_acc"].append(float((m.predict(Xte) == yte).mean())); po["asr"].append(attack_success_rate(m, Xte, yte))
    flagged = flag_suspicious(Xp, yp)
    keep = ~flagged
    m2 = LogisticRegression(max_iter=3000).fit(Xp[keep], yp[keep])
    po["filtered_clean_acc"].append(float((m2.predict(Xte) == yte).mean())); po["filtered_asr"].append(attack_success_rate(m2, Xte, yte))
    if f > 0:
        p, r = detection_metrics(flagged, idx, len(Xp)); po["precision"].append(p); po["recall"].append(r)
    else:
        po["precision"].append(None); po["recall"].append(None)
R["poisoning"] = po

fig, axs = plt.subplots(1, 2, figsize=(11, 4.4))
x = np.arange(len(FR)); w = 0.38
axs[0].bar(x - w/2, po["asr"], w, color=PINK, label="No defense"); axs[0].bar(x + w/2, po["filtered_asr"], w, color=CYAN, label="kNN label filter")
axs[0].set_xticks(x); axs[0].set_xticklabels([f"{int(f*100)}%" for f in FR]); axs[0].set_xlabel("Poisoned share of training data")
axs[0].set_ylabel("Attack success rate"); axs[0].set_title("Backdoor success"); axs[0].set_ylim(0, 1.05); axs[0].legend()
axs[1].plot(x, po["clean_acc"], "o-", color=PINK, lw=3, label="No defense"); axs[1].plot(x, po["filtered_clean_acc"], "o-", color=CYAN, lw=3, label="kNN label filter")
axs[1].set_xticks(x); axs[1].set_xticklabels([f"{int(f*100)}%" for f in FR]); axs[1].set_xlabel("Poisoned share of training data")
axs[1].set_ylabel("Clean test accuracy"); axs[1].set_title("Clean accuracy (stealth)"); axs[1].set_ylim(0.9, 1.0); axs[1].legend()
fig.tight_layout(); fig.savefig("results/backdoor_poisoning.png", dpi=160); plt.close(fig)

# ------------------------------------------------------------------ 3. PRIVACY
print("[3/3] Membership inference + defenses")
rng = np.random.default_rng(SEED)
n_mem = 200
mi = rng.choice(len(Xtr), n_mem, replace=False); ni = rng.choice(len(Xte), n_mem, replace=False)
Xm, ym = Xtr[mi], ytr[mi]; Xn, yn = Xte[ni], yte[ni]
cands = {
    "Overfit MLP (no defense)": MLPClassifier((256,), alpha=0.0, max_iter=3000, random_state=SEED),
    "MLP + L2 regularisation": MLPClassifier((256,), alpha=1.0, max_iter=3000, random_state=SEED),
    "DP-SGD ($\\sigma$=1)": DPLogReg(noise_multiplier=1.0, seed=SEED),
    "DP-SGD ($\\sigma$=4)": DPLogReg(noise_multiplier=4.0, seed=SEED),
}
pr = {"model": [], "test_acc": [], "mia_auc": [], "mia_advantage": []}
for name, mdl in cands.items():
    mdl.fit(Xm, ym)
    auc, adv = membership_inference(mdl, Xm, ym, Xn, yn)
    pr["model"].append(name); pr["test_acc"].append(float((mdl.predict(Xte) == yte).mean()))
    pr["mia_auc"].append(auc); pr["mia_advantage"].append(adv)
R["privacy"] = pr

fig, ax = plt.subplots(figsize=(9, 4.8))
x = np.arange(len(pr["model"])); w = 0.38
b1 = ax.bar(x - w/2, pr["mia_auc"], w, color=PINK, label="Membership inference AUC (lower is better)")
b2 = ax.bar(x + w/2, pr["test_acc"], w, color=CYAN, label="Test accuracy (higher is better)")
ax.axhline(0.5, color="#A5B4D4", ls="--", lw=1); ax.text(len(x) - 0.45, 0.51, "random guess", color="#A5B4D4", fontsize=9, ha="right")
ax.set_xticks(x); ax.set_xticklabels([m.replace(" (", "\n(").replace(" + ", "\n+ ") for m in pr["model"]], fontsize=9)
ax.set_ylim(0, 1.12); ax.set_title("Privacy vs utility: membership inference"); ax.legend(loc="upper right", fontsize=9)
for b in list(b1) + list(b2): ax.text(b.get_x() + b.get_width()/2, b.get_height() + 0.01, f"{b.get_height():.2f}", ha="center", fontsize=9)
fig.tight_layout(); fig.savefig("results/membership_inference.png", dpi=160); plt.close(fig)

json.dump(R, open("results/results.json", "w"), indent=2)

# ------------------------------------------------------------------ markdown tables
def pct(v): return "-" if v is None else f"{v*100:.1f}%"
L = ["### Evasion (PGD, white-box)", "", "| eps | Baseline | Adversarial training | Squeezing (non-adaptive) |", "|---|---|---|---|"]
for i, e in enumerate(EPS): L.append(f"| {e} | {pct(ev['baseline'][i])} | {pct(ev['adv_training'][i])} | {pct(ev['squeezing_non_adaptive'][i])} |")
L += ["", f"### Backdoor poisoning (target class {TARGET_CLASS})", "", "| Poisoned | Clean acc | Attack success | Clean acc (filtered) | Attack success (filtered) | Filter precision | Filter recall |", "|---|---|---|---|---|---|---|"]
for i, f in enumerate(FR): L.append(f"| {int(f*100)}% | {pct(po['clean_acc'][i])} | {pct(po['asr'][i])} | {pct(po['filtered_clean_acc'][i])} | {pct(po['filtered_asr'][i])} | {pct(po['precision'][i])} | {pct(po['recall'][i])} |")
L += ["", "### Membership inference", "", "| Model | Test acc | MIA AUC | MIA advantage |", "|---|---|---|---|"]
for i, m in enumerate(pr["model"]): L.append(f"| {m.replace('$','').replace(chr(92)+'sigma','sigma')} | {pct(pr['test_acc'][i])} | {pr['mia_auc'][i]:.3f} | {pr['mia_advantage'][i]:.3f} |")
open("results/RESULTS.md", "w").write("\n".join(L) + "\n")
print("\n".join(L))
