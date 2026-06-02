"""
Classification methods, one module per method.

Every module exposes a single function

    run(X_train, y_train, X_test) -> predictions

that fits on the training fold and predicts the test fold. Keeping each method
in its own file makes them easy to read, swap, and reuse.

  expert_rf      Run A  Expert features      + RandomForest
  expert_logreg  Run B  Expert features      + LogisticRegression
  pca_knn        Run C  Raw -> PCA           + KNN
  raw_mlp        Run D  Raw                  + MLP (neural network)
  ae_logreg      Run E  Raw -> Autoencoder   + LogisticRegression
"""

from .expert_rf import run as expert_rf
from .expert_logreg import run as expert_logreg
from .pca_knn import run as pca_knn
from .raw_mlp import run as raw_mlp
from .ae_logreg import run as ae_logreg

__all__ = ["expert_rf", "expert_logreg", "pca_knn", "raw_mlp", "ae_logreg"]
