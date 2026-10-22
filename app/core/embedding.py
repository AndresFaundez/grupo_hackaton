"""Coordenadas 2D para el scatter de clusters."""

from __future__ import annotations

import numpy as np
from sklearn.decomposition import PCA

from app.models import Point2D

MAX_POINTS = 5_000


def embed_2d(X: np.ndarray, labels: np.ndarray, max_points: int = MAX_POINTS) -> list[Point2D]:
    coords = PCA(n_components=2, random_state=42).fit_transform(X) if X.shape[1] >= 2 else np.c_[X, np.zeros(len(X))]
    refs = np.arange(len(X))
    if len(X) > max_points:
        refs = np.sort(np.random.default_rng(42).choice(len(X), size=max_points, replace=False))
    return [
        Point2D(customer_ref=int(i), x=round(float(coords[i, 0]), 4), y=round(float(coords[i, 1]), 4), cluster_id=int(labels[i]))
        for i in refs
    ]
