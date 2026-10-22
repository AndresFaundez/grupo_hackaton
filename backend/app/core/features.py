"""Construcción de features por cliente y transformación para el clustering."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

from app.core.ingest import slugify
from app.models import SchemaMapping

TRANSACTIONAL_DESCRIPTIONS = {
    "recency_days": "Días desde la última compra (menor = compró hace poco)",
    "frequency": "Número de compras distintas",
    "monetary": "Gasto total del cliente",
    "avg_ticket": "Gasto promedio por compra",
    "tenure_days": "Días desde la primera compra (antigüedad)",
    "n_categories": "Número de categorías distintas compradas",
    "top_category_share": "Proporción del gasto en su categoría favorita (1 = compra una sola categoría)",
    "top_category": "Categoría donde más gasta",
}
LOG_FEATURES = {"frequency", "monetary", "avg_ticket"}
MAX_ONE_HOT = 8


@dataclass
class FeatureSet:
    # Una fila por cliente (index = customer_id original). Features en unidades originales
    # + atributos categóricos descriptivos (no se usan para clusterizar en transaccional).
    customers: pd.DataFrame
    feature_cols: list[str]
    attribute_cols: list[str]
    descriptions: dict[str, str]
    monetary_col: str | None
    pii: pd.DataFrame = field(default_factory=pd.DataFrame)
    # Solo transaccional: días cubiertos por los datos y gasto por (cliente, categoría).
    period_days: int | None = None
    category_spend: pd.Series | None = None


@dataclass
class Transformed:
    T: pd.DataFrame  # log + recorte, sin escalar (para z-scores de perfiles)
    X: np.ndarray  # entrada del modelo


def build_features(df: pd.DataFrame, schema: SchemaMapping) -> FeatureSet:
    if schema.customer_id not in df.columns:
        raise ValueError(f"La columna de cliente '{schema.customer_id}' no existe")
    df = df.dropna(subset=[schema.customer_id]).copy()
    df[schema.customer_id] = df[schema.customer_id].astype(str).str.strip()

    if schema.data_shape == "transactional":
        fs = _transactional(df, schema)
    else:
        fs = _customer_level(df, schema)

    pii_cols = [c for c in schema.pii_columns if c in df.columns and c != schema.customer_id]
    fs.pii = df.groupby(schema.customer_id)[pii_cols].first().reindex(fs.customers.index) if pii_cols else pd.DataFrame(index=fs.customers.index)
    if len(fs.customers) < 10:
        raise ValueError(f"Se necesitan al menos 10 clientes para segmentar (hay {len(fs.customers)})")
    return fs


def _transactional(df: pd.DataFrame, schema: SchemaMapping) -> FeatureSet:
    cid, date = schema.customer_id, schema.date
    if not date or date not in df.columns:
        raise ValueError("Datos transaccionales requieren una columna de fecha")
    df[date] = pd.to_datetime(df[date], errors="coerce")

    if schema.amount:
        df["_amount"] = pd.to_numeric(df[schema.amount], errors="coerce")
    elif schema.quantity and schema.unit_price:
        df["_amount"] = pd.to_numeric(df[schema.quantity], errors="coerce") * pd.to_numeric(df[schema.unit_price], errors="coerce")
    else:
        raise ValueError("Datos transaccionales requieren monto, o cantidad y precio unitario")

    # Devoluciones (montos negativos) y filas incompletas quedan fuera.
    df = df[df["_amount"] > 0].dropna(subset=[date])
    if df.empty:
        raise ValueError("No quedan compras con monto positivo y fecha válida")

    if schema.invoice_id and schema.invoice_id in df.columns:
        df["_order"] = df[schema.invoice_id].astype(str)
    else:
        df["_order"] = df[date].dt.normalize().astype(str)

    ref_date = df[date].max() + pd.Timedelta(days=1)
    period_days = max((df[date].max() - df[date].min()).days + 1, 1)
    orders = df.groupby([cid, "_order"]).agg(amount=("_amount", "sum"), date=(date, "max")).reset_index()
    g = orders.groupby(cid)
    customers = pd.DataFrame(
        {
            "recency_days": (ref_date - g["date"].max()).dt.days,
            "frequency": g["_order"].nunique(),
            "monetary": g["amount"].sum(),
            "tenure_days": (ref_date - g["date"].min()).dt.days,
        }
    )
    customers["avg_ticket"] = customers["monetary"] / customers["frequency"]

    feature_cols = ["recency_days", "frequency", "monetary", "avg_ticket", "tenure_days"]
    attribute_cols: list[str] = []
    descriptions = {k: v for k, v in TRANSACTIONAL_DESCRIPTIONS.items()}
    category_spend = None

    if schema.category and schema.category in df.columns:
        by_cat = df.groupby([cid, schema.category])["_amount"].sum()
        category_spend = by_cat.rename_axis(["customer_id", "category"])
        totals = by_cat.groupby(level=0).sum()
        customers["n_categories"] = by_cat.groupby(level=0).size()
        customers["top_category_share"] = by_cat.groupby(level=0).max() / totals
        customers["top_category"] = by_cat.groupby(level=0).idxmax().map(lambda t: str(t[1]))
        feature_cols += ["n_categories", "top_category_share"]
        attribute_cols.append("top_category")

    # Categóricas constantes por cliente (país, comuna...) se agregan como atributos descriptivos.
    skip = {cid, date, schema.category, schema.invoice_id, schema.amount, schema.quantity, schema.unit_price}
    skip |= set(schema.pii_columns)
    for spec in schema.columns:
        if spec.semantic_type != "categorical" or spec.name in skip or spec.name not in df.columns:
            continue
        per_customer = df.groupby(cid)[spec.name].nunique()
        if (per_customer <= 1).mean() >= 0.95:
            slug = slugify(spec.name)
            customers[slug] = df.groupby(cid)[spec.name].agg(lambda s: s.mode().iat[0] if not s.mode().empty else None).astype(str)
            attribute_cols.append(slug)
            descriptions[slug] = spec.description or f"Columna original '{spec.name}'"

    return FeatureSet(
        customers=customers,
        feature_cols=feature_cols,
        attribute_cols=attribute_cols,
        descriptions={c: descriptions[c] for c in feature_cols + attribute_cols},
        monetary_col="monetary",
        period_days=period_days,
        category_spend=category_spend,
    )


def _customer_level(df: pd.DataFrame, schema: SchemaMapping) -> FeatureSet:
    cid = schema.customer_id
    df = df.drop_duplicates(subset=[cid]).set_index(cid)
    customers = pd.DataFrame(index=df.index)
    feature_cols: list[str] = []
    attribute_cols: list[str] = []
    descriptions: dict[str, str] = {}
    monetary_col = None

    for spec in schema.columns:
        if spec.name == cid or spec.name not in df.columns or spec.name in schema.pii_columns:
            continue
        slug = slugify(spec.name)
        description = spec.description or f"Columna original '{spec.name}'"
        if spec.semantic_type in {"numeric", "monetary"} and spec.use_as_feature:
            values = pd.to_numeric(df[spec.name], errors="coerce")
            customers[slug] = values.fillna(values.median())
            feature_cols.append(slug)
            descriptions[slug] = description
            if spec.semantic_type == "monetary" and (monetary_col is None or spec.name == schema.amount):
                monetary_col = slug
        elif spec.semantic_type == "categorical":
            values = df[spec.name].astype(str).where(df[spec.name].notna(), "desconocido")
            customers[slug] = values
            attribute_cols.append(slug)
            descriptions[slug] = description
            if spec.use_as_feature:
                top = values.value_counts().index[:MAX_ONE_HOT]
                for value in top:
                    col = f"{slug}={value}"
                    customers[col] = (values == value).astype(float)
                    feature_cols.append(col)
                    descriptions[col] = f"1 si {slug} es '{value}'"

    if not feature_cols:
        raise ValueError("No hay columnas marcadas como feature para segmentar")
    return FeatureSet(
        customers=customers,
        feature_cols=feature_cols,
        attribute_cols=attribute_cols,
        descriptions=descriptions,
        monetary_col=monetary_col,
    )


def transform(customers: pd.DataFrame, feature_cols: list[str]) -> Transformed:
    T = pd.DataFrame(index=customers.index)
    binary = []
    for col in feature_cols:
        x = customers[col].astype(float)
        if x.isin([0.0, 1.0]).all():
            T[col] = x
            binary.append(col)
            continue
        if x.min() >= 0 and (col in LOG_FEATURES or x.skew() > 1):
            x = np.log1p(x)
        lo, hi = x.quantile([0.01, 0.99])
        T[col] = x.clip(lo, hi)

    X = T.copy()
    continuous = [c for c in feature_cols if c not in binary]
    if continuous:
        X[continuous] = StandardScaler().fit_transform(T[continuous])
    return Transformed(T=T, X=X.to_numpy(dtype=float))
