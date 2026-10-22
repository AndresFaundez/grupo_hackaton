"""Demo en terminal: subir -> schema -> clusterizar -> chatear con los clusters.

Uso: python scripts/demo.py data/samples/synthetic_tx.csv [--k 5]

Comandos en el chat:
  /persona <id>   entrevistar a un cliente simulado del cluster <id>
  /analista       volver al modo analista
  /clusters       volver a mostrar los clusters
  /salir
"""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.agent.chat import ChatService  # noqa: E402
from app.agent.llm import LLMError, build_llm  # noqa: E402
from app.config import get_settings  # noqa: E402
from app.core.pipeline import ingest_dataset, run_clustering  # noqa: E402
from app.models import ChatRequest, ClusteringRequest, ClusteringResult  # noqa: E402
from app.store import Store  # noqa: E402


def print_clusters(result: ClusteringResult) -> None:
    print(f"\n== {result.k} clusters | silhouette {result.silhouette:.2f} | fidelidad de reglas {result.rules_fidelity:.0%} "
          f"| nombres: {result.labels_source} ==")
    for c in result.clusters:
        p, label = c.profile, c.label
        revenue = f" | {p.revenue_share:.0%} ingresos" if p.revenue_share is not None else ""
        print(f"\n[{p.cluster_id}] {label.name} — {p.size} clientes ({p.share:.0%}){revenue} | valor {label.value_level}")
        print(f"    {label.description}")
        for trait in p.top_traits[:3]:
            print(f"    · {trait}")
        for rule in c.rules[:2]:
            print(f"    regla: {rule.text}  (precisión {rule.precision:.0%}, cobertura {rule.coverage:.0%})")
        if label.suggested_questions:
            print(f"    pregunta sugerida: {label.suggested_questions[0]}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=Path)
    parser.add_argument("--k", type=int, default=None)
    args = parser.parse_args()

    settings = get_settings()
    store = Store(settings.workspace_dir)
    llm = build_llm(settings)

    print(f"Leyendo {args.path} ...")
    dataset = ingest_dataset(args.path.read_bytes(), args.path.name, llm, store)
    s = dataset.info.proposed_schema
    print(f"{dataset.info.n_rows:,} filas | schema ({s.source}): {s.data_shape}, cliente={s.customer_id}, fecha={s.date}, "
          f"monto={s.amount or f'{s.quantity}×{s.unit_price}'}, compra={s.invoice_id}, categoría={s.category}")
    print(f"PII detectada (no se envía al LLM): {', '.join(s.pii_columns) or 'ninguna'}")

    print("Clusterizando ...")
    record = run_clustering(dataset, ClusteringRequest(k=args.k), llm, settings, store)
    print_clusters(record.result)

    if llm is None:
        print("\nLLM no configurado: copia .env.example a .env y define GOOGLE_CLOUD_PROJECT para chatear.")
        return

    chat = ChatService(llm, store, settings)
    session_id, mode, persona = None, "analyst", None
    print("\nPregúntale a los clusters (/persona <id>, /analista, /clusters, /salir)")
    while True:
        try:
            message = input(f"\n{'🎭 ' if persona is not None else ''}> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not message:
            continue
        if message == "/salir":
            break
        if message == "/clusters":
            print_clusters(record.result)
            continue
        if message == "/analista":
            mode, persona, session_id = "analyst", None, None
            continue
        if message.startswith("/persona"):
            parts = message.split()
            if len(parts) == 2 and parts[1].isdigit() and record.result.cluster(int(parts[1])):
                mode, persona, session_id = "persona", int(parts[1]), None
                print(f"Hablando con un cliente simulado de «{record.result.cluster(persona).label.name}»")
            else:
                print("Uso: /persona <id de cluster>")
            continue

        try:
            resp = chat.chat(record, ChatRequest(message=message, session_id=session_id, mode=mode, persona_cluster_id=persona))
        except LLMError as e:
            print(f"Error del LLM: {e}")
            continue
        session_id = resp.session_id
        for call in resp.tool_calls:
            status = f" ERROR: {call.error}" if call.error else ""
            print(f"  ↳ {call.name}({call.args}){status}")
        print(f"\n{resp.answer}")
        for att in resp.attachments:
            if att.type == "customer_list":
                print(f"  📋 {att.title}: {att.count} clientes → GET /results/{att.handle}")
        if resp.simulated:
            print("  (respuesta simulada)")


if __name__ == "__main__":
    main()
