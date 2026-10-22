"""Coordenadas 2D para el scatter de clusters."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA

from app.core.profiling import purchases_per_year
from app.models import Point2D, ScatterData

MAX_POINTS = 1_500


def build_scatter(
    customers: pd.DataFrame, X: np.ndarray, labels: np.ndarray, period_days: int | None, max_points: int = MAX_POINTS
) -> ScatterData:
    """Transaccional: ejes de negocio (compras al año vs gasto). Si no, PCA de las features."""
    if {"frequency", "monetary"} <= set(customers.columns) and period_days:
        coords = np.c_[purchases_per_year(customers["frequency"], period_days), customers["monetary"]]
        x_label, y_label = "Compras al año", "Gasto total"
    else:
        coords = PCA(n_components=2, random_state=42).fit_transform(X) if X.shape[1] >= 2 else np.c_[X, np.zeros(len(X))]
        x_label, y_label = "Componente 1", "Componente 2"
    return ScatterData(x_label=x_label, y_label=y_label, points=_points(coords, labels, max_points))


def _points(coords: np.ndarray, labels: np.ndarray, max_points: int) -> list[Point2D]:
    refs = np.arange(len(coords))
    if len(coords) > max_points:
        refs = np.sort(np.random.default_rng(42).choice(len(coords), size=max_points, replace=False))
    return [
        Point2D(customer_ref=int(i), x=round(float(coords[i, 0]), 4), y=round(float(coords[i, 1]), 4), cluster_id=int(labels[i]))
        for i in refs
    ]
