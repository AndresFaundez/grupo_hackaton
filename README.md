# grupo_hackaton — ClusterChat

Sube tu base de clientes, segméntala con clustering y **pregúntale directamente a los clusters**.

1. **Subes** un CSV o Excel: transaccional (una fila por compra) o tabla de clientes (una fila por cliente).
2. **La IA entiende el archivo**: detecta el ID de cliente, fechas, montos y datos personales (PII).
3. **Se segmenta**: features RFM por cliente, KMeans con k elegido automáticamente.
4. **Cada cluster queda delimitado**: perfil estadístico, reglas legibles (`monetary > 938 Y recency_days ≤ 91`) y un nombre/persona generado por IA.
5. **Chat con los clusters**:
   - *Modo analista*: el agente responde con datos reales usando herramientas (SQL sobre DuckDB, comparación de clusters, explicación de clientes, listas exportables).
   - *Modo persona*: entrevistas a un cliente simulado del segmento.
   - Las campañas de marketing son una pregunta más del chat ("arma una campaña para este cluster").

**Privacidad por diseño:** el LLM nunca ve filas completas ni columnas PII. Solo recibe metadatos, agregados y las features de un cliente puntual cuando se pide explicarlo. Las listas de clientes con datos de contacto van directo a la UI.

## Equipo

- _Por completar_

## Cómo empezar

```bash
git clone https://github.com/AndresFaundez/grupo_hackaton.git
cd grupo_hackaton
python3 -m venv .venv && .venv/bin/pip install -e '.[dev]'   # o: uv sync --extra dev
cp .env.example .env    # completar GOOGLE_CLOUD_PROJECT y GEMINI_MODEL
gcloud auth application-default login
```

Sin LLM configurado todo funciona igual con fallbacks heurísticos (schema y nombres "Cluster N"), excepto el chat, que responde 503.

### Datos de ejemplo

```bash
.venv/bin/python scripts/make_synthetic.py    # data/samples/synthetic_tx.csv: 2.000 clientes, 4 segmentos plantados
.venv/bin/python scripts/fetch_samples.py     # data/samples/online_retail.csv: Online Retail II (UCI), datos reales
```

### Demo en terminal

```bash
.venv/bin/python scripts/demo.py data/samples/synthetic_tx.csv
```

Muestra el schema detectado y los clusters, y abre un chat (`/persona <id>`, `/analista`, `/clusters`, `/salir`).

### API

```bash
.venv/bin/uvicorn app.main:app --reload     # docs interactivas en http://localhost:8000/docs
```

| Método | Ruta | Qué hace |
|---|---|---|
| GET | `/health` | Estado y si el LLM está configurado |
| POST | `/datasets` | Sube un archivo (multipart `file`) → perfil de columnas + schema propuesto |
| GET | `/datasets/{id}` | Info del dataset |
| PUT | `/datasets/{id}/schema` | Confirma o corrige el schema |
| POST | `/datasets/{id}/clusterings` | `{k?, features?}` → clusters con perfiles, reglas, nombres y coordenadas 2D |
| GET | `/clusterings/{id}` | Resultado del clustering |
| GET | `/clusterings/{id}/clusters/{cid}` | Un cluster |
| POST | `/clusterings/{id}/chat` | `{message, session_id?, cluster_ids?, mode: analyst\|persona, persona_cluster_id?}` |
| GET | `/results/{handle}?format=json\|csv` | Lista de clientes generada desde el chat |

Ejemplo:

```bash
curl -F file=@data/samples/synthetic_tx.csv localhost:8000/datasets
curl -X POST localhost:8000/datasets/<dataset_id>/clusterings -H 'content-type: application/json' -d '{}'
curl -X POST localhost:8000/clusterings/<clustering_id>/chat -H 'content-type: application/json' \
  -d '{"message": "¿Qué clientes valiosos están dejando de comprar?", "cluster_ids": [2]}'
```

La respuesta del chat trae `answer`, `tool_calls` (cada herramienta con sus argumentos y un preview, para el botón "ver consulta") y `attachments` (tablas y listas de clientes).

### Tests

```bash
.venv/bin/python -m pytest          # sin credenciales, con FakeLLM
.venv/bin/python -m pytest -m live  # smoke test contra Gemini real (requiere .env)
```

## Arquitectura

```
app/
  models.py          contratos pydantic compartidos (API y salida estructurada del LLM)
  config.py          settings desde .env
  store.py           estado en memoria + copia en workspace/
  main.py            FastAPI
  api/               routers: datasets, clusterings, chat
  core/
    ingest.py        lectura CSV/Excel, tipos, detección de PII
    schema.py        mapeo semántico con LLM + fallback heurístico
    features.py      RFM por cliente / one-hot, transformación
    clustering.py    KMeans, k por silhouette (3..8)
    profiling.py     estadísticas y z-scores por cluster
    rules.py         árbol de decisión → reglas legibles + explicación por cliente
    embedding.py     PCA 2D para el scatter
    naming.py        nombres, personas y preguntas sugeridas con LLM
    pipeline.py      orquestación
  agent/
    llm.py           wrapper de google-genai (Gemini / Vertex AI) + FakeLLM
    sandbox.py       DuckDB sin PII + guard de SQL (solo SELECT, tablas permitidas, LIMIT)
    tools.py         herramientas del agente
    prompts.py       prompts de los modos analista y persona
    chat.py          loop de tool calling, sesiones, trazas
scripts/             make_synthetic, fetch_samples, demo
```

### Modelo Gemini

El modelo se define con `GEMINI_MODEL` en `.env`. Hay que elegir el Flash vigente en la [lista de versiones de Vertex AI](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/learn/model-versions) y validarlo con `pytest -m live`.
