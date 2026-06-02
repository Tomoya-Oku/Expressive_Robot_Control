"""
Expert (hand-crafted) features for expressive gait.

These features are motivated by the affective-gait literature, where emotions
are known to modulate interpretable biomechanical quantities:
  - anger / joy  -> faster walking, larger strides, bigger arm swing, more energy
  - sadness      -> slow gait, slumped trunk, lowered head, reduced arm swing
  - neutral      -> baseline

We summarise each variable-length trial into a fixed vector of ~30 scalars.
Lengths are normalised by the actor's body height so the descriptors are
comparable across subjects of different size.
"""

import numpy as np
from data_loader import MARKER_IDX, FPS

# Axis convention in this dataset: X lateral, Y vertical (up), Z walking dir.
Y = 1  # vertical


def _m(seq, name):
    """Time series (frames,3) for a marker name."""
    return seq[:, MARKER_IDX[name], :]


def _mid(seq, names):
    return np.mean([_m(seq, n) for n in names], axis=0)


def _angle(a, b, c):
    """Per-frame angle (deg) at joint b for the chain a-b-c."""
    v1 = a - b
    v2 = c - b
    n1 = np.linalg.norm(v1, axis=1) + 1e-8
    n2 = np.linalg.norm(v2, axis=1) + 1e-8
    cos = np.sum(v1 * v2, axis=1) / (n1 * n2)
    return np.degrees(np.arccos(np.clip(cos, -1, 1)))


def _dominant_freq(signal, fps=FPS):
    """Dominant oscillation frequency (Hz) of a 1D signal, ignoring DC."""
    sig = signal - np.mean(signal)
    if len(sig) < 8:
        return 0.0
    spec = np.abs(np.fft.rfft(sig * np.hanning(len(sig))))
    freqs = np.fft.rfftfreq(len(sig), d=1.0 / fps)
    spec[0] = 0
    band = (freqs > 0.3) & (freqs < 4.0)  # plausible gait cadence range
    if not band.any() or spec[band].max() == 0:
        return 0.0
    return float(freqs[band][np.argmax(spec[band])])


def extract(seq):
    """Return an ordered dict of expert features for one trial."""
    f = {}
    pelvis = _mid(seq, ["LFWT", "RFWT", "LBWT", "RBWT"])
    shoulder = _mid(seq, ["LSHO", "RSHO"])
    head = _mid(seq, ["LFHD", "RFHD", "LBHD", "RBHD"])
    ankle = _mid(seq, ["LANK", "RANK"])

    # Body height (scale) = head-to-ankle vertical span, used for normalisation.
    height = np.median(head[:, Y] - ankle[:, Y])
    height = height if height > 1 else 1000.0
    dt = 1.0 / FPS
    dur = len(seq) * dt

    # --- Gait dynamics -------------------------------------------------------
    horiz = pelvis[:, [0, 2]]  # X,Z plane
    path = np.sum(np.linalg.norm(np.diff(horiz, axis=0), axis=1))
    f["speed"] = (path / dur) / height                  # body-heights / s
    cad = _dominant_freq(ankle[:, Y])
    f["cadence"] = cad                                   # steps/strides per s
    f["stride_len"] = (f["speed"] / cad) if cad > 0 else 0.0
    f["com_vert_osc"] = np.std(pelvis[:, Y]) / height    # bounce
    f["lateral_sway"] = np.std(pelvis[:, 0]) / height

    # --- Posture -------------------------------------------------------------
    trunk_vec = shoulder - pelvis
    # inclination from vertical (0 deg = upright)
    incl = np.degrees(
        np.arccos(np.clip(trunk_vec[:, Y] / (np.linalg.norm(trunk_vec, axis=1) + 1e-8), -1, 1))
    )
    f["trunk_incl_mean"] = np.mean(incl)
    f["trunk_incl_std"] = np.std(incl)
    f["head_height"] = np.median(head[:, Y] - shoulder[:, Y]) / height  # head drop if low
    head_vec = head - shoulder
    head_incl = np.degrees(
        np.arccos(np.clip(head_vec[:, Y] / (np.linalg.norm(head_vec, axis=1) + 1e-8), -1, 1))
    )
    f["head_incl_mean"] = np.mean(head_incl)

    # --- Arm swing -----------------------------------------------------------
    for side in ["L", "R"]:
        wr = _m(seq, side + "WRA")
        rel = wr - pelvis  # relative to body
        f[f"arm_swing_{side}"] = (np.ptp(rel[:, 2]) + np.ptp(rel[:, 0])) / height
        elb = _angle(_m(seq, side + "SHO"), _m(seq, side + "ELB"), _m(seq, side + "WRA"))
        f[f"elbow_mean_{side}"] = np.mean(elb)
        f[f"elbow_rom_{side}"] = np.ptp(elb)
    f["arm_swing_asym"] = abs(f["arm_swing_L"] - f["arm_swing_R"])

    # --- Legs ----------------------------------------------------------------
    for side in ["L", "R"]:
        hip = _m(seq, side + "FWT")
        knee = _angle(hip, _m(seq, side + "KNE"), _m(seq, side + "ANK"))
        f[f"knee_rom_{side}"] = np.ptp(knee)
        an = _m(seq, side + "ANK")
        f[f"foot_lift_{side}"] = np.ptp(an[:, Y]) / height
    f["step_asym"] = abs(f["foot_lift_L"] - f["foot_lift_R"])

    # --- Overall energy / smoothness ----------------------------------------
    vel = np.diff(seq, axis=0) / dt                      # (T-1,41,3)
    acc = np.diff(vel, axis=0) / dt
    f["mean_speed_all"] = np.mean(np.linalg.norm(vel, axis=2)) / height
    f["mean_jerk_all"] = np.mean(np.linalg.norm(acc, axis=2)) / height
    f["energy_var"] = np.std(np.linalg.norm(vel, axis=2)) / height

    # --- Shoulder span (openness) -------------------------------------------
    f["shoulder_width"] = np.median(
        np.linalg.norm(_m(seq, "LSHO") - _m(seq, "RSHO"), axis=1)
    ) / height
    return f


FEATURE_NAMES = None  # set on first call via build_matrix


def build_matrix(trials):
    """Return (X, names) feature matrix for a list of trials."""
    rows = [extract(t["seq"]) for t in trials]
    names = list(rows[0].keys())
    X = np.array([[r[k] for k in names] for r in rows], dtype=float)
    X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)
    return X, names


if __name__ == "__main__":
    import os
    from data_loader import load_dataset
    here = os.path.dirname(__file__)
    trc = os.path.join(here, "..", "data", "expressive_gait", "MotionCaptureData trc")
    trials = load_dataset(trc)
    X, names = build_matrix(trials)
    print(f"Feature matrix: {X.shape}, {len(names)} features")
    print("features:", names)
    print("example row (", trials[0]["name"], "):")
    for n, v in zip(names, X[0]):
        print(f"  {n:18s} {v: .4f}")
