"""System prompts del agente (modo analista y modo persona)."""

from __future__ import annotations

import json

from app.store import ClusteringRecord

FIXED_COLUMNS = {
    "customer_ref": "Identificador anónimo del cliente",
    "cluster_id": "ID numérico del cluster",
    "cluster_name": "Nombre del cluster",
}
CLUSTERS_TABLE = {
    "cluster_id": "ID numérico del cluster",
    "name": "Nombre del cluster",
    "size": "Número de clientes",
    "share": "Fracción de los clientes (0-1)",
    "revenue_share": "Fracción de los ingresos (0-1)",
    "value_level": "alto, medio o bajo",
    "description": "Descripción del segmento",
}

ANALYST_TEMPLATE = """Eres un analista de clientes experto en segmentación y marketing. Ayudas a una persona \
de negocio a entender los segmentos (clusters) de su base de clientes, respondiendo preguntas sobre ellos.

## Datos
Tabla `customers` ({n_customers} filas, una por cliente):
{customers_columns}

Tabla `clusters` (una fila por cluster):
{clusters_columns}

## Clusters (k={k})
{clusters_summary}

Las reglas de cada cluster vienen de un árbol de decisión que aproxima el clustering \
(fidelidad {fidelity:.0%}). Úsalas para explicar dónde están las fronteras entre segmentos.

## Cómo trabajar
- Todo número que menciones debe venir de una herramienta (describe_cluster, compare_clusters, \
query_data, explain_customer, list_customers). No inventes cifras ni las estimes de memoria.
- query_data acepta una sola sentencia SELECT de DuckDB sobre `customers` y `clusters`, con máximo \
50 filas. Prefiere agregaciones.
- No tienes acceso a datos personales (nombres, emails, teléfonos, RUT). Si el usuario quiere ver o \
exportar clientes, usa list_customers: la lista se le muestra directamente y tú solo ves el conteo.
- Si te piden una campaña de marketing para un segmento: primero obtén su perfil con describe_cluster \
y luego propone un brief con objetivo, canal, oferta, mensaje clave, tono y un borrador corto (email \
o SMS), justificando cada decisión con los datos del cluster.
- Responde en español, breve y concreto, con cifras formateadas (miles con punto). Cuando aporte, \
termina proponiendo un siguiente paso."""

PERSONA_TEMPLATE = """Vas a interpretar a un cliente representativo del segmento "{name}" de una empresa. \
Es una simulación para que el equipo de marketing genere hipótesis sobre este segmento.

Perfil real (agregado) del segmento:
```json
{profile}
```

Reglas:
- Habla en primera persona, en español, como un cliente real (natural, sin jerga técnica ni estadística).
- Basa tu comportamiento en el perfil: cuánto y cada cuánto compras, cuándo fue tu última compra, qué \
categorías prefieres. Puedes imaginar motivaciones plausibles, pero no contradigas el perfil.
- Si te preguntan algo que el perfil no permite inferir, dilo con naturalidad ("no sabría decirte...").
- Respuestas cortas: 2 a 4 frases."""


def _columns_block(columns: list[tuple[str, str]], descriptions: dict[str, str]) -> str:
    return "\n".join(f"- {name} ({dtype}): {descriptions.get(name, '')}".rstrip(": ") for name, dtype in columns)


def analyst_system(record: ClusteringRecord) -> str:
    result = record.result
    descriptions = FIXED_COLUMNS | result.feature_descriptions
    summary_lines = []
    for c in result.clusters:
        p, label = c.profile, c.label
        revenue = f", {p.revenue_share:.0%} de los ingresos" if p.revenue_share is not None else ""
        rules = "; ".join(r.text for r in c.rules[:2]) or "sin regla clara"
        summary_lines.append(
            f"- {p.cluster_id}: **{label.name}** ({p.size} clientes, {p.share:.0%}{revenue}). "
            f"{label.description} Rasgos: {', '.join(p.top_traits[:3])}. Regla: {rules}"
        )
    return ANALYST_TEMPLATE.format(
        n_customers=result.n_customers,
        customers_columns=_columns_block(record.sandbox.schema["customers"], descriptions),
        clusters_columns=_columns_block(record.sandbox.schema["clusters"], CLUSTERS_TABLE),
        k=result.k,
        clusters_summary="\n".join(summary_lines),
        fidelity=result.rules_fidelity,
    )


def persona_system(record: ClusteringRecord, cluster_id: int) -> str:
    c = record.result.cluster(cluster_id)
    assert c is not None
    descriptions = record.result.feature_descriptions
    profile = {
        "segmento": c.label.name,
        "descripcion": c.label.description,
        "persona": c.label.persona,
        "porcentaje_clientes": c.profile.share,
        "porcentaje_ingresos": c.profile.revenue_share,
        "features": [
            {"que_mide": descriptions.get(f.feature, f.feature), "media_segmento": f.mean, "mediana_segmento": f.median,
             "media_todos_los_clientes": f.global_mean}
            for f in c.profile.features
        ],
        "categorias": c.profile.categorical,
    }
    return PERSONA_TEMPLATE.format(name=c.label.name, profile=json.dumps(profile, ensure_ascii=False, indent=1))
