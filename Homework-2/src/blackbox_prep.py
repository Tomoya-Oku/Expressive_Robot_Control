"""
Black-box preprocessing of raw marker trajectories.

No biomechanical interpretation is injected here: we just turn each
variable-length trial into a fixed-size numeric vector and let the model
(PCA / MLP / autoencoder) discover whatever structure is useful.

Steps per trial:
  1. resample the (frames, 41, 3) sequence to a fixed length T along time,
  2. translate so the first-frame pelvis sits at the origin (remove the
     arbitrary capture-volume offset, but keep within-trial displacement so
     walking speed/energy survive),
  3. scale by the actor's body height (subject-size invariance),
  4. flatten to a single vector of length T*41*3.
"""

import numpy as np
from data_loader import MARKER_IDX

T = 64  # resampled frames
Y = 1
PELVIS = ["LFWT", "RFWT", "LBWT", "RBWT"]


def _resample(seq, T):
    n = seq.shape[0]
    src = np.linspace(0, 1, n)
    dst = np.linspace(0, 1, T)
    out = np.empty((T, seq.shape[1], seq.shape[2]))
    for m in range(seq.shape[1]):
        for c in range(seq.shape[2]):
            out[:, m, c] = np.interp(dst, src, seq[:, m, c])
    return out


def preprocess(seq, T=T):
    pelvis_idx = [MARKER_IDX[n] for n in PELVIS]
    head_idx = [MARKER_IDX[n] for n in ["LFHD", "RFHD", "LBHD", "RBHD"]]
    ankle_idx = [MARKER_IDX[n] for n in ["LANK", "RANK"]]

    height = np.median(
        seq[:, head_idx, Y].mean(1) - seq[:, ankle_idx, Y].mean(1)
    )
    height = height if height > 1 else 1000.0

    r = _resample(seq, T)
    origin = r[0, pelvis_idx, :].mean(0)  # first-frame pelvis
    r = (r - origin) / height
    return r.reshape(-1)


def build_matrix(trials, T=T):
    X = np.array([preprocess(t["seq"], T) for t in trials], dtype=float)
    X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)
    return X


if __name__ == "__main__":
    import os
    from data_loader import load_dataset
    here = os.path.dirname(__file__)
    trc = os.path.join(here, "..", "data", "expressive_gait", "MotionCaptureData trc")
    trials = load_dataset(trc)
    X = build_matrix(trials)
    print(f"Black-box matrix: {X.shape}  (= {len(trials)} trials x {T}*41*3={T*41*3})")
    print(f"range: [{X.min():.3f}, {X.max():.3f}], mean={X.mean():.3f}")
