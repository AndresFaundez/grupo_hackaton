import io

import pandas as pd
import pytest

from app.core.ingest import profile_columns, read_table
from app.core.schema import heuristic_schema
from app.synthetic import generate


@pytest.fixture(scope="session")
def synthetic():
    """(transacciones, verdad) con 600 clientes: rápido pero con los 4 segmentos."""
    return generate(n_customers=600, seed=3)


@pytest.fixture(scope="session")
def synthetic_csv(synthetic) -> bytes:
    tx, _ = synthetic
    return tx.to_csv(index=False).encode()


@pytest.fixture(scope="session")
def synthetic_df(synthetic_csv) -> pd.DataFrame:
    return read_table(synthetic_csv, "synthetic_tx.csv")


@pytest.fixture(scope="session")
def synthetic_schema(synthetic_df):
    return heuristic_schema(profile_columns(synthetic_df), len(synthetic_df))


@pytest.fixture
def small_tx() -> pd.DataFrame:
    csv = io.StringIO(
        "factura;cliente_id;fecha;monto;categoria\n"
        "F1;A;2025-01-01;100;Bebidas\n"
        "F1;A;2025-01-01;50;Lácteos\n"
        "F2;A;2025-01-10;200;Bebidas\n"
        "F3;B;2025-01-05;30;Lácteos\n"
        "F4;B;2025-01-05;-30;Lácteos\n"
    )
    return read_table(csv.getvalue().encode(), "tx.csv")
