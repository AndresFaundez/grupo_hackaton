import pandas as pd

from app.agent.llm import FakeLLM
from app.core.ingest import detect_pii, profile_columns, read_table, tokens
from app.core.schema import detect_schema, heuristic_schema
from app.models import ColumnSpec, SchemaMappingLLM


def test_tokens_split_camel_snake_and_accents():
    assert tokens("NombreCliente") == ["nombre", "cliente"]
    assert tokens("teléfono_móvil") == ["telefono", "movil"]


def test_read_table_sniffs_separator_and_types(small_tx):
    assert list(small_tx.columns) == ["factura", "cliente_id", "fecha", "monto", "categoria"]
    assert pd.api.types.is_datetime64_any_dtype(small_tx["fecha"])
    assert pd.api.types.is_numeric_dtype(small_tx["monto"])


def test_read_table_latin1():
    content = "cliente;comuna;gasto\n1;Ñuñoa;10\n2;Maipú;20\n".encode("latin-1")
    df = read_table(content, "x.csv")
    assert df["comuna"].tolist() == ["Ñuñoa", "Maipú"]


def test_detect_pii_by_name_and_values():
    assert detect_pii("email", pd.Series(["x"])) == "email"
    assert detect_pii("nombre_cliente", pd.Series(["Ana"])) == "nombre"
    assert detect_pii("product_name", pd.Series(["Leche"])) is None
    assert detect_pii("contacto", pd.Series(["a@b.cl", "c@d.com"])) == "email"
    assert detect_pii("doc", pd.Series(["12.345.678-5", "9.876.543-K"])) == "rut"
    assert detect_pii("monto", pd.Series([1, 2])) is None


def test_profile_masks_pii_examples(synthetic_df):
    profiles = {p.name: p for p in profile_columns(synthetic_df)}
    assert profiles["email"].pii_suspect
    assert all("oculto" in e for e in profiles["email"].examples)
    assert not profiles["comuna"].pii_suspect


def test_heuristic_schema_on_synthetic(synthetic_schema):
    s = synthetic_schema
    assert s.data_shape == "transactional"
    assert (s.customer_id, s.date, s.amount, s.invoice_id, s.category) == ("rut_cliente", "fecha", "monto", "boleta", "categoria")
    assert {"rut_cliente", "nombre_cliente", "email"} <= set(s.pii_columns)


def test_heuristic_schema_customer_level():
    df = pd.DataFrame({"CustomerID": range(50), "Age": range(20, 70), "Gender": ["F", "M"] * 25, "Spending Score": range(50)})
    s = heuristic_schema(profile_columns(df), len(df))
    assert s.data_shape == "customer"
    assert s.customer_id == "CustomerID"
    assert {c.name for c in s.columns if c.use_as_feature} == {"Age", "Gender", "Spending Score"}


def test_detect_schema_uses_llm_and_keeps_heuristic_pii(synthetic_df):
    profiles = profile_columns(synthetic_df)
    proposal = SchemaMappingLLM(
        data_shape="transactional", customer_id="rut_cliente", date="fecha", amount="monto",
        invoice_id="boleta", category="categoria", pii_columns=["email"],
        columns=[ColumnSpec(name="comuna", semantic_type="categorical", description="Comuna del cliente")],
    )
    s = detect_schema(profiles, len(synthetic_df), FakeLLM({SchemaMappingLLM: proposal}))
    assert s.source == "llm"
    assert {"rut_cliente", "nombre_cliente", "email"} <= set(s.pii_columns)
    assert {c.name for c in s.columns} == set(synthetic_df.columns)


def test_detect_schema_falls_back_on_invalid_llm_output(synthetic_df):
    profiles = profile_columns(synthetic_df)
    bad = SchemaMappingLLM(data_shape="transactional", customer_id="no_existe")
    s = detect_schema(profiles, len(synthetic_df), FakeLLM({SchemaMappingLLM: bad}))
    assert s.source == "heuristic"
    assert s.customer_id == "rut_cliente"


def test_detect_schema_falls_back_when_llm_errors(synthetic_df):
    s = detect_schema(profile_columns(synthetic_df), len(synthetic_df), FakeLLM())
    assert s.source == "heuristic"
