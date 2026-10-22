import numpy as np
import pandas as pd
import pytest

from app.core.features import build_features, transform
from app.core.ingest import profile_columns
from app.core.schema import heuristic_schema
from app.models import SchemaMapping


def tx_schema(**overrides) -> SchemaMapping:
    base = dict(data_shape="transactional", customer_id="cliente_id", date="fecha", amount="monto",
                invoice_id="factura", category="categoria")
    return SchemaMapping(**(base | overrides))


def padded(df: pd.DataFrame) -> pd.DataFrame:
    """Agrega clientes de relleno para pasar el mínimo de 10 clientes."""
    filler = pd.DataFrame({
        "factura": [f"X{i}" for i in range(10)], "cliente_id": [f"Z{i}" for i in range(10)],
        "fecha": pd.Timestamp("2025-01-01"), "monto": 1.0, "categoria": "Bebidas",
    })
    return pd.concat([df, filler], ignore_index=True)


def test_rfm_matches_hand_computation(small_tx):
    fs = build_features(padded(small_tx), tx_schema())
    a, b = fs.customers.loc["A"], fs.customers.loc["B"]
    # Fecha de referencia = última compra (2025-01-10) + 1 día.
    assert a["recency_days"] == 1 and a["tenure_days"] == 10
    assert a["frequency"] == 2 and a["monetary"] == 350 and a["avg_ticket"] == 175
    assert a["n_categories"] == 2 and a["top_category_share"] == pytest.approx(300 / 350)
    assert a["top_category"] == "Bebidas"
    # La devolución de B (monto negativo) se excluye.
    assert b["frequency"] == 1 and b["monetary"] == 30 and b["recency_days"] == 6


def test_quantity_times_price_when_no_amount():
    df = pd.DataFrame({
        "cliente_id": [f"C{i}" for i in range(12)], "fecha": pd.Timestamp("2025-03-01"),
        "qty": 2, "price": 5.0,
    })
    fs = build_features(df, tx_schema(amount=None, quantity="qty", unit_price="price", invoice_id=None, category=None))
    assert (fs.customers["monetary"] == 10).all()
    assert "n_categories" not in fs.feature_cols


def test_customer_level_one_hot_and_attributes():
    df = pd.DataFrame({"CustomerID": range(40), "Age": np.arange(40) + 18, "Gender": ["F", "M"] * 20})
    schema = heuristic_schema(profile_columns(df), len(df))
    fs = build_features(df, schema)
    assert set(fs.feature_cols) == {"age", "gender=F", "gender=M"}
    assert fs.attribute_cols == ["gender"]


def test_pii_kept_apart_from_features(synthetic_df, synthetic_schema):
    fs = build_features(synthetic_df, synthetic_schema)
    assert set(fs.pii.columns) == {"nombre_cliente", "email"}
    assert not set(fs.pii.columns) & set(fs.customers.columns)
    assert "comuna" in fs.attribute_cols


def test_transform_standardizes_continuous_and_keeps_binary():
    customers = pd.DataFrame({"monetary": np.exp(np.linspace(0, 10, 100)), "flag": [0.0, 1.0] * 50})
    t = transform(customers, ["monetary", "flag"])
    assert t.X[:, 0].mean() == pytest.approx(0, abs=1e-9)
    assert t.X[:, 0].std() == pytest.approx(1, abs=1e-6)
    assert set(t.X[:, 1]) == {0.0, 1.0}


def test_too_few_customers_raises(small_tx):
    with pytest.raises(ValueError, match="al menos 10"):
        build_features(small_tx, tx_schema())
