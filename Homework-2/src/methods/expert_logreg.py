"""Run B: Expert features + LogisticRegression.

A linear model on the 25 hand-crafted features. Used as the *shared* downstream
classifier for the hand-crafted-vs-autoencoder comparison (see ae_logreg.py):
fixing the classifier isolates the effect of the feature source.
"""

from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression


def run(X_train, y_train, X_test):
    scaler = StandardScaler().fit(X_train)
    clf = LogisticRegression(max_iter=2000, C=1.0)
    clf.fit(scaler.transform(X_train), y_train)
    return clf.predict(scaler.transform(X_test))
