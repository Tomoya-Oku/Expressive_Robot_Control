"""
Generate beginner-friendly algorithm diagrams (JPG, white background, English,
with formulas) for each method used in this homework.

Outputs (in docs/):
  overview.jpg              - the two feature philosophies + LOSO evaluation
  pca.jpg                   - Principal Component Analysis
  knn.jpg                   - k-Nearest Neighbors
  random_forest.jpg         - Random Forest
  logistic_regression.jpg   - Logistic Regression
  mlp.jpg                   - Multi-Layer Perceptron (neural network)
  autoencoder.jpg           - Autoencoder
"""

import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle, Ellipse

HERE = os.path.dirname(__file__)
FIGS = os.path.join(HERE, "..", "figs")  # algorithm diagrams live in Homework-2/figs/
os.makedirs(FIGS, exist_ok=True)
BLUE, ORANGE, GREEN, RED, GREY = "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#888888"


def new_fig(title):
    fig, ax = plt.subplots(figsize=(10, 6.2))
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis("off")
    ax.set_title(title, fontsize=17, fontweight="bold", pad=12)
    return fig, ax


def box(ax, x, y, w, h, text, fc="#eaf2fb", ec=BLUE, fs=11, tc="black"):
    ax.add_patch(
        FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.12",
                       fc=fc, ec=ec, lw=1.8, zorder=2)
    )
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
            fontsize=fs, color=tc, zorder=3)


def arrow(ax, x1, y1, x2, y2, c="black", lw=2.0):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>",
                 mutation_scale=18, lw=lw, color=c, zorder=2))


def note(ax, text, y=0.55, color="#333333"):
    ax.text(5, y, text, ha="center", va="center", fontsize=12.5,
            color=color, style="italic", wrap=True)


def save(fig, name):
    out = os.path.join(FIGS, name)
    fig.savefig(out, dpi=140, facecolor="white", bbox_inches="tight",
                pad_inches=0.25)
    plt.close(fig)
    print("wrote", os.path.relpath(out))


# ---------------------------------------------------------------------------
def fig_overview():
    fig, ax = new_fig("Overview: two feature philosophies, compared fairly")
    # left: expert path
    box(ax, 0.4, 7.2, 2.6, 1.3, "Motion capture\n(41 markers, 3D, 30 fps)",
        fc="#f2f2f2", ec=GREY)
    box(ax, 0.4, 4.7, 2.6, 1.3,
        "EXPERT features\n25 hand-made numbers\nspeed, posture, arm swing...",
        fc="#eafaef", ec=GREEN)
    box(ax, 0.4, 2.2, 2.6, 1.3,
        "BLACK-BOX raw\n64 frames x 41 x 3\n= 7872 numbers",
        fc="#fdeeee", ec=RED)
    arrow(ax, 1.7, 7.2, 1.7, 6.0)
    arrow(ax, 1.7, 7.2, 1.7, 3.5)
    # middle: models
    box(ax, 3.8, 6.4, 2.4, 0.9, "Random Forest / LogReg", fc="#eafaef", ec=GREEN)
    box(ax, 3.8, 4.9, 2.4, 0.9, "PCA + KNN", fc="#fdeeee", ec=RED)
    box(ax, 3.8, 3.4, 2.4, 0.9, "Neural Net (MLP)", fc="#fdeeee", ec=RED)
    box(ax, 3.8, 1.9, 2.4, 0.9, "Autoencoder + LogReg", fc="#fdeeee", ec=RED)
    arrow(ax, 3.0, 5.3, 3.8, 6.8);
    arrow(ax, 3.0, 2.8, 3.8, 5.3)
    arrow(ax, 3.0, 2.8, 3.8, 3.8); arrow(ax, 3.0, 2.8, 3.8, 2.3)
    # right: evaluation
    box(ax, 7.0, 4.0, 2.7, 1.6,
        "Leave-One-Subject-Out\ntrain on 3 actors,\ntest on the 4th\n(repeat x4)",
        fc="#eaf2fb", ec=BLUE)
    for yy in (6.85, 5.35, 3.85, 2.35):
        arrow(ax, 6.2, yy, 7.0, 4.9, c=GREY, lw=1.4)
    box(ax, 7.6, 1.7, 1.6, 0.9, "accuracy\nmacro-F1", fc="#fff7e6", ec=ORANGE)
    arrow(ax, 8.35, 4.0, 8.35, 2.6)
    note(ax, r"Goal: classify emotion $\in$ {anger, joy, neutral, sad}."
             r"  Same data, same split $\Rightarrow$ a fair comparison.", y=0.7)
    save(fig, "overview.jpg")


# ---------------------------------------------------------------------------
def fig_pca():
    fig, ax = new_fig("PCA - Principal Component Analysis (dimensionality reduction)")
    # scatter with principal axes
    rng = np.random.default_rng(1)
    pts = rng.normal(0, 1, (60, 2)) @ np.array([[1.6, 0.9], [0.0, 0.45]])
    cx, cy = 2.4, 6.1
    sx, sy = 0.7, 0.7
    ax.scatter(cx + pts[:, 0] * sx, cy + pts[:, 1] * sy, s=22, color=BLUE, alpha=0.7)
    arrow(ax, cx, cy, cx + 1.9, cy + 1.05, c=RED, lw=2.6)      # PC1
    arrow(ax, cx, cy, cx - 0.5, cy + 0.9, c=GREEN, lw=2.2)     # PC2
    ax.text(cx + 1.95, cy + 1.15, "PC1\n(max variance)", color=RED, fontsize=10)
    ax.text(cx - 1.4, cy + 1.0, "PC2", color=GREEN, fontsize=10)

    box(ax, 6.0, 7.0, 3.4, 1.9,
        "Idea: find new axes (principal\ncomponents) along which the\n"
        "data spreads the most, then\nkeep only the first few.",
        fc="#eaf2fb", ec=BLUE, fs=11)

    ax.text(5.0, 4.2,
            r"$\tilde{x}=x-\bar{x}$  (center the data)" "\n\n"
            r"$C=\frac{1}{N}\sum_i \tilde{x}_i \tilde{x}_i^{\top}$  (covariance)" "\n\n"
            r"$C\,v_k=\lambda_k v_k$  (eigenvectors $v_k$, variance $\lambda_k$)" "\n\n"
            r"$z = W_k^{\top}\,\tilde{x}\quad$ keep top-$k$ axes  $(W_k=[v_1..v_k])$",
            ha="center", va="center", fontsize=13)
    note(ax, r"Here: 7872 raw numbers $\rightarrow$ 20 components. Fewer dims = less noise & overfitting.")
    save(fig, "pca.jpg")


# ---------------------------------------------------------------------------
def fig_knn():
    fig, ax = new_fig("k-NN - k-Nearest Neighbors (vote of the closest points)")
    rng = np.random.default_rng(3)
    a = rng.normal([2.3, 6.8], 0.55, (12, 2))
    b = rng.normal([4.0, 5.6], 0.55, (12, 2))
    ax.scatter(a[:, 0], a[:, 1], s=45, color=BLUE, label="class A", zorder=3)
    ax.scatter(b[:, 0], b[:, 1], s=45, color=ORANGE, marker="s",
               label="class B", zorder=3)
    q = np.array([3.1, 6.2])
    ax.scatter(*q, s=160, color=RED, marker="*", zorder=4, label="new point ?")
    # neighborhood circle (k=5)
    dists = np.sort(np.linalg.norm(np.vstack([a, b]) - q, axis=1))
    r = dists[4] + 0.05
    ax.add_patch(Circle(q, r, fill=False, ec=RED, ls="--", lw=1.8))
    ax.legend(loc="upper right", fontsize=10, framealpha=1)

    ax.text(7.4, 4.4,
            r"distance:" "\n"
            r"$d(x,x_i)=\sqrt{\sum_j (x_j-x_{ij})^2}$" "\n\n"
            r"predict the majority label" "\n"
            r"among the $k$ closest points:" "\n"
            r"$\hat{y}=\mathrm{mode}\{\,y_i : x_i \in N_k(x)\,\}$",
            ha="center", va="center", fontsize=12.5)
    note(ax, r"No training - just store all points and let the $k=5$ nearest neighbors vote.")
    save(fig, "knn.jpg")


# ---------------------------------------------------------------------------
def _mini_tree(ax, x, y, leaf_color):
    box(ax, x - 0.35, y, 0.7, 0.4, "x?", fc="white", ec=GREY, fs=8)
    for dx in (-0.8, 0.8):
        box(ax, x + dx - 0.32, y - 0.9, 0.64, 0.38, "x?", fc="white", ec=GREY, fs=8)
        arrow(ax, x, y, x + dx, y - 0.5, c=GREY, lw=1.2)
    for dx in (-1.2, -0.4, 0.4, 1.2):
        ax.add_patch(Circle((x + dx, y - 1.5), 0.16, color=leaf_color, zorder=3))
        arrow(ax, x + (0.8 if dx > 0 else -0.8), y - 0.9, x + dx, y - 1.34,
              c=GREY, lw=1.0)


def fig_random_forest():
    fig, ax = new_fig("Random Forest (many decision trees vote)")
    cols = [BLUE, ORANGE, GREEN]
    for i, x in enumerate([1.9, 4.0, 6.1]):
        _mini_tree(ax, x, 8.2, cols[i])
        ax.text(x, 6.2, f"tree {i+1}", ha="center", fontsize=9, color=GREY)
    box(ax, 7.6, 7.3, 2.0, 1.0, "majority\nvote", fc="#fff7e6", ec=ORANGE, fs=12)
    for x in (1.9, 4.0, 6.1):
        arrow(ax, x, 6.5, 7.6, 7.8, c=GREY, lw=1.2)
    box(ax, 7.9, 5.3, 1.4, 0.8, "class", fc="#eaf2fb", ec=BLUE)
    arrow(ax, 8.6, 7.3, 8.6, 6.1)

    ax.text(5.0, 3.9,
            r"each tree asks yes/no questions on features and splits to" "\n"
            r"reduce node impurity (Gini):  "
            r"$G=1-\sum_c p_c^{\,2}$" "\n\n"
            r"forest prediction = majority over $B$ trees:" "\n"
            r"$\hat{y}=\mathrm{mode}\{\,T_1(x),\,T_2(x),\,\dots,\,T_B(x)\,\}$",
            ha="center", va="center", fontsize=12.5)
    note(ax, r"Each tree sees random data/features; averaging many trees cuts overfitting. Here: $B=300$.")
    save(fig, "random_forest.jpg")


# ---------------------------------------------------------------------------
def fig_logreg():
    fig, ax = new_fig("Logistic Regression (weighted sum -> probabilities)")
    xs = [1.4]
    feats = ["$x_1$", "$x_2$", "$x_3$", r"$\vdots$", "$x_d$"]
    ys = np.linspace(8.3, 5.3, 5)
    for f, yy in zip(feats, ys):
        ax.add_patch(Circle((1.4, yy), 0.22, fc="#eaf2fb", ec=BLUE, zorder=3))
        ax.text(1.4, yy, f, ha="center", va="center", fontsize=11, zorder=4)
    box(ax, 3.4, 6.4, 1.7, 1.0, r"$z=w^{\top}x+b$", fc="#fff7e6", ec=ORANGE, fs=12)
    for yy in ys:
        arrow(ax, 1.65, yy, 3.4, 6.9, c=GREY, lw=1.0)
    box(ax, 5.7, 6.4, 1.9, 1.0, "softmax", fc="#eafaef", ec=GREEN, fs=12)
    arrow(ax, 5.1, 6.9, 5.7, 6.9)
    # prob bars
    labels = ["anger", "joy", "neutral", "sad"]
    probs = [0.1, 0.15, 0.2, 0.55]
    bx = 8.7
    for i, (lb, p) in enumerate(zip(labels, probs)):
        yy = 7.7 - i * 0.45
        ax.barh(yy, p * 1.2, height=0.32, left=bx, color=BLUE, alpha=0.8)
        ax.text(bx - 0.15, yy, lb, ha="right", va="center", fontsize=8.5)
    arrow(ax, 7.6, 6.9, 8.0, 6.9)

    ax.text(5.0, 3.7,
            r"score per class:  $z_c=w_c^{\top}x+b_c$" "\n\n"
            r"softmax $\rightarrow$ probabilities:  "
            r"$P(y=c\,|\,x)=\dfrac{e^{z_c}}{\sum_k e^{z_k}}$" "\n\n"
            r"(binary view: sigmoid $\sigma(z)=\dfrac{1}{1+e^{-z}}$)",
            ha="center", va="center", fontsize=12.5)
    note(ax, r"A linear model: weighted sum of features squashed into class probabilities. Simple & interpretable.")
    save(fig, "logistic_regression.jpg")


# ---------------------------------------------------------------------------
def _layer(ax, x, ys, color):
    for yy in ys:
        ax.add_patch(Circle((x, yy), 0.20, fc=color, ec="black", lw=0.8, zorder=3))
    return [(x, yy) for yy in ys]


def fig_mlp():
    fig, ax = new_fig("Neural Network (MLP) - layers of neurons")
    L0 = _layer(ax, 1.6, np.linspace(8.2, 4.6, 5), "#eaf2fb")
    L1 = _layer(ax, 3.8, np.linspace(8.4, 4.4, 6), "#fff7e6")
    L2 = _layer(ax, 6.0, np.linspace(7.6, 5.2, 4), "#fff7e6")
    L3 = _layer(ax, 8.2, np.linspace(7.4, 5.4, 4), "#eafaef")
    for A, B in [(L0, L1), (L1, L2), (L2, L3)]:
        for (x1, y1) in A:
            for (x2, y2) in B:
                ax.plot([x1, x2], [y1, y2], color=GREY, lw=0.3, zorder=1)
    for xx, lab in [(1.6, "input\nx"), (3.8, "hidden\n128"), (6.0, "hidden\n32"),
                    (8.2, "output\n4 classes")]:
        ax.text(xx, 3.9, lab, ha="center", fontsize=9, color=GREY)

    ax.text(5.0, 3.0,
            r"$h^{(1)}=\mathrm{ReLU}(W^{(1)}x+b^{(1)})$,   "
            r"$h^{(2)}=\mathrm{ReLU}(W^{(2)}h^{(1)}+b^{(2)})$" "\n"
            r"$\hat{y}=\mathrm{softmax}(W^{(3)}h^{(2)}+b^{(3)})$,   "
            r"$\mathrm{ReLU}(z)=\max(0,z)$" "\n\n"
            r"learn weights $W$ by minimizing cross-entropy via gradient descent",
            ha="center", va="center", fontsize=12)
    note(ax, r"Stacked weighted sums + nonlinearity learn complex patterns - but need lots of data.", y=0.5)
    save(fig, "mlp.jpg")


# ---------------------------------------------------------------------------
def fig_autoencoder():
    fig, ax = new_fig("Autoencoder - learn compact features without labels")
    L0 = _layer(ax, 1.5, np.linspace(8.4, 4.6, 6), "#fdeeee")
    L1 = _layer(ax, 3.3, np.linspace(7.9, 5.1, 4), "#fff7e6")
    Lz = _layer(ax, 5.0, np.linspace(7.0, 6.0, 2), "#eafaef")
    L3 = _layer(ax, 6.7, np.linspace(7.9, 5.1, 4), "#fff7e6")
    L4 = _layer(ax, 8.5, np.linspace(8.4, 4.6, 6), "#fdeeee")
    for A, B in [(L0, L1), (L1, Lz), (Lz, L3), (L3, L4)]:
        for (x1, y1) in A:
            for (x2, y2) in B:
                ax.plot([x1, x2], [y1, y2], color=GREY, lw=0.3, zorder=1)
    ax.text(1.5, 4.0, "input x\n(7872)", ha="center", fontsize=9, color=GREY)
    ax.text(5.0, 7.85, "bottleneck z (16)", ha="center", fontsize=9.5,
            color=GREEN, fontweight="bold")
    ax.text(8.5, 4.0, r"reconstruction $\hat{x}$", ha="center", fontsize=9, color=GREY)
    ax.text(2.4, 8.7, "encoder", color=ORANGE, fontsize=11)
    ax.text(7.0, 8.7, "decoder", color=ORANGE, fontsize=11)
    arrow(ax, 5.0, 5.7, 5.0, 4.4, c=GREEN, lw=2.0)
    box(ax, 4.0, 3.4, 2.0, 0.8, "z = features\nfor classifier", fc="#eafaef", ec=GREEN, fs=10)

    ax.text(5.0, 2.3,
            r"encode $z=f(x)$,   decode $\hat{x}=g(z)$,   "
            r"train to reconstruct:  $L=\| x-\hat{x}\|^{2}$" "\n\n"
            r"the small bottleneck $z$ is then used as input features (unsupervised)",
            ha="center", va="center", fontsize=12)
    note(ax, r"Squeeze data into a few numbers that still rebuild it; those numbers become features. Here: 16-d.", y=0.55)
    save(fig, "autoencoder.jpg")


if __name__ == "__main__":
    fig_overview()
    fig_pca()
    fig_knn()
    fig_random_forest()
    fig_logreg()
    fig_mlp()
    fig_autoencoder()
    print("done")
