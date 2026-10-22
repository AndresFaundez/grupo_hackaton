"""KMeans con k elegido por silhouette."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

RANDOM_STATE = 42
SILHOUETTE_SAMPLE = 10_000


@dataclass
class ClusterFit:
    labels: np.ndarray
    k: int
    silhouette: float
    k_scores: dict[int, float]


def fit_clusters(X: np.ndarray, k: int | None = None, k_min: int = 3, k_max: int = 8) -> ClusterFit:
    n = len(X)
    candidates = [k] if k else list(range(k_min, min(k_max, n - 1) + 1))
    if not candidates or candidates[0] < 2:
        raise ValueError("No hay suficientes clientes para el rango de k pedido")

    scores: dict[int, float] = {}
    fits: dict[int, np.ndarray] = {}
    for kk in candidates:
        labels = KMeans(n_clusters=kk, n_init=10, random_state=RANDOM_STATE).fit_predict(X)
        scores[kk] = float(
            silhouette_score(X, labels, sample_size=min(SILHOUETTE_SAMPLE, n), random_state=RANDOM_STATE)
        )
        fits[kk] = labels

    best = max(scores, key=scores.get)
    return ClusterFit(labels=_relabel_by_size(fits[best]), k=best, silhouette=scores[best], k_scores=scores)


def _relabel_by_size(labels: np.ndarray) -> np.ndarray:
    """Cluster 0 = el más grande, para que los IDs sean estables entre corridas."""
    ids, counts = np.unique(labels, return_counts=True)
    order = ids[np.argsort(-counts, kind="stable")]
    mapping = {old: new for new, old in enumerate(order)}
    return np.array([mapping[label] for label in labels])
