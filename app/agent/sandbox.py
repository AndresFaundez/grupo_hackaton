"""Conexión DuckDB aislada para las consultas del LLM.

Solo contiene tablas sin PII (`customers`, `clusters`). Las consultas pasan por un guard:
una sola sentencia de lectura, solo tablas permitidas, sin funciones de archivo, con LIMIT.
DuckDB además se configura sin acceso externo como segunda barrera.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import Any

import duckdb
import pandas as pd
import sqlglot
from sqlglot import exp

ALLOWED_TABLES = {"customers", "clusters"}
FORBIDDEN_FUNCTION_PREFIXES = ("read_", "parquet_", "csv_", "json_", "glob", "sniff_", "iceberg_", "delta_", "query", "getenv")
FORBIDDEN_NODES = (exp.Insert, exp.Update, exp.Delete, exp.Drop, exp.Create, exp.Alter, exp.Command, exp.Copy, exp.Set, exp.Pragma)
QUERY_TIMEOUT_S = 10.0


class SqlRejected(ValueError):
    pass


@dataclass
class QueryResult:
    sql: str
    columns: list[str]
    rows: list[list[Any]]
    truncated: bool


def validate_sql(sql: str, max_rows: int | None) -> str:
    """Devuelve la consulta normalizada (con LIMIT si corresponde) o lanza SqlRejected."""
    try:
        statements = [s for s in sqlglot.parse(sql, read="duckdb") if s is not None]
    except sqlglot.errors.ParseError as e:
        raise SqlRejected(f"SQL inválido: {e}") from e
    if len(statements) != 1:
        raise SqlRejected("Se permite exactamente una sentencia")
    stmt = statements[0]
    if not isinstance(stmt, exp.Query):
        raise SqlRejected("Solo se permiten consultas SELECT")
    if any(isinstance(node, FORBIDDEN_NODES) for node in stmt.walk()):
        raise SqlRejected("La consulta contiene operaciones no permitidas")

    for func in stmt.find_all(exp.Func):
        name = (func.name if isinstance(func, exp.Anonymous) else func.sql_name()).lower()
        if name.startswith(FORBIDDEN_FUNCTION_PREFIXES):
            raise SqlRejected(f"Función no permitida: {name}")

    ctes = {cte.alias_or_name.lower() for cte in stmt.find_all(exp.CTE)}
    for table in stmt.find_all(exp.Table):
        name = table.name.lower()
        if table.args.get("db") or table.args.get("catalog") or name not in ALLOWED_TABLES | ctes:
            raise SqlRejected(f"Tabla no permitida: {table.sql(dialect='duckdb')}. Usa customers o clusters.")

    if max_rows is not None and stmt.args.get("limit") is None:
        stmt = stmt.limit(max_rows)
    return stmt.sql(dialect="duckdb")


class Sandbox:
    def __init__(self, customers: pd.DataFrame, clusters: pd.DataFrame, max_rows: int = 50):
        self.max_rows = max_rows
        self._conn = duckdb.connect(":memory:")
        for name, df in (("customers", customers), ("clusters", clusters)):
            self._conn.register(f"_{name}_df", df)
            self._conn.execute(f"CREATE TABLE {name} AS SELECT * FROM _{name}_df")
            self._conn.unregister(f"_{name}_df")
        self._conn.execute("SET enable_external_access = false")
        self._conn.execute("SET lock_configuration = true")
        self.schema = {
            name: [(row[0], row[1]) for row in self._conn.execute(f"DESCRIBE {name}").fetchall()]
            for name in ("customers", "clusters")
        }

    def query(self, sql: str, max_rows: int | None = None, limit: bool = True) -> QueryResult:
        max_rows = max_rows or self.max_rows
        safe_sql = validate_sql(sql, max_rows if limit else None)
        cursor = self._conn.cursor()
        timer = threading.Timer(QUERY_TIMEOUT_S, cursor.interrupt)
        timer.start()
        try:
            cursor.execute(safe_sql)
            columns = [d[0] for d in cursor.description]
            fetched = cursor.fetchall() if not limit else cursor.fetchmany(max_rows + 1)
        except duckdb.Error as e:
            raise SqlRejected(f"Error al ejecutar la consulta: {e}") from e
        finally:
            timer.cancel()
            cursor.close()
        truncated = limit and len(fetched) > max_rows
        if limit:
            fetched = fetched[:max_rows]
        rows = [[_plain(v) for v in row] for row in fetched]
        return QueryResult(sql=safe_sql, columns=columns, rows=rows, truncated=truncated)


def _plain(value: Any) -> Any:
    """Valores JSON-serializables y compactos para el LLM."""
    if isinstance(value, float):
        return round(value, 4)
    if hasattr(value, "isoformat"):
        return value.isoformat()
    if isinstance(value, (int, str, bool)) or value is None:
        return value
    return str(value)
