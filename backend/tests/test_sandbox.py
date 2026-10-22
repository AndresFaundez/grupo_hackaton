import pandas as pd
import pytest

from app.agent.sandbox import Sandbox, SqlRejected, validate_sql


@pytest.fixture(scope="module")
def sandbox():
    customers = pd.DataFrame({"customer_ref": range(120), "cluster_id": [i % 3 for i in range(120)], "monetary": [float(i) for i in range(120)]})
    clusters = pd.DataFrame({"cluster_id": [0, 1, 2], "name": ["A", "B", "C"]})
    return Sandbox(customers, clusters, max_rows=50)


@pytest.mark.parametrize(
    "sql",
    [
        "DROP TABLE customers",
        "INSERT INTO customers VALUES (1, 1, 1)",
        "UPDATE customers SET monetary = 0",
        "SELECT 1; SELECT 2",
        "SELECT * FROM read_csv('/etc/passwd')",
        "SELECT * FROM '/etc/passwd'",
        "SELECT * FROM glob('*')",
        "SELECT getenv('HOME')",
        "COPY customers TO 'out.csv'",
        "ATTACH 'x.db'",
        "SET threads = 1",
        "PRAGMA version",
        "SELECT * FROM information_schema.tables",
        "SELECT * FROM duckdb_settings()",
        "SELECT * FROM main.customers",
        "SELECT * FROM pii",
        "SELEC nada",
    ],
)
def test_rejects_unsafe_sql(sql):
    with pytest.raises(SqlRejected):
        validate_sql(sql, 50)


def test_injects_limit_and_keeps_existing():
    assert validate_sql("SELECT * FROM customers", 50).endswith("LIMIT 50")
    assert validate_sql("SELECT * FROM customers LIMIT 5", 50).endswith("LIMIT 5")
    assert "LIMIT" not in validate_sql("SELECT * FROM customers", None)


def test_allows_ctes_and_joins(sandbox):
    result = sandbox.query(
        "WITH big AS (SELECT * FROM customers WHERE monetary > 100) "
        "SELECT name, COUNT(*) AS n FROM big JOIN clusters USING (cluster_id) GROUP BY name ORDER BY name"
    )
    assert result.columns == ["name", "n"]
    assert sum(row[1] for row in result.rows) == 19


def test_truncates_to_max_rows(sandbox):
    result = sandbox.query("SELECT * FROM customers LIMIT 100")
    assert len(result.rows) == 50 and result.truncated


def test_unlimited_query_for_internal_lists(sandbox):
    result = sandbox.query("SELECT customer_ref FROM customers WHERE cluster_id = 0", limit=False)
    assert len(result.rows) == 40 and not result.truncated


def test_duckdb_external_access_disabled(sandbox):
    with pytest.raises(Exception):
        sandbox._conn.execute("SELECT * FROM read_csv('/etc/hosts')").fetchall()
