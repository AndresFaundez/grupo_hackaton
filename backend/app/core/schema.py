"""Detección semántica del schema: LLM con fallback heurístico.

El LLM solo recibe perfiles de columnas (nombre, tipo, estadísticas y ejemplos
enmascarados), nunca filas completas.
"""

from __future__ import annotations

import json
import logging

from app.agent.llm import LLM, LLMError
from app.core.ingest import tokens
from app.models import ColumnProfile, ColumnSpec, SchemaMapping, SchemaMappingLLM

log = logging.getLogger(__name__)

CUSTOMER_TOKENS = {"customer", "cliente", "client", "socio", "member"}
ID_TOKENS = {"id", "code", "codigo", "cod", "rut", "no", "nro", "num", "number", "key"}
AMOUNT_TOKENS = {"amount", "monto", "total", "revenue", "venta", "ventas", "importe", "spend", "gasto", "sales", "valor"}
QUANTITY_TOKENS = {"quantity", "qty", "cantidad", "unidades", "units"}
PRICE_TOKENS = {"price", "precio", "unitprice"}
INVOICE_TOKENS = {"invoice", "factura", "order", "orden", "pedido", "boleta", "transaction", "transaccion", "ticket", "receipt"}
CATEGORY_TOKENS = {"category", "categoria", "family", "familia", "department", "departamento", "rubro", "linea"}

SYSTEM_PROMPT = """Eres un experto en datos de clientes. Recibes el perfil de las columnas de una tabla \
subida por una empresa y debes mapear su significado para segmentar clientes.

Reglas:
- data_shape = "transactional" si cada fila es una compra/línea de compra y el cliente se repite \
(n_unique del ID de cliente bastante menor que n_rows). "customer" si hay una fila por cliente.
- En transaccional: indica date y amount; si no hay monto total pero hay cantidad y precio unitario, \
indica quantity y unit_price.
- pii_columns: nombres, emails, teléfonos, RUT/DNI, direcciones. Si la columna aparece con pii_suspect=true, inclúyela.
- columns: una entrada por cada columna. use_as_feature=true solo para columnas numéricas o categóricas \
(pocas categorías) que describan el comportamiento o perfil del cliente, y solo cuando data_shape="customer". \
Nunca para IDs, PII, fechas ni texto libre.
- description: explica en español, en pocas palabras, qué contiene la columna.
- Usa exactamente los nombres de columna recibidos."""


def heuristic_schema(profiles: list[ColumnProfile], n_rows: int) -> SchemaMapping:
    by_name = {p.name: p for p in profiles}
    toks = {p.name: set(tokens(p.name)) for p in profiles}
    numeric = [p.name for p in profiles if p.stats and "mean" in p.stats]
    datetimes = [p.name for p in profiles if p.dtype.startswith("datetime")]

    def first(candidates: list[str], wanted: set[str]) -> str | None:
        return next((c for c in candidates if toks[c] & wanted), None)

    names = [p.name for p in profiles]
    customer_id = (
        next((c for c in names if toks[c] & CUSTOMER_TOKENS and toks[c] & ID_TOKENS), None)
        or next((c for c in names if toks[c] & CUSTOMER_TOKENS and not by_name[c].stats), None)
        or next((c for c in names if "id" in toks[c]), None)
        or names[0]
    )
    date = datetimes[0] if datetimes else None
    amount = first(numeric, AMOUNT_TOKENS)
    quantity = first(numeric, QUANTITY_TOKENS)
    unit_price = first(numeric, PRICE_TOKENS)
    invoice_id = first([n for n in names if n != customer_id], INVOICE_TOKENS)
    category = first([n for n in names if not by_name[n].stats], CATEGORY_TOKENS)

    repeats = by_name[customer_id].n_unique < 0.9 * n_rows
    data_shape = "transactional" if repeats and date else "customer"

    reserved = {c for c in (customer_id, invoice_id) if c}
    columns = []
    for p in profiles:
        if p.pii_suspect:
            semantic = "pii"
        elif p.name in reserved:
            semantic = "id"
        elif p.name in datetimes:
            semantic = "datetime"
        elif p.name in numeric:
            semantic = "monetary" if p.name in {amount, unit_price} else "numeric"
        elif p.n_unique <= 50:
            semantic = "categorical"
        else:
            semantic = "text"
        use = data_shape == "customer" and semantic in {"numeric", "monetary", "categorical"}
        columns.append(ColumnSpec(name=p.name, semantic_type=semantic, use_as_feature=use))

    return SchemaMapping(
        data_shape=data_shape,
        customer_id=customer_id,
        date=date,
        amount=amount,
        quantity=quantity,
        unit_price=unit_price,
        invoice_id=invoice_id,
        category=category,
        pii_columns=[p.name for p in profiles if p.pii_suspect],
        columns=columns,
        source="heuristic",
    )


def validate_schema(schema: SchemaMappingLLM, column_names: list[str]) -> list[str]:
    """Lista de problemas; vacía si el schema es utilizable."""
    names = set(column_names)
    problems = []
    for field in ("customer_id", "date", "amount", "quantity", "unit_price", "invoice_id", "category"):
        value = getattr(schema, field)
        if value is not None and value not in names:
            problems.append(f"{field}: la columna '{value}' no existe")
    problems += [f"pii_columns: '{c}' no existe" for c in schema.pii_columns if c not in names]
    if schema.data_shape == "transactional":
        if not schema.date:
            problems.append("transaccional requiere una columna de fecha")
        if not schema.amount and not (schema.quantity and schema.unit_price):
            problems.append("transaccional requiere monto, o cantidad y precio unitario")
    if schema.data_shape == "customer" and not any(c.use_as_feature for c in schema.columns):
        problems.append("tabla de clientes sin columnas marcadas como feature")
    return problems


def detect_schema(profiles: list[ColumnProfile], n_rows: int, llm: LLM | None) -> SchemaMapping:
    fallback = heuristic_schema(profiles, n_rows)
    if llm is None:
        return fallback

    payload = {
        "n_rows": n_rows,
        "columns": [p.model_dump(exclude_none=True) for p in profiles],
    }
    prompt = f"Perfil de la tabla:\n```json\n{json.dumps(payload, ensure_ascii=False, default=str)}\n```"
    try:
        proposal = llm.generate_json(prompt, SchemaMappingLLM, system=SYSTEM_PROMPT)
    except LLMError:
        log.warning("Detección de schema con LLM falló; uso heurística", exc_info=True)
        return fallback

    problems = validate_schema(proposal, [p.name for p in profiles])
    if problems:
        log.warning("Schema del LLM inválido (%s); uso heurística", "; ".join(problems))
        return fallback

    schema = SchemaMapping(**proposal.model_dump(), source="llm")
    # Por seguridad, la PII detectada por heurística siempre se mantiene.
    schema.pii_columns = sorted(set(schema.pii_columns) | set(fallback.pii_columns))
    known = {c.name for c in schema.columns}
    schema.columns += [c for c in fallback.columns if c.name not in known]
    for spec in schema.columns:
        if spec.name in schema.pii_columns:
            spec.semantic_type = "pii"
            spec.use_as_feature = False
    return schema
