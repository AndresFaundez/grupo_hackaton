"""Estadísticas por cluster: qué lo distingue del promedio."""

from __future__ import annotations

import numpy as np
import pandas as pd

from app.models import ClusterProfile, FeatureStat

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
) -> list[ClusterProfile]:
    n = len(customers)
    global_mean = customers[feature_cols].mean()
    t_mean, t_std = T.mean(), T.std(ddof=0).replace(0, 1.0)
    total_revenue = float(customers[monetary_col].sum()) if monetary_col else None

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
                features=stats,
                top_traits=traits,
                categorical=categorical,
            )
        )
    return profiles
