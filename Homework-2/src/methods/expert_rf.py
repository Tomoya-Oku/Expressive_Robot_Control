"""Run A: Expert features + RandomForest.

A tree ensemble on the 25 hand-crafted features. Trees handle non-linear
feature interactions and are robust on small, low-dimensional data.
"""

from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier

SEED = 0


def run(X_train, y_train, X_test):
    scaler = StandardScaler().fit(X_train)
    clf = RandomForestClassifier(n_estimators=300, random_state=SEED)
    clf.fit(scaler.transform(X_train), y_train)
    return clf.predict(scaler.transform(X_test))
