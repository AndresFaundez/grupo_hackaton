"""Smoke tests contra Gemini real. Correr con: pytest -m live"""

import pytest

from app.agent.chat import ChatService
from app.agent.llm import GeminiLLM
from app.config import Settings
from app.core.ingest import profile_columns
from app.core.pipeline import ingest_dataset, run_clustering
from app.core.schema import detect_schema
from app.models import ChatRequest, ClusteringRequest
from app.store import Store

pytestmark = pytest.mark.live


@pytest.fixture(scope="module")
def llm():
    settings = Settings()
    if not settings.llm_configured:
        pytest.skip("Gemini no configurado (.env)")
    return GeminiLLM(settings)


def test_schema_detection(llm, synthetic_df):
    schema = detect_schema(profile_columns(synthetic_df), len(synthetic_df), llm)
    assert schema.source == "llm"
    assert schema.customer_id == "rut_cliente" and schema.data_shape == "transactional"


def test_naming_and_chat(llm, synthetic_csv, tmp_path):
    settings = Settings(workspace_dir=tmp_path)
    store = Store(tmp_path)
    dataset = ingest_dataset(synthetic_csv, "synthetic_tx.csv", llm, store)
    record = run_clustering(dataset, ClusteringRequest(), llm, settings, store)
    assert record.result.labels_source == "llm"

    resp = ChatService(llm, store, settings).chat(
        record, ChatRequest(message="¿Qué cluster aporta más ingresos y cuántos clientes tiene?")
    )
    assert resp.tool_calls and resp.answer
