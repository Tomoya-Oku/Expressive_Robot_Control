"""
Loader for the College de France expressive gait database (TRC motion capture).

Each .trc file is one walking trial recorded with a Vicon-like marker system:
  - 41 markers, 3D coordinates (mm), 30 fps.
  - Axes: X = lateral, Y = vertical (up), Z = walking direction (depth).

File names encode the subject and the expressed emotion, e.g. "NABACOE03.4.trc":
  - subject : first 4 letters  (NABA, PAIB, SALE, EMLA)  -> the actor
  - emotion : next 3 letters (French)
        COE = colere   (anger)
        JOE = joie     (joy)
        NEE = neutre   (neutral)
        TRE = triste   (sad)
Some EMLA files carry an extra "a_" prefix which we strip before parsing.
"""

import os
import glob
import numpy as np

# 41 marker names in column order (subject prefix removed).
MARKERS = [
    "LFHD", "RFHD", "LBHD", "RBHD", "LFTShould", "RFTShould", "LRRShould",
    "RRRShould", "T10", "STRN", "TRUN", "LSHO", "LUPA", "LELB", "LFRM", "LWRA",
    "LWRB", "LFIN", "RSHO", "RUPA", "RELB", "RFRM", "RWRA", "RWRB", "RFIN",
    "LFWT", "RFWT", "LBWT", "RBWT", "LTHI", "LKNE", "LSHN", "LANK", "LHEE",
    "LTOE", "RTHI", "RKNE", "RSHN", "RANK", "RHEE", "RTOE",
]
MARKER_IDX = {name: i for i, name in enumerate(MARKERS)}

EMOTION_CODES = {"COE": "anger", "JOE": "joy", "NEE": "neutral", "TRE": "sad"}
FPS = 30.0


def parse_trc(path):
    """Parse one .trc file into an array of shape (frames, 41, 3).

    Marker dropouts are stored as 0.0 in the file; we convert them to NaN and
    linearly interpolate (then forward/back fill) so downstream code is clean.
    """
    with open(path, "r", errors="ignore") as f:
        lines = f.readlines()
    # Header: line0 PathFileType, line1 meta-keys, line2 meta-values,
    # line3 marker names, line4 X1/Y1/..., line5 blank, data from line6.
    # NumMarkers is the 4th value on the meta-values line; a few files carry
    # extra trailing columns, so we trust this count.
    try:
        n_markers = int(lines[2].split("\t")[3])
    except (IndexError, ValueError):
        n_markers = len(MARKERS)
    data_lines = [ln for ln in lines[5:] if ln.strip()]
    rows = []
    for ln in data_lines:
        parts = ln.rstrip("\n").split("\t")
        if len(parts) < 2:
            continue
        vals = parts[2:]  # drop Frame# and Time
        rows.append([float(v) if v.strip() else np.nan for v in vals])
    arr = np.array(rows, dtype=float)  # (frames, n_markers*3)
    arr = arr[:, : n_markers * 3].reshape(arr.shape[0], n_markers, 3)
    arr[arr == 0.0] = np.nan
    arr = _fill_gaps(arr)
    return arr


def _fill_gaps(arr):
    """Linearly interpolate NaNs along time for each marker/axis."""
    T = arr.shape[0]
    t = np.arange(T)
    out = arr.copy()
    for m in range(arr.shape[1]):
        for c in range(arr.shape[2]):
            col = arr[:, m, c]
            good = ~np.isnan(col)
            if good.sum() == 0:
                out[:, m, c] = 0.0
            elif good.sum() < T:
                out[:, m, c] = np.interp(t, t[good], col[good])
    return out


def parse_name(fname):
    """Return (subject, emotion_label) from a .trc filename."""
    base = os.path.basename(fname)
    base = base[:-4] if base.lower().endswith(".trc") else base
    if base.startswith("a_"):
        base = base[2:]
    subject = base[:4]
    emo_code = base[4:7]
    return subject, EMOTION_CODES.get(emo_code, "unknown")


def load_dataset(trc_dir):
    """Load every trial. Returns list of dicts with keys:
    name, subject, label, seq (frames,41,3)."""
    paths = sorted(glob.glob(os.path.join(trc_dir, "*.trc")))
    trials = []
    for p in paths:
        subject, label = parse_name(p)
        if label == "unknown":
            continue
        seq = parse_trc(p)
        trials.append(
            {
                "name": os.path.basename(p),
                "subject": subject,
                "label": label,
                "seq": seq,
            }
        )
    return trials


if __name__ == "__main__":
    here = os.path.dirname(__file__)
    trc_dir = os.path.join(here, "..", "data", "expressive_gait", "MotionCaptureData trc")
    trials = load_dataset(trc_dir)
    print(f"Loaded {len(trials)} trials")
    lengths = [t["seq"].shape[0] for t in trials]
    print(f"frames: min={min(lengths)} max={max(lengths)} mean={np.mean(lengths):.0f}")
    from collections import Counter
    print("labels  :", dict(Counter(t["label"] for t in trials)))
    print("subjects:", dict(Counter(t["subject"] for t in trials)))
    ex = trials[0]
    print(f"example {ex['name']}: seq{ex['seq'].shape}, nan={np.isnan(ex['seq']).sum()}")
