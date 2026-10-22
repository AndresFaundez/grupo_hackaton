"""Orquestación: subir dataset -> schema -> features -> clustering -> perfiles/reglas/nombres -> sandbox."""

from __future__ import annotations

import pandas as pd

from app.agent.llm import LLM
from app.agent.sandbox import Sandbox
from app.config import Settings
from app.core.clustering import fit_clusters
from app.core.embedding import embed_2d
from app.core.features import build_features, transform
from app.core.ingest import preview_rows, profile_columns, read_table
from app.core.naming import label_clusters
from app.core.profiling import profile_clusters
from app.core.rules import fit_rules
from app.core.schema import detect_schema
from app.models import ClusteringRequest, ClusteringResult, ClusterSummary, DatasetInfo
from app.store import ClusteringRecord, DatasetRecord, Store, new_id


def ingest_dataset(content: bytes, filename: str, llm: LLM | None, store: Store) -> DatasetRecord:
    try:
        df = read_table(content, filename)
    except Exception as e:
        raise ValueError(f"No se pudo leer el archivo: {e}") from e
    if df.empty or len(df.columns) < 2:
        raise ValueError("El archivo está vacío o tiene menos de 2 columnas")

    profiles = profile_columns(df)
    schema = detect_schema(profiles, len(df), llm)
    info = DatasetInfo(
        dataset_id=new_id("ds"),
        filename=filename,
        n_rows=len(df),
        columns=profiles,
        proposed_schema=schema,
        preview=preview_rows(df),
    )
    record = DatasetRecord(info=info, df=df)
    store.add_dataset(record)
    return record


def run_clustering(
    dataset: DatasetRecord, req: ClusteringRequest, llm: LLM | None, settings: Settings, store: Store
) -> ClusteringRecord:
    schema = dataset.info.schema_in_use
    fs = build_features(dataset.df, schema)

    feature_cols = fs.feature_cols
    if req.features:
        unknown = set(req.features) - set(fs.feature_cols)
        if unknown:
            raise ValueError(f"Features desconocidas: {sorted(unknown)}. Disponibles: {fs.feature_cols}")
        feature_cols = [c for c in fs.feature_cols if c in req.features]

    transformed = transform(fs.customers, feature_cols)
    fit = fit_clusters(transformed.X, k=req.k, k_min=settings.k_min, k_max=settings.k_max)
    profiles = profile_clusters(fs.customers, transformed.T, fit.labels, feature_cols, fs.attribute_cols, fs.monetary_col)
    rule_set = fit_rules(fs.customers[feature_cols], fit.labels)
    descriptions = {c: fs.descriptions[c] for c in feature_cols + fs.attribute_cols if c in fs.descriptions}
    labels, labels_source = label_clusters(profiles, rule_set.rules, descriptions, llm)

    # customer_ref = posición 0..n-1: es la clave anónima que ve el LLM.
    customers = fs.customers.rename_axis("customer_id").reset_index().rename_axis("customer_ref")
    customers["cluster_id"] = fit.labels
    pii = fs.pii.reset_index(drop=True).rename_axis("customer_ref")

    names = {label.cluster_id: label.name for label in labels}
    sandbox_columns = [c for c in fs.customers.columns if "=" not in c]  # sin one-hot: las categóricas van crudas
    safe = customers[sandbox_columns].copy()
    safe.insert(0, "customer_ref", safe.index)
    safe.insert(1, "cluster_id", fit.labels)
    safe.insert(2, "cluster_name", safe["cluster_id"].map(names))
    clusters_table = pd.DataFrame(
        [
            {"cluster_id": p.cluster_id, "name": label.name, "size": p.size, "share": p.share,
             "revenue_share": p.revenue_share, "value_level": label.value_level, "description": label.description}
            for p, label in zip(profiles, labels)
        ]
    )
    sandbox = Sandbox(safe.reset_index(drop=True), clusters_table, max_rows=settings.max_query_rows)

    all_descriptions = {c: d for c, d in fs.descriptions.items() if "=" not in c}
    result = ClusteringResult(
        clustering_id=new_id("cl"),
        dataset_id=dataset.info.dataset_id,
        data_shape=schema.data_shape,
        n_customers=len(customers),
        k=fit.k,
        silhouette=round(fit.silhouette, 4),
        k_scores={k: round(v, 4) for k, v in fit.k_scores.items()},
        features=feature_cols,
        feature_descriptions=all_descriptions | descriptions,
        rules_fidelity=rule_set.fidelity,
        labels_source=labels_source,
        clusters=[
            ClusterSummary(profile=p, rules=rule_set.rules.get(p.cluster_id, []), label=label)
            for p, label in zip(profiles, labels)
        ],
        embedding=embed_2d(transformed.X, fit.labels),
    )
    record = ClusteringRecord(result=result, customers=customers, pii=pii, rule_set=rule_set, sandbox=sandbox)
    store.add_clustering(record)
    return record
