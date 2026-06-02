"""
Expressive gait emotion classification — method comparison.

Task: classify the emotion (anger / joy / neutral / sad) expressed in a walking
trial from the College de France expressive gait database (TRC motion capture).

We compare two *feature philosophies* and several *models*, organised so that
three textbook comparisons fall out of five runs:

  Run A  Expert features      + RandomForest        (interpretable / tree)
  Run B  Expert features      + LogisticRegression  (interpretable / linear)
  Run C  Raw markers -> PCA   + KNN                  (classic black-box)
  Run D  Raw markers          + MLP (neural net)     (pure black-box)
  Run E  Raw markers -> AE    + LogisticRegression   (learned features)

  Comparison 1  Expert features vs pure black box :  A  vs  D
  Comparison 2  PCA            vs neural net       :  C  vs  D
  Comparison 3  Hand-crafted   vs autoencoder feats:  B  vs  E
                (same LogisticRegression downstream, only features differ)

Evaluation: Leave-One-Subject-Out cross-validation (4 actors -> 4 folds).
This is the honest test of whether the methods capture *emotion* rather than
*who is walking*: every test actor is unseen during training.
"""

import os
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import KNeighborsClassifier
from sklearn.neural_network import MLPClassifier, MLPRegressor
from sklearn.decomposition import PCA
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix

from data_loader import load_dataset
import expert_features
import blackbox_prep

HERE = os.path.dirname(__file__)
OUT = os.path.join(HERE, "..", "outputs")
os.makedirs(OUT, exist_ok=True)
SEED = 0
CLASSES = ["anger", "joy", "neutral", "sad"]


# ----------------------------------------------------------------------------
# Autoencoder helper: train an MLP to reconstruct X, use bottleneck as features
# ----------------------------------------------------------------------------
def ae_encode(X_train, X_test, bottleneck=16, seed=SEED):
    """Nonlinear autoencoder via MLPRegressor (input -> 64 -> bottleneck -> 64
    -> input). Returns encoded train/test (bottleneck activations)."""
    ae = MLPRegressor(
        hidden_layer_sizes=(64, bottleneck, 64),
        activation="relu",
        solver="adam",
        alpha=1e-3,
        max_iter=600,
        random_state=seed,
    )
    ae.fit(X_train, X_train)

    def encode(X):
        # forward pass up to and including the bottleneck layer (relu)
        a = X
        for i in range(2):  # coefs_[0]: in->64, coefs_[1]: 64->bottleneck
            a = np.maximum(0, a @ ae.coefs_[i] + ae.intercepts_[i])
        return a

    return encode(X_train), encode(X_test)


# ----------------------------------------------------------------------------
# One method = a function (Xtr, ytr, Xte) -> predictions, plus which X it uses
# ----------------------------------------------------------------------------
def m_expert_rf(Xtr, ytr, Xte):
    sc = StandardScaler().fit(Xtr)
    clf = RandomForestClassifier(n_estimators=300, random_state=SEED)
    clf.fit(sc.transform(Xtr), ytr)
    return clf.predict(sc.transform(Xte))


def m_expert_logreg(Xtr, ytr, Xte):
    sc = StandardScaler().fit(Xtr)
    clf = LogisticRegression(max_iter=2000, C=1.0)
    clf.fit(sc.transform(Xtr), ytr)
    return clf.predict(sc.transform(Xte))


def m_pca_knn(Xtr, ytr, Xte):
    sc = StandardScaler().fit(Xtr)
    pca = PCA(n_components=20, random_state=SEED).fit(sc.transform(Xtr))
    knn = KNeighborsClassifier(n_neighbors=5)
    knn.fit(pca.transform(sc.transform(Xtr)), ytr)
    return knn.predict(pca.transform(sc.transform(Xte)))


def m_raw_mlp(Xtr, ytr, Xte):
    sc = StandardScaler().fit(Xtr)
    clf = MLPClassifier(
        hidden_layer_sizes=(128, 32),
        activation="relu",
        alpha=1e-2,            # strong L2: few samples, high dimension
        max_iter=800,
        random_state=SEED,
    )
    clf.fit(sc.transform(Xtr), ytr)
    return clf.predict(sc.transform(Xte))


def m_ae_logreg(Xtr, ytr, Xte):
    sc = StandardScaler().fit(Xtr)
    Ztr, Zte = ae_encode(sc.transform(Xtr), sc.transform(Xte))
    sc2 = StandardScaler().fit(Ztr)
    clf = LogisticRegression(max_iter=2000, C=1.0)
    clf.fit(sc2.transform(Ztr), ytr)
    return clf.predict(sc2.transform(Zte))


METHODS = [
    ("A: Expert + RandomForest", "expert", m_expert_rf),
    ("B: Expert + LogReg",       "expert", m_expert_logreg),
    ("C: PCA + KNN",             "black",  m_pca_knn),
    ("D: Raw + MLP (NN)",        "black",  m_raw_mlp),
    ("E: Autoencoder + LogReg",  "black",  m_ae_logreg),
]


def loso_evaluate(Xe, Xb, y, groups):
    """Leave-One-Subject-Out CV for every method. Returns results dict."""
    subjects = sorted(set(groups))
    results = {}
    for name, src, fn in METHODS:
        X = Xe if src == "expert" else Xb
        y_true_all, y_pred_all, fold_acc = [], [], []
        for s in subjects:
            te = groups == s
            tr = ~te
            yp = fn(X[tr], y[tr], X[te])
            y_pred_all.extend(yp)
            y_true_all.extend(y[te])
            fold_acc.append(accuracy_score(y[te], yp))
        acc = accuracy_score(y_true_all, y_pred_all)
        f1 = f1_score(y_true_all, y_pred_all, average="macro", labels=CLASSES)
        results[name] = {
            "acc": acc,
            "macro_f1": f1,
            "fold_acc": fold_acc,
            "fold_acc_std": float(np.std(fold_acc)),
            "y_true": y_true_all,
            "y_pred": y_pred_all,
        }
    return results


# ----------------------------------------------------------------------------
# Plots
# ----------------------------------------------------------------------------
def plot_confusion(res, name, fname):
    cm = confusion_matrix(res["y_true"], res["y_pred"], labels=CLASSES)
    cmn = cm / cm.sum(1, keepdims=True).clip(min=1)
    fig, ax = plt.subplots(figsize=(4.2, 3.8))
    im = ax.imshow(cmn, cmap="Blues", vmin=0, vmax=1)
    ax.set_xticks(range(4)); ax.set_xticklabels(CLASSES, rotation=45, ha="right")
    ax.set_yticks(range(4)); ax.set_yticklabels(CLASSES)
    ax.set_xlabel("predicted"); ax.set_ylabel("true")
    ax.set_title(f"{name}\nacc={res['acc']:.2f}, macroF1={res['macro_f1']:.2f}")
    for i in range(4):
        for j in range(4):
            ax.text(j, i, f"{cm[i,j]}", ha="center", va="center",
                    color="white" if cmn[i, j] > 0.5 else "black", fontsize=9)
    fig.colorbar(im, fraction=0.046, pad=0.04)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, fname), dpi=130)
    plt.close(fig)


def plot_summary(results):
    names = list(results.keys())
    accs = [results[n]["acc"] for n in names]
    f1s = [results[n]["macro_f1"] for n in names]
    x = np.arange(len(names))
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.bar(x - 0.2, accs, 0.4, label="accuracy")
    ax.bar(x + 0.2, f1s, 0.4, label="macro F1")
    ax.axhline(0.25, ls="--", c="gray", label="chance (4 classes)")
    ax.set_xticks(x); ax.set_xticklabels(names, rotation=20, ha="right", fontsize=8)
    ax.set_ylim(0, 1); ax.set_ylabel("LOSO score"); ax.legend()
    ax.set_title("Method comparison (Leave-One-Subject-Out)")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "summary_scores.png"), dpi=130)
    plt.close(fig)


def plot_feature_importance(Xe, y, names):
    sc = StandardScaler().fit(Xe)
    clf = RandomForestClassifier(n_estimators=400, random_state=SEED)
    clf.fit(sc.transform(Xe), y)
    imp = clf.feature_importances_
    order = np.argsort(imp)[::-1][:15]
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.barh(range(len(order)), imp[order][::-1])
    ax.set_yticks(range(len(order)))
    ax.set_yticklabels([names[i] for i in order][::-1], fontsize=8)
    ax.set_xlabel("RandomForest importance")
    ax.set_title("Top expert features for emotion")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "expert_feature_importance.png"), dpi=130)
    plt.close(fig)


def plot_pca_scatter(Xb, y):
    sc = StandardScaler().fit(Xb)
    Z = PCA(n_components=2, random_state=SEED).fit_transform(sc.transform(Xb))
    fig, ax = plt.subplots(figsize=(5.5, 4.5))
    for c in CLASSES:
        m = y == c
        ax.scatter(Z[m, 0], Z[m, 1], label=c, s=35, alpha=0.8)
    ax.set_xlabel("PC1"); ax.set_ylabel("PC2")
    ax.set_title("Raw marker data — first 2 principal components")
    ax.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "pca_scatter.png"), dpi=130)
    plt.close(fig)


# ----------------------------------------------------------------------------
def main():
    trc = os.path.join(HERE, "..", "data", "expressive_gait", "MotionCaptureData trc")
    trials = load_dataset(trc)
    y = np.array([t["label"] for t in trials])
    groups = np.array([t["subject"] for t in trials])

    Xe, feat_names = expert_features.build_matrix(trials)
    Xb = blackbox_prep.build_matrix(trials)
    print(f"Trials={len(trials)}  expert={Xe.shape}  blackbox={Xb.shape}")
    print(f"Subjects (LOSO folds): {sorted(set(groups))}\n")

    results = loso_evaluate(Xe, Xb, y, groups)

    # ---- report -----------------------------------------------------------
    print(f"{'method':28s} {'acc':>6s} {'mF1':>6s}  per-fold acc")
    print("-" * 70)
    for n, r in results.items():
        folds = " ".join(f"{a:.2f}" for a in r["fold_acc"])
        print(f"{n:28s} {r['acc']:6.3f} {r['macro_f1']:6.3f}  [{folds}]")
    print(f"\nchance level = {1/len(CLASSES):.2f}")

    print("\nRequested comparisons:")
    def line(tag, a, b):
        ra, rb = results[a], results[b]
        print(f"  {tag}\n     {a:26s} acc={ra['acc']:.3f} mF1={ra['macro_f1']:.3f}"
              f"\n     {b:26s} acc={rb['acc']:.3f} mF1={rb['macro_f1']:.3f}")
    line("1) Expert features vs pure black box",
         "A: Expert + RandomForest", "D: Raw + MLP (NN)")
    line("2) PCA vs Neural Net", "C: PCA + KNN", "D: Raw + MLP (NN)")
    line("3) Hand-crafted vs Autoencoder features (same LogReg)",
         "B: Expert + LogReg", "E: Autoencoder + LogReg")

    # ---- figures ----------------------------------------------------------
    for n in results:
        tag = n.split(":")[0].strip().lower()
        plot_confusion(results[n], n, f"cm_{tag}.png")
    plot_summary(results)
    plot_feature_importance(Xe, y, feat_names)
    plot_pca_scatter(Xb, y)

    # ---- save json --------------------------------------------------------
    dump = {n: {k: r[k] for k in ("acc", "macro_f1", "fold_acc", "fold_acc_std")}
            for n, r in results.items()}
    dump["_meta"] = {"n_trials": len(trials), "classes": CLASSES,
                     "expert_dim": Xe.shape[1], "blackbox_dim": Xb.shape[1],
                     "feature_names": feat_names, "cv": "leave-one-subject-out"}
    with open(os.path.join(OUT, "results.json"), "w") as f:
        json.dump(dump, f, indent=2)
    print(f"\nFigures + results.json written to {os.path.relpath(OUT)}/")


if __name__ == "__main__":
    main()
