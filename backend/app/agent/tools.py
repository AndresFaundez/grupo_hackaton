"""Herramientas que el agente puede llamar. Todas devuelven agregados o datos sin PII."""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from typing import Any

import pandas as pd

from app.agent.llm import ToolSpec
from app.agent.sandbox import SqlRejected
from app.core.rules import explain_row
from app.models import Attachment
from app.store import ClusteringRecord, Store

log = logging.getLogger(__name__)

PREVIEW_ROWS = 5

TOOL_SPECS: dict[str, ToolSpec] = {
    spec.name: spec
    for spec in [
        ToolSpec(
            name="describe_cluster",
            description="Perfil completo de un cluster: nombre, tamaño, % de ingresos, estadísticas por feature "
            "(media, mediana, media global, z), distribución de categorías y reglas que lo delimitan.",
            parameters={
                "type": "object",
                "properties": {"cluster_id": {"type": "integer", "description": "ID numérico del cluster"}},
                "required": ["cluster_id"],
            },
        ),
        ToolSpec(
            name="compare_clusters",
            description="Compara dos clusters y devuelve sus diferencias principales ordenadas por magnitud.",
            parameters={
                "type": "object",
                "properties": {
                    "cluster_a": {"type": "integer"},
                    "cluster_b": {"type": "integer"},
                },
                "required": ["cluster_a", "cluster_b"],
            },
        ),
        ToolSpec(
            name="query_data",
            description="Ejecuta una consulta SQL de solo lectura (dialecto DuckDB) sobre las tablas `customers` y "
            "`clusters`. Devuelve como máximo 50 filas; prefiere agregaciones (COUNT, AVG, SUM, GROUP BY).",
            parameters={
                "type": "object",
                "properties": {"sql": {"type": "string", "description": "Una única sentencia SELECT"}},
                "required": ["sql"],
            },
        ),
        ToolSpec(
            name="explain_customer",
            description="Explica por qué un cliente quedó en su cluster: sus features vs. la media del cluster y "
            "el camino de reglas que cumple. Recibe el ID del cliente tal como lo escribe el usuario.",
            parameters={
                "type": "object",
                "properties": {"customer_id": {"type": "string"}},
                "required": ["customer_id"],
            },
        ),
        ToolSpec(
            name="list_customers",
            description="Arma una lista de clientes de un cluster (opcionalmente filtrada) para que el usuario la "
            "vea o descargue. Tú solo recibes el conteo; los datos personales van directo al usuario.",
            parameters={
                "type": "object",
                "properties": {
                    "cluster_id": {"type": "integer"},
                    "where": {"type": "string", "description": "Condición SQL opcional sobre columnas de customers, ej: recency_days > 60"},
                    "order_by": {"type": "string", "description": "Orden opcional, ej: monetary DESC"},
                    "limit": {"type": "integer", "description": "Máximo de clientes, opcional"},
                    "title": {"type": "string", "description": "Título corto para la lista"},
                },
                "required": ["cluster_id"],
            },
        ),
    ]
}


@dataclass
class ToolOutcome:
    response: dict[str, Any]
    preview: Any = None
    attachment: Attachment | None = None
    error: str | None = None


class ToolError(ValueError):
    pass


def execute_tool(name: str, args: dict[str, Any], record: ClusteringRecord, store: Store) -> ToolOutcome:
    handler = HANDLERS.get(name)
    if handler is None:
        return _error(f"Herramienta desconocida: {name}")
    try:
        return handler(args, record, store)
    except (ToolError, SqlRejected, KeyError, TypeError, ValueError) as e:
        return _error(str(e))
    except Exception as e:
        log.exception("Error inesperado en la herramienta %s", name)
        return _error(f"Error interno: {e}")


def _error(message: str) -> ToolOutcome:
    return ToolOutcome(response={"error": message}, preview=None, error=message)


def _cluster(record: ClusteringRecord, cluster_id: Any):
    summary = record.result.cluster(int(cluster_id))
    if summary is None:
        valid = [c.profile.cluster_id for c in record.result.clusters]
        raise ToolError(f"No existe el cluster {cluster_id}. Clusters válidos: {valid}")
    return summary


def describe_cluster(args: dict, record: ClusteringRecord, store: Store) -> ToolOutcome:
    s = _cluster(record, args["cluster_id"])
    descriptions = record.result.feature_descriptions
    response = {
        "cluster_id": s.profile.cluster_id,
        "name": s.label.name,
        "description": s.label.description,
        "persona": s.label.persona,
        "value_level": s.label.value_level,
        "size": s.profile.size,
        "share_of_customers": s.profile.share,
        "share_of_revenue": s.profile.revenue_share,
        "features": [
            {"feature": f.feature, "meaning": descriptions.get(f.feature), "mean": f.mean, "median": f.median,
             "global_mean": f.global_mean, "z": f.z}
            for f in s.profile.features
        ],
        "top_traits": s.profile.top_traits,
        "categorical": s.profile.categorical,
        "rules": [{"text": r.text, "precision": r.precision, "coverage": r.coverage} for r in s.rules],
    }
    return ToolOutcome(response=response, preview={"name": s.label.name, "size": s.profile.size})


def compare_clusters(args: dict, record: ClusteringRecord, store: Store) -> ToolOutcome:
    a, b = _cluster(record, args["cluster_a"]), _cluster(record, args["cluster_b"])
    stats_b = {f.feature: f for f in b.profile.features}
    differences = sorted(
        (
            {"feature": fa.feature, "mean_a": fa.mean, "mean_b": stats_b[fa.feature].mean,
             "z_a": fa.z, "z_b": stats_b[fa.feature].z, "z_diff": round(fa.z - stats_b[fa.feature].z, 3)}
            for fa in a.profile.features
        ),
        key=lambda d: abs(d["z_diff"]),
        reverse=True,
    )

    def head(s):
        return {"cluster_id": s.profile.cluster_id, "name": s.label.name, "size": s.profile.size,
                "share_of_customers": s.profile.share, "share_of_revenue": s.profile.revenue_share}

    categorical = {
        col: {"a": a.profile.categorical.get(col, {}), "b": b.profile.categorical.get(col, {})}
        for col in a.profile.categorical
    }
    response = {"a": head(a), "b": head(b), "differences": differences[:8], "categorical": categorical}
    return ToolOutcome(response=response, preview={"top_difference": differences[0]["feature"] if differences else None})


def query_data(args: dict, record: ClusteringRecord, store: Store) -> ToolOutcome:
    result = record.sandbox.query(str(args["sql"]))
    response = {"sql": result.sql, "columns": result.columns, "rows": result.rows, "truncated": result.truncated}
    attachment = Attachment(type="table", title="Resultado de la consulta", columns=result.columns, rows=result.rows)
    preview = {"sql": result.sql, "columns": result.columns, "rows": result.rows[:PREVIEW_ROWS], "truncated": result.truncated}
    return ToolOutcome(response=response, preview=preview, attachment=attachment)


def _normalize_id(value: Any) -> str:
    return re.sub(r"[\s.]", "", str(value)).lower()


def explain_customer(args: dict, record: ClusteringRecord, store: Store) -> ToolOutcome:
    wanted = _normalize_id(args["customer_id"])
    customers = record.customers
    matches = customers.index[customers["customer_id"].map(_normalize_id) == wanted]
    if len(matches) == 0:
        raise ToolError(f"No encontré al cliente '{args['customer_id']}'")
    ref = int(matches[0])
    row = customers.loc[ref]
    summary = _cluster(record, row["cluster_id"])
    means = {f.feature: f for f in summary.profile.features}
    predicted, path = explain_row(record.rule_set, row)
    response = {
        "customer_ref": ref,
        "cluster_id": summary.profile.cluster_id,
        "cluster_name": summary.label.name,
        "features": [
            {"feature": f, "value": round(float(row[f]), 4), "cluster_mean": means[f].mean, "global_mean": means[f].global_mean}
            for f in record.rule_set.feature_names
        ],
        "decision_path": path,
        "rules_predict_same_cluster": predicted == summary.profile.cluster_id,
    }
    return ToolOutcome(response=response, preview={"customer_ref": ref, "cluster": summary.label.name})


def list_customers(args: dict, record: ClusteringRecord, store: Store) -> ToolOutcome:
    summary = _cluster(record, args["cluster_id"])
    sql = f"SELECT customer_ref FROM customers WHERE cluster_id = {summary.profile.cluster_id}"
    if args.get("where"):
        sql += f" AND ({args['where']})"
    if args.get("order_by"):
        sql += f" ORDER BY {args['order_by']}"
    if args.get("limit"):
        sql += f" LIMIT {int(args['limit'])}"
    result = record.sandbox.query(sql, limit=False)
    refs = [int(r[0]) for r in result.rows]

    full = record.customers.loc[refs].join(record.pii, how="left")
    full.insert(0, "customer_ref", full.index)
    handle = store.add_result(full.reset_index(drop=True))
    title = args.get("title") or f"Clientes de {summary.label.name}"
    response = {
        "handle": handle,
        "count": len(refs),
        "title": title,
        "note": "La lista ya se muestra al usuario con sus datos de contacto; tú no los ves.",
    }
    attachment = Attachment(type="customer_list", title=title, handle=handle, count=len(refs), columns=list(full.columns))
    return ToolOutcome(response=response, preview={"count": len(refs), "sql": result.sql}, attachment=attachment)


HANDLERS = {
    "describe_cluster": describe_cluster,
    "compare_clusters": compare_clusters,
    "query_data": query_data,
    "explain_customer": explain_customer,
    "list_customers": list_customers,
}


def dataframe_payload(df: pd.DataFrame) -> dict[str, Any]:
    """Serializa una lista de clientes para la API."""
    split = json.loads(df.to_json(orient="split", index=False, date_format="iso"))
    return {"count": len(df), "columns": split["columns"], "rows": split["data"]}
