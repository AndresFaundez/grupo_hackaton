import numpy as np
import pandas as pd
import pytest
from sklearn.metrics import adjusted_rand_score

from app.agent.llm import FakeLLM
from app.core.clustering import fit_clusters
from app.core.embedding import build_scatter
from app.core.features import build_features, transform
from app.core.naming import label_clusters
from app.core.profiling import profile_clusters, representatives
from app.core.rules import explain_row, fit_rules, rule_text
from app.models import ClusterLabel, ClusterLabelsLLM, Condition


@pytest.fixture(scope="module")
def fitted(synthetic, synthetic_df, synthetic_schema):
    _, truth = synthetic
    fs = build_features(synthetic_df, synthetic_schema)
    t = transform(fs.customers, fs.feature_cols)
    fit = fit_clusters(t.X)
    truth = truth.set_index("rut_cliente").reindex(fs.customers.index)["segmento"]
    return fs, t, fit, truth


def test_recovers_planted_segments(fitted):
    fs, t, fit, truth = fitted
    # Los "ocasionales" de una sola compra pueden separarse en su propio cluster: k = 4 o 5.
    assert fit.k in {4, 5}
    assert adjusted_rand_score(truth, fit.labels) > 0.7
    # Cada segmento plantado cae mayoritariamente (>90%) en un solo cluster.
    for segment in truth.unique():
        counts = np.bincount(fit.labels[(truth == segment).to_numpy()])
        if segment != "ocasionales":
            assert counts.max() / counts.sum() > 0.9, segment


def test_forced_k(fitted):
    _, t, _, _ = fitted
    forced = fit_clusters(t.X, k=6)
    assert forced.k == 6 and len(np.unique(forced.labels)) == 6 and list(forced.k_scores) == [6]


def test_cluster_ids_sorted_by_size(fitted):
    _, _, fit, _ = fitted
    sizes = np.bincount(fit.labels)
    assert list(sizes) == sorted(sizes, reverse=True)


def test_profiles_flag_vip_as_high_value(fitted):
    fs, t, fit, truth = fitted
    profiles = profile_clusters(fs.customers, t.T, fit.labels, fs.feature_cols, fs.attribute_cols, fs.monetary_col)
    assert sum(p.size for p in profiles) == len(fs.customers)
    assert sum(p.revenue_share for p in profiles) == pytest.approx(1, abs=1e-3)
    vip_cluster = truth[truth == "vip"].index
    vip_id = int(np.bincount(fit.labels[fs.customers.index.isin(vip_cluster)]).argmax())
    vip = next(p for p in profiles if p.cluster_id == vip_id)
    assert vip.revenue_share / vip.share > 3
    assert any(trait.startswith("monetary alto") for trait in vip.top_traits)


def test_rules_are_faithful_and_readable(fitted):
    fs, _, fit, _ = fitted
    rs = fit_rules(fs.customers[fs.feature_cols], fit.labels)
    assert rs.fidelity > 0.8
    assert set(rs.rules) == set(np.unique(fit.labels))
    for rules in rs.rules.values():
        assert all(r.precision >= 0.5 and 0 < r.coverage <= 1 for r in rules)

    predicted, steps = explain_row(rs, fs.customers.iloc[0])
    assert predicted in rs.rules and steps and "valor:" in steps[0]


def test_rule_text_ranges_integers_and_one_hot():
    conds = [
        Condition(feature="recency_days", op=">", threshold=30.5),
        Condition(feature="recency_days", op="<=", threshold=90.5),
        Condition(feature="gender=F", op=">", threshold=0.5),
        Condition(feature="monetary", op="<=", threshold=1234.5),
    ]
    assert rule_text(conds, {"recency_days"}) == "30 < recency_days ≤ 90 Y gender = F Y monetary ≤ 1,234"


def test_scatter_uses_business_axes_for_transactional(fitted):
    fs, t, fit, _ = fitted
    scatter = build_scatter(fs.customers, t.X, fit.labels, fs.period_days, max_points=200)
    assert (scatter.x_label, scatter.y_label) == ("Compras al año", "Gasto total")
    assert len(scatter.points) == 200 and len({p.customer_ref for p in scatter.points}) == 200
    point = scatter.points[0]
    row = fs.customers.iloc[point.customer_ref]
    assert point.y == pytest.approx(row["monetary"])


def test_scatter_falls_back_to_pca():
    X = np.random.default_rng(0).normal(size=(50, 3))
    customers = pd.DataFrame(X, columns=["a", "b", "c"])
    scatter = build_scatter(customers, X, np.zeros(50, dtype=int), None, max_points=20)
    assert scatter.x_label == "Componente 1" and len(scatter.points) == 20


def test_metrics_products_and_representative(fitted):
    fs, t, fit, _ = fitted
    profiles = profile_clusters(fs.customers, t.T, fit.labels, fs.feature_cols, fs.attribute_cols, fs.monetary_col,
                                period_days=fs.period_days, category_spend=fs.category_spend)
    p = profiles[0]
    members = fs.customers[fit.labels == 0]
    assert p.metrics.avg_spend == pytest.approx(members["monetary"].mean(), rel=1e-4)
    assert p.metrics.revenue == pytest.approx(members["monetary"].sum(), rel=1e-4)
    assert p.metrics.purchases_per_year == pytest.approx(members["frequency"].mean() * 365 / fs.period_days, abs=0.01)
    assert 1 <= len(p.top_products) <= 5
    assert sum(x.share for x in p.top_products) <= 1 + 1e-6
    # Los cazadores de ofertas concentran su gasto en "Ofertas".
    offers = [next((x.share for x in pr.top_products if x.name == "Ofertas"), 0) for pr in profiles]
    assert max(offers) > 0.5

    customers = fs.customers.rename_axis("customer_id").reset_index().rename_axis("customer_ref")
    pii = fs.pii.reset_index(drop=True).rename_axis("customer_ref")
    reps = representatives(t.X, fit.labels, customers, pii, "nombre_cliente", ["monetary", "comuna"])
    assert set(reps) == set(np.unique(fit.labels))
    rep = reps[0]
    assert fit.labels[rep.customer_ref] == 0 and rep.name and set(rep.features) == {"monetary", "comuna"}


def test_naming_with_llm_and_fallbacks(fitted):
    fs, t, fit, _ = fitted
    profiles = profile_clusters(fs.customers, t.T, fit.labels, fs.feature_cols, fs.attribute_cols, fs.monetary_col)

    labels, source = label_clusters(profiles, {}, fs.descriptions, None)
    assert source == "fallback" and labels[0].name == "Cluster 1"
    assert all(label.tags and len(label.strategies) == 3 for label in labels)
    # El cluster de mayor recencia (inactivos) se sugiere reactivar.
    inactive = max(profiles, key=lambda p: next(f.z for f in p.features if f.feature == "recency_days"))
    assert next(l for l in labels if l.cluster_id == inactive.cluster_id).suggested_objective == "reactivar"

    def fake(prompt: str) -> ClusterLabelsLLM:
        assert "@" not in prompt  # nada de emails ni datos personales en el prompt
        return ClusterLabelsLLM(clusters=[
            ClusterLabel(cluster_id=p.cluster_id, name=f"Segmento {p.cluster_id}", description="d", persona="p",
                         tags=["a"], key_traits=["t"], value_level="medio", suggested_objective="fidelizar",
                         strategies=["s"], suggested_questions=["q"])
            for p in profiles
        ])

    labels, source = label_clusters(profiles, {}, fs.descriptions, FakeLLM({ClusterLabelsLLM: fake}))
    assert source == "llm" and [label.name for label in labels] == [f"Segmento {p.cluster_id}" for p in profiles]

    duplicated = ClusterLabelsLLM(clusters=[
        ClusterLabel(cluster_id=p.cluster_id, name="Igual", description="d", persona="p", tags=[],
                     key_traits=[], value_level="bajo", suggested_objective="ticket", strategies=[],
                     suggested_questions=[]) for p in profiles
    ])
    _, source = label_clusters(profiles, {}, fs.descriptions, FakeLLM({ClusterLabelsLLM: duplicated}))
    assert source == "fallback"
