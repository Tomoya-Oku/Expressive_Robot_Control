"""Run C: Raw markers -> PCA(20) + KNN.

Classic black-box baseline: linearly compress the 7872-d raw vector to 20
principal components, then classify by the majority label of the 5 nearest
neighbors. PCA tames the curse of dimensionality before KNN.
"""

from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.neighbors import KNeighborsClassifier

SEED = 0


def run(X_train, y_train, X_test):
    scaler = StandardScaler().fit(X_train)
    Xtr = scaler.transform(X_train)
    Xte = scaler.transform(X_test)
    pca = PCA(n_components=20, random_state=SEED).fit(Xtr)
    knn = KNeighborsClassifier(n_neighbors=5)
    knn.fit(pca.transform(Xtr), y_train)
    return knn.predict(pca.transform(Xte))
