import pytest
from fastapi.testclient import TestClient

from app.agent.llm import FakeLLM, LLMTurn, ToolCall
from app.config import Settings
from app.main import create_app


@pytest.fixture
def llm():
    return FakeLLM()


@pytest.fixture
def client(tmp_path, llm):
    return TestClient(create_app(Settings(workspace_dir=tmp_path), llm=llm))


def upload(client, csv: bytes):
    r = client.post("/datasets", files={"file": ("synthetic_tx.csv", csv, "text/csv")})
    assert r.status_code == 200, r.text
    return r.json()


def test_health(client):
    assert client.get("/health").json()["status"] == "ok"


def test_full_flow(client, llm, synthetic_csv, tmp_path):
    info = upload(client, synthetic_csv)
    assert info["proposed_schema"]["data_shape"] == "transactional"
    assert info["proposed_schema"]["source"] == "heuristic"  # FakeLLM sin respuesta -> fallback
    assert len(info["preview"]) == 10
    assert (tmp_path / info["dataset_id"] / "raw.parquet").exists()

    schema = info["proposed_schema"] | {"category": None}
    r = client.put(f"/datasets/{info['dataset_id']}/schema", json=schema)
    assert r.status_code == 200 and r.json()["confirmed_schema"]["source"] == "user"

    r = client.post(f"/datasets/{info['dataset_id']}/clusterings", json={"k": 4})
    assert r.status_code == 200, r.text
    result = r.json()
    assert result["k"] == 4 and len(result["clusters"]) == 4
    assert "n_categories" not in result["features"]  # se quitó la categoría en el schema confirmado
    assert result["scatter"]["points"] and result["rules_fidelity"] > 0.5
    assert result["filename"] == "synthetic_tx.csv" and result["total_revenue"] > 0
    first = result["clusters"][0]
    assert first["profile"]["metrics"]["avg_spend"] > 0 and first["label"]["strategies"]
    assert first["representative"]["name"]  # nombre_cliente detectado como columna de nombre

    cid = result["clustering_id"]
    assert client.get(f"/clusterings/{cid}").json()["clustering_id"] == cid
    assert client.get(f"/clusterings/{cid}/clusters/0").json()["profile"]["cluster_id"] == 0
    assert client.get(f"/clusterings/{cid}/clusters/42").status_code == 404

    llm.chat_script = [
        LLMTurn(text=None, tool_calls=[ToolCall("list_customers", {"cluster_id": 1, "limit": 5})]),
        LLMTurn(text="Listo, te dejé 5 clientes.", tool_calls=[]),
    ]
    r = client.post(f"/clusterings/{cid}/chat", json={"message": "Dame 5 clientes del cluster 1"})
    assert r.status_code == 200, r.text
    chat = r.json()
    handle = chat["attachments"][0]["handle"]

    rows = client.get(f"/results/{handle}").json()
    assert rows["count"] == 5 and "email" in rows["columns"]
    csv = client.get(f"/results/{handle}?format=csv")
    assert csv.headers["content-type"].startswith("text/csv") and csv.text.count("\n") == 6


def test_errors(client, synthetic_csv):
    assert client.get("/datasets/nope").status_code == 404
    assert client.post("/datasets", files={"file": ("x.csv", b"", "text/csv")}).status_code == 400
    assert client.post("/datasets", files={"file": ("x.csv", b"solo_una_columna\n1\n2\n", "text/csv")}).status_code == 422

    info = upload(client, synthetic_csv)
    bad = info["proposed_schema"] | {"customer_id": "no_existe"}
    r = client.put(f"/datasets/{info['dataset_id']}/schema", json=bad)
    assert r.status_code == 422 and "no existe" in str(r.json())

    r = client.post(f"/datasets/{info['dataset_id']}/clusterings", json={"features": ["inventada"]})
    assert r.status_code == 422


def test_chat_returns_503_without_llm(tmp_path, synthetic_csv):
    client = TestClient(create_app(Settings(workspace_dir=tmp_path), llm=None))
    info = upload(client, synthetic_csv)
    result = client.post(f"/datasets/{info['dataset_id']}/clusterings").json()
    assert result["labels_source"] == "fallback"
    r = client.post(f"/clusterings/{result['clustering_id']}/chat", json={"message": "hola"})
    assert r.status_code == 503


def test_sample_rename_audience_and_campaign(client, llm):
    from app.models import CampaignDraftLLM

    info = client.post("/datasets/sample").json()
    assert info["filename"] == "ejemplo_tienda_2025.csv" and info["proposed_schema"]["data_shape"] == "transactional"
    result = client.post(f"/datasets/{info['dataset_id']}/clusterings", json={}).json()
    cid = result["clustering_id"]

    r = client.patch(f"/clusterings/{cid}/clusters/0", json={"name": "  Mis favoritos "})
    assert r.status_code == 200 and r.json()["label"]["name"] == "Mis favoritos"
    assert client.get(f"/clusterings/{cid}").json()["clusters"][0]["label"]["name"] == "Mis favoritos"
    record = client.app.state.services.store.get_clustering(cid)
    assert record.sandbox.query("SELECT DISTINCT cluster_name FROM customers WHERE cluster_id = 0").rows == [["Mis favoritos"]]
    assert client.patch(f"/clusterings/{cid}/clusters/0", json={"name": ""}).status_code == 422

    audience = client.get(f"/clusterings/{cid}/clusters/0/customers").json()
    assert audience["count"] == result["clusters"][0]["profile"]["size"] and "email" in audience["columns"]
    csv = client.get(f"/clusterings/{cid}/clusters/0/customers?format=csv")
    assert csv.text.count("\n") == audience["count"] + 1

    prompts = []

    def fake(prompt):
        prompts.append(prompt)
        return CampaignDraftLLM(subject="Hola", message="Vuelve, [Nombre]", rationale="Porque sí")

    llm.json_responses[CampaignDraftLLM] = fake
    body = {"objective": "reactivar", "channel": "sms", "instructions": "tono formal", "previous_message": "v1"}
    draft = client.post(f"/clusterings/{cid}/clusters/0/campaign-draft", json=body).json()
    assert draft["message"] == "Vuelve, [Nombre]" and draft["subject"] is None  # SMS no lleva asunto
    assert draft["audience_size"] == result["clusters"][0]["profile"]["size"]
    assert "tono formal" in prompts[0] and "v1" in prompts[0] and "@" not in prompts[0]
    bad = client.post(f"/clusterings/{cid}/clusters/0/campaign-draft", json={"objective": "x", "channel": "sms"})
    assert bad.status_code == 422


def test_cors_allows_vite_dev_server(client):
    r = client.options("/health", headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "GET"})
    assert r.headers["access-control-allow-origin"] == "http://localhost:5173"
