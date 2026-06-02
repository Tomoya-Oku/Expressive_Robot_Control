# Homework-2 — Emotion classification from expressive gait (method comparison)

Using the College de France **expressive gait database** (motion capture), we
classify the emotion expressed while walking. We compare **two feature
philosophies** — expert hand-crafted features vs. a pure black-box on raw data —
across several models.

日本語版: [README_JA.md](README_JA.md)

---

## Glossary of abbreviations (by category)

There are many acronyms, so here is a beginner-friendly, categorised cheat sheet.

**A. Data & recording format**
| Abbr. | Full name | Meaning |
|---|---|---|
| TRC | Track Row Column | motion-capture format storing 3D marker trajectories over time |
| fps | frames per second | frames recorded per second (this data: 30 fps) |
| marker | — | reflective marker on the body (41 here) |
| ROM | Range Of Motion | joint angular range (max − min) |
| CoM | Center of Mass | body center of mass (approximated near the pelvis) |

**B. Evaluation terms**
| Abbr. | Full name | Meaning |
|---|---|---|
| CV | Cross-Validation | split data, repeat train/test |
| LOSO | Leave-One-Subject-Out | hold out a whole actor for testing; prevents subject leakage |
| chance | chance level | accuracy of random guessing (0.25 for 4 classes) |
| acc | accuracy | fraction correct |
| macro-F1 | macro-averaged F1 | mean of per-class F1 (robust to class imbalance) |

**C. Feature philosophy**
| Abbr. | Full name | Meaning |
|---|---|---|
| Expert features | — | interpretable features designed by hand from domain knowledge |
| Black-box / Raw | — | use the raw coordinates directly, designing nothing |
| PCA | Principal Component Analysis | reduce dimensions along directions of largest variance |
| AE | Autoencoder | compress→reconstruct; use the bottleneck as features (unsupervised) |
| bottleneck | — | the narrowest middle layer of an AE (the learned feature vector) |
| dim(s) | dimension(s) | length of a feature vector |

**D. Models / classifiers**
| Abbr. | Full name | Meaning |
|---|---|---|
| RF | Random Forest | majority vote over many decision trees |
| LogReg | Logistic Regression | linear weighted sum + softmax → probabilities |
| KNN | k-Nearest Neighbors | majority vote of the k closest points (k=5 here) |
| MLP / NN | Multi-Layer Perceptron / Neural Network | a multi-layer neural network |
| softmax | — | turns scores into probabilities (summing to 1) |
| ReLU | Rectified Linear Unit | activation function max(0, z) |
| L2 (alpha) | L2 regularization | strength of regularization that fights overfitting |

**E. Emotion labels (French codes, from College de France)**
| Code | French | Emotion |
|---|---|---|
| COE | colère | anger |
| JOE | joie | joy |
| NEE | neutre | neutral |
| TRE | triste | sad |

---

## 1. Data

- Source: the Dropbox folder given in the assignment (extracted to `data/expressive_gait/`).
- Contents: `MotionCaptureData trc/` (**used here**), `JointAngleData anm_scaled/`,
  `anm_scaled/`, `A few videos/`.
- We use the **TRC motion capture** (`.trc`): 41 markers, 3D coordinates, 30 fps.
- **81 trials** = 4 actors (NABA / PAIB / SALE / EMLA) × 4 emotions × ~5 trials.
- Labels come from the French code in each filename:
  `COE=colère(anger)`, `JOE=joie(joy)`, `NEE=neutre(neutral)`, `TRE=triste(sad)`.
- Classes are nearly balanced (anger 20 / joy 20 / neutral 21 / sad 20). Chance = 0.25.

Axes: X = lateral, **Y = vertical**, Z = walking direction.

> The dataset itself is **not** committed (course-distributed, redistribution
> rights unclear, ~55 MB). It is excluded via `.gitignore`; download it yourself.

---

## 2. Two feature philosophies

| | Expert features | Black-box (Raw) |
|---|---|---|
| Content | walking speed, cadence, stride length, trunk inclination, head tilt, arm-swing amplitude, elbow/knee ROM, motion energy/jerk, … — **25 interpretable scalars** | each trial resampled to 64 frames, pelvis-centred and height-normalised raw marker coordinates, flattened (**7872 dims**) |
| Idea | inject affective-gait domain knowledge by hand | inject nothing; let the model find structure |
| Code | [src/expert_features.py](../src/expert_features.py) | [src/blackbox_prep.py](../src/blackbox_prep.py) |

---

## 3. Methods (5 runs) and comparison design

| Run | Features | Model |
|---|---|---|
| A | Expert | RandomForest |
| B | Expert | LogisticRegression |
| C | Raw → PCA(20) | KNN |
| D | Raw | MLP (neural network) |
| E | Raw → Autoencoder(16) | LogisticRegression |

The assignment asks to compare **two methods**; we draw **three** such
comparisons from the five runs:

1. **Expert features vs pure black box** … A vs D
2. **PCA vs neural network** … C vs D
3. **Hand-crafted vs autoencoder features** … B vs E
   (downstream classifier **fixed to LogisticRegression**; only the feature
   source changes — a clean, controlled comparison)

### Why these comparisons
- Comparison 1: the most direct test of "injecting domain knowledge or not".
- Comparison 2: on the same raw data, **linear dimensionality reduction + simple
  classifier** vs a **non-linear learner**.
- Comparison 3: fixing the classifier attributes any difference **purely to the
  features**, the cleanest controlled experiment.

### Algorithm diagrams (beginner-friendly, with formulas)
One diagram per method (JPG, white background, English; generated by
[../src/make_figures.py](../src/make_figures.py)).

**Overview** — the two feature philosophies and the LOSO evaluation

![overview](../figs/overview.jpg)

| Method | Diagram |
|---|---|
| PCA (dimensionality reduction) | ![pca](../figs/pca.jpg) |
| k-NN (vote of nearest points) | ![knn](../figs/knn.jpg) |
| Random Forest (trees vote) | ![rf](../figs/random_forest.jpg) |
| Logistic Regression (linear + softmax) | ![logreg](../figs/logistic_regression.jpg) |
| Neural Net / MLP | ![mlp](../figs/mlp.jpg) |
| Autoencoder (unsupervised features) | ![ae](../figs/autoencoder.jpg) |

---

## 4. Evaluation: Leave-One-Subject-Out (LOSO)

4-fold cross-validation holding out one of the 4 actors each time. Since the test
actor never appears in training, this honestly measures whether the model
captures **the emotion** rather than **who is walking** (no subject leakage).
Scaler / PCA / AE are fit on the training fold only.

---

## 5. Results (LOSO)

| Method | accuracy | macro F1 |
|---|---|---|
| **A: Expert + RandomForest** | **0.91** | **0.92** |
| B: Expert + LogReg | 0.75 | 0.76 |
| C: PCA + KNN | 0.49 | 0.48 |
| D: Raw + MLP (NN) | 0.40 | 0.39 |
| E: Autoencoder + LogReg | 0.52 | 0.51 |

Chance = 0.25. Figures are in [outputs/](../outputs/)
(`summary_scores.png`, `cm_*.png`, `expert_feature_importance.png`, `pca_scatter.png`).

### Reading each comparison
1. **A(0.91) ≫ D(0.40)**: with only ~60 training trials, the raw-data NN overfits
   in high dimension. Hand-crafted expert features win decisively —
   **domain knowledge pays off on small data**.
2. **C(0.49) > D(0.40)**: on the same raw data, compressing to 20 PCA dims then
   KNN is more robust than feeding 7872 dims straight to an NN — the
   **curse of dimensionality** in action.
3. **B(0.75) > E(0.52)**: even with the classifier fixed, hand-crafted features
   beat autoencoder features. Still, the AE beats raw-fed (D) and PCA (C),
   showing it **learns a useful representation unsupervised**.

### Takeaways
- Top features (`expert_feature_importance.png`) are **motion energy/jerk, trunk
  inclination, elbow ROM, arm swing** — matching the affective-gait literature
  (anger/joy = fast & large; sadness = forward-leaning, little arm swing).
- In the confusion matrices, **sad is almost perfectly separated**; errors
  concentrate on anger↔joy (both high-energy).
- Lesson: **the smaller the data, the more valuable hand-designed features are.**
  Beating expert features with black-box/deep representations would need more data.

### What makes this experiment interesting
- **A counterexample to "deeper = better"**: with ~80 trials and 7872 raw dims,
  the black-box NN (D) overfits and ranks last, while 25 hand-made features (A)
  win at 0.91 — on small data, domain knowledge wins.
- **Comparison 3 is the cleanest**: with the classifier fixed to LogReg, the gap
  B(0.75) vs E(0.52) is purely a **difference in feature quality**. The AE,
  despite being unsupervised, beats raw (D) and PCA (C) — "you can learn useful
  representations without labels, but not yet better than expert knowledge."
- **The curse of dimensionality, visualised**: C>D shows that merely dropping to
  20 dims makes things more robust than feeding an NN 7872 dims. In
  `pca_scatter.png`, PC1/PC2 mostly capture **subject / capture-volume**
  differences rather than emotion — exactly why raw data struggles.
- **Top features match the literature**: motion energy/jerk, trunk inclination,
  elbow ROM, arm swing. Sad is almost perfectly separated; errors cluster on
  anger↔joy (both high-arousal) — textbook affective-gait behaviour.

---

## 6. How to run

```bash
cd Homework-2
pip install -r requirements.txt
python3 src/main.py          # prints the table; writes figures + results.json to outputs/
```

Each module self-tests when run directly:
`python3 src/data_loader.py` / `expert_features.py` / `blackbox_prep.py`.

## 7. Files
- [src/data_loader.py](../src/data_loader.py) … TRC parsing, label/subject extraction
- [src/expert_features.py](../src/expert_features.py) … 25 expert features
- [src/blackbox_prep.py](../src/blackbox_prep.py) … raw-data preprocessing
- [src/methods/](../src/methods/) … **one file per method** (each exposes `run()`)
  - [expert_rf.py](../src/methods/expert_rf.py) / [expert_logreg.py](../src/methods/expert_logreg.py) / [pca_knn.py](../src/methods/pca_knn.py) / [raw_mlp.py](../src/methods/raw_mlp.py) / [ae_logreg.py](../src/methods/ae_logreg.py)
- [src/main.py](../src/main.py) … 5 methods × LOSO evaluation, experiment figures
- [src/make_figures.py](../src/make_figures.py) … generates the algorithm diagrams (figs/)
- [outputs/](../outputs/) … experiment figures, `results.json`
- [figs/](../figs/) … algorithm diagrams (JPG)
- [docs/](.) … READMEs (JP/EN)

---

## 8. Directions for improvement

**(A) Evaluation stability** (high impact, low cost)
- With only 4 actors, LOSO folds vary a lot (e.g. A ranges 0.80–1.00). Use
  **nested CV**, repetition, and confidence intervals to make conclusions robust.

**(B) Give the black box a fair fight** (most promising)
- The flat 7872-d + MLP throws away temporal structure. Use **1D-CNN / LSTM /
  Transformer** to model the time series, or **data augmentation** (time warping,
  speed jitter, left-right flip, cropping) to enlarge the effective sample size,
  and directly test *"does deep learning overtake expert features with more data?"*

**(C) Better features**
- Search the AE **bottleneck size**; switch to a **convolutional AE** that keeps
  the time axis. Add **symmetry, phase, frequency spectra, gait-cycle-normalised
  time-series statistics** to the expert features.

**(D) Use the unused data**
- We used TRC only. `JointAngleData` (joint angles) enables a new axis:
  **"marker-coordinate features vs joint-angle features"**. Pose-estimating the
  `A few videos/` would also connect back to Homework-1.

**(E) Rethink the labels**
- anger↔joy mix because they share high arousal but opposite valence. A
  **two-stage (arousal → valence)** scheme or cross-subject normalisation could
  address the structure of the errors.
