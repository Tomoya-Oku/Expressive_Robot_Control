"""Run E: Raw markers -> Autoencoder(16) + LogisticRegression.

A nonlinear autoencoder learns a 16-d code that can reconstruct the raw vector
(unsupervised). That code is then classified by the *same* LogisticRegression as
the expert-feature run (expert_logreg.py), so the comparison reflects only the
feature source: hand-crafted vs. learned.
"""

import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPRegressor

SEED = 0


def _ae_encode(X_train, X_test, bottleneck=16, seed=SEED):
    """Train an MLP autoencoder (in -> 64 -> bottleneck -> 64 -> in) and return
    the bottleneck activations for train/test."""
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


def run(X_train, y_train, X_test):
    scaler = StandardScaler().fit(X_train)
    Ztr, Zte = _ae_encode(scaler.transform(X_train), scaler.transform(X_test))
    scaler2 = StandardScaler().fit(Ztr)
    clf = LogisticRegression(max_iter=2000, C=1.0)
    clf.fit(scaler2.transform(Ztr), y_train)
    return clf.predict(scaler2.transform(Zte))
