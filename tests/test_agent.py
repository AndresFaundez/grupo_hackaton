import pandas as pd
import pytest

from app.agent.chat import ChatService, ChatUnavailable
from app.agent.llm import FakeLLM, LLMError, LLMTurn, ToolCall
from app.agent.tools import execute_tool
from app.config import Settings
from app.core.pipeline import ingest_dataset, run_clustering
from app.models import ChatRequest, ClusteringRequest
from app.store import Store


@pytest.fixture(scope="module")
def env(synthetic_csv, tmp_path_factory):
    settings = Settings(workspace_dir=tmp_path_factory.mktemp("ws"))
    store = Store(settings.workspace_dir)
    dataset = ingest_dataset(synthetic_csv, "synthetic_tx.csv", None, store)
    record = run_clustering(dataset, ClusteringRequest(), None, settings, store)
    return settings, store, record


def test_sandbox_has_no_pii(env):
    _, _, record = env
    columns = {name for name, _ in record.sandbox.schema["customers"]}
    assert not columns & {"rut_cliente", "customer_id", "nombre_cliente", "email"}
    assert {"customer_ref", "cluster_id", "cluster_name", "monetary", "comuna"} <= columns


def test_describe_and_compare(env):
    _, store, record = env
    out = execute_tool("describe_cluster", {"cluster_id": 0}, record, store)
    assert out.error is None and out.response["size"] == record.result.clusters[0].profile.size
    assert out.response["rules"]

    out = execute_tool("compare_clusters", {"cluster_a": 0, "cluster_b": 1}, record, store)
    diffs = out.response["differences"]
    assert [abs(d["z_diff"]) for d in diffs] == sorted((abs(d["z_diff"]) for d in diffs), reverse=True)

    out = execute_tool("describe_cluster", {"cluster_id": 99}, record, store)
    assert "No existe el cluster" in out.error


def test_query_data_returns_table_attachment(env):
    _, store, record = env
    out = execute_tool("query_data", {"sql": "SELECT cluster_id, COUNT(*) AS n FROM customers GROUP BY 1 ORDER BY 1"}, record, store)
    assert [row[1] for row in out.response["rows"]] == [c.profile.size for c in record.result.clusters]
    assert out.attachment.type == "table"

    out = execute_tool("query_data", {"sql": "DELETE FROM customers"}, record, store)
    assert out.error


def test_explain_customer_accepts_unformatted_rut(env):
    _, store, record = env
    row = record.customers.iloc[0]
    rut = row["customer_id"]
    out = execute_tool("explain_customer", {"customer_id": rut.replace(".", "")}, record, store)
    assert out.error is None
    assert out.response["cluster_id"] == row["cluster_id"]
    assert out.response["decision_path"]


def test_list_customers_hides_pii_from_llm(env):
    _, store, record = env
    out = execute_tool("list_customers", {"cluster_id": 0, "where": "recency_days > 60", "order_by": "monetary DESC"}, record, store)
    members = record.customers[(record.customers["cluster_id"] == 0) & (record.customers["recency_days"] > 60)]
    assert out.response["count"] == len(members)
    assert "@" not in str(out.response)

    listed = store.get_result(out.response["handle"])
    assert {"email", "nombre_cliente", "customer_id"} <= set(listed.columns)
    assert listed["monetary"].is_monotonic_decreasing


def test_chat_loop_with_tools_and_traces(env):
    settings, store, record = env
    llm = FakeLLM(chat_script=[
        LLMTurn(text=None, tool_calls=[ToolCall("query_data", {"sql": "SELECT COUNT(*) AS n FROM customers WHERE cluster_id = 0"})]),
        LLMTurn(text=None, tool_calls=[ToolCall("list_customers", {"cluster_id": 0, "where": "recency_days > 60"})]),
        LLMTurn(text="Hay N clientes en riesgo.", tool_calls=[]),
    ])
    service = ChatService(llm, store, settings)
    resp = service.chat(record, ChatRequest(message="¿Quiénes están en riesgo?", cluster_ids=[0]))

    assert resp.answer == "Hay N clientes en riesgo."
    assert [t.name for t in resp.tool_calls] == ["query_data", "list_customers"]
    assert resp.tool_calls[0].result_preview["rows"] == [[record.result.clusters[0].profile.size]]
    assert [a.type for a in resp.attachments] == ["table", "customer_list"]
    assert not resp.simulated

    # El LLM recibió el contexto de clusters seleccionados y nunca vio datos personales.
    first_call = llm.chat_calls[0]
    assert "[Contexto: el usuario tiene seleccionados los clusters 0" in first_call["messages"][0].text
    seen = first_call["system"] + str(llm.chat_calls[-1]["messages"])
    assert "@example.com" not in seen and "rut_cliente" not in seen

    # La sesión continúa con el historial.
    llm.chat_script = [LLMTurn(text="Sigo aquí.", tool_calls=[])]
    again = service.chat(record, ChatRequest(message="¿Y?", session_id=resp.session_id))
    assert again.session_id == resp.session_id
    assert len(llm.chat_calls[-1]["messages"]) == 7  # user, model, tool, model, tool, model, user


def test_chat_stops_after_max_steps(env):
    settings, store, record = env
    loop = [LLMTurn(text=None, tool_calls=[ToolCall("describe_cluster", {"cluster_id": 0})])] * 10
    service = ChatService(FakeLLM(chat_script=loop), store, settings.model_copy(update={"max_agent_steps": 3}))
    resp = service.chat(record, ChatRequest(message="loop"))
    assert len(resp.tool_calls) == 3 and "No alcancé" in resp.answer


def test_persona_mode_only_allows_describe(env):
    settings, store, record = env
    llm = FakeLLM(chat_script=[
        LLMTurn(text=None, tool_calls=[ToolCall("query_data", {"sql": "SELECT 1"})]),
        LLMTurn(text="Compro casi todas las semanas.", tool_calls=[]),
    ])
    resp = ChatService(llm, store, settings).chat(record, ChatRequest(message="¿Cada cuánto compras?", mode="persona", persona_cluster_id=1))
    assert resp.simulated
    assert llm.chat_calls[0]["tools"] == ["describe_cluster"]
    assert "no disponible" in resp.tool_calls[0].error
    assert record.result.cluster(1).label.name in llm.chat_calls[0]["system"]

    with pytest.raises(ValueError):
        ChatService(llm, store, settings).chat(record, ChatRequest(message="x", mode="persona"))


def test_chat_without_llm_and_llm_errors(env):
    settings, store, record = env
    with pytest.raises(ChatUnavailable):
        ChatService(None, store, settings).chat(record, ChatRequest(message="hola"))

    class Broken(FakeLLM):
        def chat(self, messages, system, tools):
            raise LLMError("caído")

    with pytest.raises(LLMError):
        ChatService(Broken(), store, settings).chat(record, ChatRequest(message="hola"))
    # El turno fallido no queda en el historial de la sesión.
    newest = list(store.sessions.values())[-1]
    assert newest.messages == []


def test_customer_level_pipeline(tmp_path):
    df = pd.DataFrame({
        "CustomerID": range(200),
        "Gender": ["Female", "Male"] * 100,
        "Age": [20 + (i % 50) for i in range(200)],
        "Annual Income (k$)": [15 + (i * 7) % 120 for i in range(200)],
        "Spending Score (1-100)": [(i * 13) % 100 for i in range(200)],
    })
    settings = Settings(workspace_dir=tmp_path)
    store = Store(tmp_path)
    dataset = ingest_dataset(df.to_csv(index=False).encode(), "mall.csv", None, store)
    assert dataset.info.proposed_schema.data_shape == "customer"
    record = run_clustering(dataset, ClusteringRequest(k=4), None, settings, store)
    assert record.result.k == 4
    assert "annual_income_k" in record.result.features
    columns = {name for name, _ in record.sandbox.schema["customers"]}
    assert "gender" in columns and not any("=" in c for c in columns)
