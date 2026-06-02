"""Run D: Raw markers + MLP (neural network).

Pure black box: feed the standardized 7872-d raw vector straight into a small
neural net. Strong L2 (alpha) is needed because the input dimension dwarfs the
~60 training trials, so overfitting is the main risk.
"""

from sklearn.preprocessing import StandardScaler
from sklearn.neural_network import MLPClassifier

SEED = 0


def run(X_train, y_train, X_test):
    scaler = StandardScaler().fit(X_train)
    clf = MLPClassifier(
        hidden_layer_sizes=(128, 32),
        activation="relu",
        alpha=1e-2,            # strong L2: few samples, high dimension
        max_iter=800,
        random_state=SEED,
    )
    clf.fit(scaler.transform(X_train), y_train)
    return clf.predict(scaler.transform(X_test))
