"""Estadísticas por cluster: qué lo distingue del promedio, métricas de negocio y cliente representativo."""

from __future__ import annotations

import numpy as np
import pandas as pd

from app.models import ClusterMetrics, ClusterProfile, FeatureStat, ProductShare, RepresentativeCustomer

TOP_TRAITS = 4
MIN_TRAIT_Z = 0.3
TOP_CATEGORIES = 5


def profile_clusters(
    customers: pd.DataFrame,
    T: pd.DataFrame,
    labels: np.ndarray,
    feature_cols: list[str],
    attribute_cols: list[str],
    monetary_col: str | None,
    period_days: int | None = None,
    category_spend: pd.Series | None = None,
) -> list[ClusterProfile]:
    n = len(customers)
    global_mean = customers[feature_cols].mean()
    t_mean, t_std = T.mean(), T.std(ddof=0).replace(0, 1.0)
    total_revenue = float(customers[monetary_col].sum()) if monetary_col else None
    products = _top_products(customers, labels, category_spend)

    profiles = []
    for cluster_id in sorted(np.unique(labels)):
        mask = labels == cluster_id
        members = customers[mask]
        z = (T[mask].mean() - t_mean) / t_std

        stats = [
            FeatureStat(
                feature=col,
                mean=round(float(members[col].mean()), 4),
                median=round(float(members[col].median()), 4),
                global_mean=round(float(global_mean[col]), 4),
                z=round(float(z[col]), 3),
            )
            for col in feature_cols
        ]
        ranked = sorted(stats, key=lambda s: abs(s.z), reverse=True)
        traits = [
            f"{s.feature} {'alto' if s.z > 0 else 'bajo'} ({s.z:+.1f}σ; media {s.mean:,.1f} vs {s.global_mean:,.1f})"
            for s in ranked[:TOP_TRAITS]
            if abs(s.z) >= MIN_TRAIT_Z
        ]

        categorical = {
            col: {str(k): round(float(v), 3) for k, v in members[col].value_counts(normalize=True).head(TOP_CATEGORIES).items()}
            for col in attribute_cols
        }
        revenue_share = (
            round(float(members[monetary_col].sum()) / total_revenue, 4) if monetary_col and total_revenue else None
        )
        profiles.append(
            ClusterProfile(
                cluster_id=int(cluster_id),
                size=int(mask.sum()),
                share=round(float(mask.sum()) / n, 4),
                revenue_share=revenue_share,
                metrics=_metrics(members, monetary_col, period_days),
                top_products=products.get(int(cluster_id), []),
                features=stats,
                top_traits=traits,
                categorical=categorical,
            )
        )
    return profiles


def purchases_per_year(frequency: pd.Series, period_days: int) -> pd.Series:
    return frequency * 365.0 / period_days


def _metrics(members: pd.DataFrame, monetary_col: str | None, period_days: int | None) -> ClusterMetrics:
    def mean(col: str | None) -> float | None:
        return round(float(members[col].mean()), 2) if col and col in members else None

    per_year = None
    if "frequency" in members and period_days:
        per_year = round(float(purchases_per_year(members["frequency"], period_days).mean()), 2)
    return ClusterMetrics(
        avg_spend=mean(monetary_col),
        avg_ticket=mean("avg_ticket"),
        purchases_per_year=per_year,
        days_since_last_purchase=mean("recency_days"),
        revenue=round(float(members[monetary_col].sum()), 2) if monetary_col else None,
    )


def _top_products(customers: pd.DataFrame, labels: np.ndarray, category_spend: pd.Series | None) -> dict[int, list[ProductShare]]:
    if category_spend is None or category_spend.empty:
        return {}
    cluster_of = pd.Series(labels, index=customers.index)
    spend = category_spend.reset_index(name="amount")
    spend["cluster_id"] = spend["customer_id"].map(cluster_of)
    by_cluster = spend.dropna(subset=["cluster_id"]).groupby(["cluster_id", "category"])["amount"].sum()
    result = {}
    for cluster_id, group in by_cluster.groupby(level=0):
        shares = (group / group.sum()).droplevel(0).sort_values(ascending=False).head(TOP_CATEGORIES)
        result[int(cluster_id)] = [ProductShare(name=str(k), share=round(float(v), 3)) for k, v in shares.items()]
    return result


def representatives(
    X: np.ndarray,
    labels: np.ndarray,
    customers: pd.DataFrame,
    pii: pd.DataFrame,
    name_column: str | None,
    display_cols: list[str],
) -> dict[int, RepresentativeCustomer]:
    """Por cluster, el cliente más cercano a su centroide. `customers` y `pii` indexados por customer_ref."""
    result = {}
    for cluster_id in np.unique(labels):
        positions = np.flatnonzero(labels == cluster_id)
        centroid = X[positions].mean(axis=0)
        ref = int(positions[np.argmin(np.linalg.norm(X[positions] - centroid, axis=1))])
        row = customers.loc[ref]
        name = None
        if name_column and name_column in pii.columns and pd.notna(pii.loc[ref, name_column]):
            name = str(pii.loc[ref, name_column])
        features = {
            col: (round(float(row[col]), 2) if isinstance(row[col], (int, float, np.number)) else str(row[col]))
            for col in display_cols
        }
        result[int(cluster_id)] = RepresentativeCustomer(
            customer_ref=ref, customer_id=str(row["customer_id"]), name=name, features=features
        )
    return result
